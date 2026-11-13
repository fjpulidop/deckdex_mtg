#!/usr/bin/env python3
"""Run with python3.11 scripts/verify_backend_docker.py (requires Docker).

Build the production Dockerfile without cache and test its normal entrypoint,
real migrations, HTTP health and card preservation across another boot. All
containers, the network and the image tag belong to this invocation. PostgreSQL
uses tmpfs; no host ports, existing volumes, .env files or host secrets are used.
Stdout contains JSON evidence; build output and failure logs go to stderr.

SQLAlchemy 2.1 changes bare postgresql:// URLs from psycopg2 to psycopg v3:
https://docs.sqlalchemy.org/en/21/changelog/migration_21.html#default-postgresql-driver-changed-to-psycopg-psycopg-3
The retained psycopg2-binary package cannot satisfy that import. A separate
disposable container installs the incompatible series and must reproduce the
exact missing-psycopg exception. That expected diagnostic failure is distinct
from the unchanged image's startup, which must succeed with SQLAlchemy 2.0.
Resolved versions are measured each run; historical patch versions are not
assumed. Any failed build, assertion or deadline returns nonzero, never a skip.
"""

import json
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATABASE_URL = "postgresql://deckdex:deckdex@db:5432/deckdex"
PACKAGE_TIMEOUT = 900
DB_TIMEOUT = 60
STARTUP_TIMEOUT = 120
PROBE_TIMEOUT = 5
SETTLING_SECONDS = 5
MIGRATION_MARKERS = ("Migrations completed.", "Database is ready.")

DEPENDENCY_PROBE = r"""
import importlib.metadata
import importlib.util
import json
import os
import platform
import sys
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

url = os.environ["DATABASE_URL"]
report = {
    "python": platform.python_version(),
    "sqlalchemy": importlib.metadata.version("sqlalchemy"),
    "psycopg2_binary": importlib.metadata.version("psycopg2-binary"),
    "driver": make_url(url).get_dialect().driver,
    "psycopg_available": importlib.util.find_spec("psycopg") is not None,
    "psycopg2_available": importlib.util.find_spec("psycopg2") is not None,
    "psycopg2_import": psycopg2.__name__,
}
engine = None
try:
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    report["dbapi"] = engine.dialect.dbapi.__name__
    if sys.argv[1:] == ["connect"]:
        with engine.connect() as connection:
            report["select_1"] = connection.execute(text("SELECT 1")).scalar_one()
except Exception as error:
    report["exception"] = {
        "type": type(error).__name__, "name": getattr(error, "name", None), "message": str(error)
    }
finally:
    if engine is not None:
        engine.dispose()
print(json.dumps(report))
"""

HEALTH_PROBE = r"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

try:
    with urlopen("http://127.0.0.1:8000/api/health", timeout=3) as response:
        print(json.dumps({"status": response.status, "body": json.load(response)}))
except HTTPError as error:
    print(json.dumps({"status": error.code, "error": str(error)}))
except URLError as error:
    print(json.dumps({"waiting": str(error)}))
"""

SENTINEL_PROBE = r"""
import json
import os
import sys
import psycopg2

with psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=3) as connection:
    with connection.cursor() as cursor:
        if sys.argv[1] == "insert":
            cursor.execute(
                "INSERT INTO cards (name, set_id, quantity, user_id) "
                "SELECT %s, %s, %s, id FROM users WHERE email = %s "
                "RETURNING id, name, set_id, quantity",
                (sys.argv[2], "docker-regression", 3, "admin@deckdex.local"),
            )
        else:
            cursor.execute("SELECT id, name, set_id, quantity FROM cards WHERE id = %s", (int(sys.argv[2]),))
        rows = cursor.fetchall()
        if len(rows) != 1:
            raise RuntimeError("Expected exactly one sentinel card, got %s" % len(rows))
        print(json.dumps(dict(zip(("id", "name", "set", "quantity"), rows[0]))))
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def docker(*args: str, timeout: float = 30) -> subprocess.CompletedProcess[str]:
    # spec: backend-docker-startup/executable-failure-evidence
    try:
        result = subprocess.run(["docker", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"docker {args[0]} exceeded {timeout}s\n{error.stdout!r}\n{error.stderr!r}") from error
    if result.returncode:
        raise RuntimeError(f"docker {args[0]} exited {result.returncode}\n{result.stdout}\n{result.stderr}")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result


def python_probe(container: str, source: str, *args: str) -> dict:
    output = docker("exec", container, "python", "-c", source, *args, timeout=PROBE_TIMEOUT).stdout
    return json.loads(output)


def require_running(container: str) -> None:
    state = json.loads(docker("inspect", "--format", "{{json .State}}", container, timeout=PROBE_TIMEOUT).stdout)
    require(state["Running"], f"Container {container} exited: {state}")


def check_migrations(container: str, boot: int) -> None:
    output = docker("logs", container, timeout=PROBE_TIMEOUT)
    logs = output.stdout + output.stderr
    for marker in MIGRATION_MARKERS:
        require(logs.count(marker) >= boot, f"Boot {boot} lacks migration marker: {marker}")
    require("ModuleNotFoundError" not in logs and "Traceback" not in logs, "Migration traceback in logs")


def wait_for_health(container: str, boot: int) -> dict:
    # spec: backend-docker-startup/executable-failure-evidence
    deadline = time.monotonic() + STARTUP_TIMEOUT
    last_response = {}
    while time.monotonic() < deadline:
        require_running(container)
        last_response = python_probe(container, HEALTH_PROBE)
        if "status" in last_response:
            require(last_response["status"] == 200, f"Unexpected health HTTP status: {last_response}")
            body = last_response.get("body", {})
            require(
                body.get("status") == "healthy" and body.get("database") == "connected",
                f"Unexpected health body: {last_response}",
            )
            check_migrations(container, boot)
            return last_response
        time.sleep(1)
    raise RuntimeError(f"Health readiness exceeded {STARTUP_TIMEOUT}s: {last_response}")


def check_boot(container: str, boot: int) -> dict:
    # spec: backend-docker-startup/compatible-fresh-image-postgresql-startup
    first = wait_for_health(container, boot)
    deadline = time.monotonic() + SETTLING_SECONDS
    while time.monotonic() < deadline:
        require_running(container)
        time.sleep(1)
    settled = python_probe(container, HEALTH_PROBE)
    require(settled == first, f"Health changed after settling: {settled}")
    require_running(container)
    check_migrations(container, boot)
    return {"migrations_completed": True, "running": True, "health": [first, settled]}


def interrupt_run(signum: int, frame: object) -> None:
    raise InterruptedError(f"Interrupted by signal {signum}")


def main() -> int:
    suffix = uuid.uuid4().hex
    image = f"deckdex-startup-check:{suffix}"
    network = f"deckdex-startup-{suffix}"
    containers: list[str] = []
    network_created = False
    stage = "docker"
    result: dict = {"success": False}
    cleanup_errors: list[str] = []
    signal.signal(signal.SIGINT, interrupt_run)
    signal.signal(signal.SIGTERM, interrupt_run)
    try:
        docker("version")
        stage = "build"
        build = docker(
            "build", "--no-cache", "--load", "-f", "backend/Dockerfile", "-t", image, ".", timeout=PACKAGE_TIMEOUT
        )
        print(build.stdout, file=sys.stderr, end="")
        result["image_id"] = docker("image", "inspect", "--format", "{{.Id}}", image).stdout.strip()

        stage = "diagnostic"
        diagnostic = f"deckdex-diagnostic-{suffix}"
        containers.append(diagnostic)
        docker(
            "create",
            "--name",
            diagnostic,
            "-e",
            f"DATABASE_URL={DATABASE_URL}",
            "--entrypoint",
            "python",
            image,
            "-c",
            f"import time; time.sleep({PACKAGE_TIMEOUT + 60})",
        )
        docker("start", diagnostic)
        result["fresh_image_dependencies"] = python_probe(diagnostic, DEPENDENCY_PROBE)
        print(json.dumps({"fresh_image_dependencies": result["fresh_image_dependencies"]}), flush=True)
        install = docker(
            "exec",
            diagnostic,
            "python",
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "sqlalchemy>=2.1,<2.2",
            timeout=PACKAGE_TIMEOUT,
        )
        print(install.stdout, file=sys.stderr, end="")
        diagnostic_report = python_probe(diagnostic, DEPENDENCY_PROBE)
        result["diagnostic"] = diagnostic_report
        print(json.dumps({"diagnostic": diagnostic_report}), flush=True)
        # spec: backend-docker-startup/reproducible-dependency-incompatibility-evidence
        require(diagnostic_report["sqlalchemy"].startswith("2.1."), "Diagnostic did not install SQLAlchemy 2.1")
        require(diagnostic_report["driver"] == "psycopg", "Diagnostic did not select psycopg")
        require(diagnostic_report["psycopg2_import"] == "psycopg2", "Retained driver did not import")
        require(not diagnostic_report["psycopg_available"], "Unexpected psycopg v3 installation")
        require(
            diagnostic_report.get("exception")
            == {"type": "ModuleNotFoundError", "name": "psycopg", "message": "No module named 'psycopg'"},
            "Diagnostic did not reproduce the exact missing psycopg exception",
        )

        stage = "postgres"
        # spec: backend-docker-startup/data-preserving-isolated-startup-verification
        network_created = True
        docker("network", "create", network)
        database = f"deckdex-postgres-{suffix}"
        containers.append(database)
        docker(
            "create",
            "--name",
            database,
            "--network",
            network,
            "--network-alias",
            "db",
            "--tmpfs",
            "/var/lib/postgresql/data",
            "-e",
            "POSTGRES_USER=deckdex",
            "-e",
            "POSTGRES_PASSWORD=deckdex",
            "-e",
            "POSTGRES_DB=deckdex",
            "postgres:15-alpine",
            timeout=PACKAGE_TIMEOUT,
        )
        docker("start", database)
        deadline = time.monotonic() + DB_TIMEOUT
        while True:
            require_running(database)
            # TCP excludes the temporary Unix-socket-only initialization server.
            ready = subprocess.run(
                ["docker", "exec", database, "pg_isready", "-h", "127.0.0.1", "-U", "deckdex", "-d", "deckdex"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=PROBE_TIMEOUT,
            )
            if ready.returncode == 0:
                break
            require(time.monotonic() < deadline, f"PostgreSQL readiness timeout: {ready.stdout}{ready.stderr}")
            time.sleep(1)

        stage = "startup"
        backend = f"deckdex-backend-{suffix}"
        containers.append(backend)
        docker("create", "--name", backend, "--network", network, "-e", f"DATABASE_URL={DATABASE_URL}", image)
        docker("start", backend)
        result["startup"] = check_boot(backend, 1)
        stage = "final_dependencies"
        final_report = python_probe(backend, DEPENDENCY_PROBE, "connect")
        result["final_dependencies"] = final_report
        print(json.dumps({"final_dependencies": final_report}), flush=True)
        # spec: backend-docker-startup/reproducible-dependency-incompatibility-evidence
        require(final_report["sqlalchemy"].startswith("2.0."), "Final image must use SQLAlchemy 2.0.x")
        require(final_report["driver"] == final_report.get("dbapi") == "psycopg2", "Final driver must be psycopg2")
        require(final_report.get("select_1") == 1 and "exception" not in final_report, "Real SELECT 1 failed")
        require(not final_report["psycopg_available"], "Final image unexpectedly contains psycopg v3")

        stage = "sentinel_insert"
        sentinel = python_probe(backend, SENTINEL_PROBE, "insert", f"Startup sentinel {suffix}")
        result["sentinel_before"] = sentinel
        stage = "restart"
        docker("restart", "--time", "10", backend)
        result["restart"] = check_boot(backend, 2)
        stage = "sentinel_preservation"
        result["sentinel_after"] = python_probe(backend, SENTINEL_PROBE, "read", str(sentinel["id"]))
        # spec: backend-docker-startup/data-preserving-isolated-startup-verification
        require(result["sentinel_after"] == sentinel, "Sentinel id/name/set/quantity changed across startup")
        result["data_preserved"] = True
        result["success"] = True
        stage = "complete"
    except (Exception, KeyboardInterrupt) as error:
        result["error"] = f"{type(error).__name__}: {error}"
        for container in containers:
            try:
                logs = docker("logs", container)
                print(f"Logs for {container}:\n{logs.stdout}", file=sys.stderr)
            except Exception as log_error:
                print(f"Cannot collect logs for {container}: {log_error}", file=sys.stderr)
    finally:
        for container in reversed(containers):
            try:
                docker("rm", "--force", container)
            except Exception as error:
                cleanup_errors.append(str(error))
        if network_created:
            try:
                docker("network", "rm", network)
            except Exception as error:
                if "No such network" not in str(error):
                    cleanup_errors.append(str(error))
        # Removing a unique tag cannot remove another invocation's image tag.
        try:
            docker("image", "rm", image)
        except Exception as error:
            if "No such image" not in str(error):
                cleanup_errors.append(str(error))
        if cleanup_errors:
            result["cleanup_errors"] = cleanup_errors
            if result["success"]:
                stage = "cleanup"
                result["success"] = False
        result["stage"] = stage
        print(json.dumps(result, sort_keys=True), flush=True)
    # spec: backend-docker-startup/executable-failure-evidence
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
