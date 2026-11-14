# Design

## Context

See proposal.md for motivation. The production change is one dependency boundary; a Docker harness is necessary because existing tests do not exercise package resolution or the entrypoint. Python target is 3.11 (`backend/Dockerfile`, `.python-version`); the host offers `python3.11` 3.11.14 and Docker server 24.0.6. No local virtual environment or installed application-package inventory was supplied. Requirements declare SQLAlchemy >=2.0.0, psycopg2-binary >=2.9.9, FastAPI 0.109.0, uvicorn 0.27.0 and Pydantic 2.5.0. These are declarations, not measured rebuilt-image versions.

The upstream SQLAlchemy 2.1 migration guide explicitly changes the default PostgreSQL DBAPI to psycopg v3 for bare `postgresql://` URLs: https://docs.sqlalchemy.org/en/21/changelog/migration_21.html#default-postgresql-driver-changed-to-psycopg-psycopg-3 . This explains how an unbounded requirement can select a driver not installed by this repository. Historical SQLAlchemy 2.1.8 remains historical evidence; actual installed versions must be emitted by the harness. No clarification requiring a requester decision remains: the ticket specifies driver, URL, preservation constraints and the conditional fix, and upstream documentation resolves the driver-selection question at design level. Container evidence will confirm it at implementation time.

## Goals / Non-Goals

**Goals:** Restore the psycopg2 default-driver compatibility boundary and prove migration-to-API startup using the shipped image and its actual entrypoint. Make the evidence reproducible as command output.

## Non-Goals

No psycopg v3 dependency, database schema or migration changes, application refactoring, endpoint changes, exact patch-version lock, general dependency upgrades, CI expansion, frontend changes, production ports/CORS changes, `.env` or secret edits, or operations on existing PostgreSQL volumes.

## Local reference patterns

- `backend/Dockerfile`: Python 3.11, pip installation of core then API requirements, copies scripts/migrations, uses `backend/docker-entrypoint.sh`; preserve this build path and default command.
- `backend/docker-entrypoint.sh`: `set -e`, invokes `python scripts/setup_db.py` when DATABASE_URL exists, then `exec` starts uvicorn. Migration failure must remain fatal; the smoke check must not replace the startup command with a test server or call migrations separately as its positive proof.
- `scripts/setup_db.py`: `create_database_if_not_exists()` imports psycopg2 directly; `run_migrations()` calls `create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")`, executes sorted SQL then Python migrations and prints `Migrations completed.` and `Database is ready.`. Preserve all signatures, SQL splitting and error behavior.
- `backend/api/db.py:get_engine()` creates the shared engine without a driver override. `deckdex/storage/repository.py:PostgresCollectionRepository._get_engine()` similarly defers driver choice. A dependency bound addresses all callers without changing their layering.
- `backend/api/main.py:health_check()` is async but performs a synchronous SELECT 1 via the shared engine; connected returns HTTP 200 with status healthy/database connected, exceptions return HTTP 503 with status degraded/database error. No API or rendering/state changes are needed. Readiness must await the real endpoint rather than assume a running container is healthy.
- `tests/test_setup_db.py:TestSqlSplitting` contains plain pytest assertions over reproduced SQL-splitting helpers. `tests/test_api.py:TestHealth` uses unittest/TestClient without a real PostgreSQL startup. Neither establishes installed-driver compatibility.
- `.github/workflows/ci.yml:backend` uses Python 3.11, PostgreSQL, dependency installation, real setup_db invocation, ruff and pytest. `pyproject.toml` declares pytest markers and Python 3.11 lint target. No equivalent Docker migration-to-health smoke harness exists in `scripts/` or `tests/`; add a focused executable harness there, not a new application layer. Its assertions run with Docker, not mocks.
- `migrations/005_users_table.sql`, `006_add_user_id.sql`, `007_add_quantity_to_cards.sql`, `009_group_cards_by_name_set.sql` establish a seed user, required user_id, quantity, and repeatable deduplication. Use a single sentinel card referencing the seed user, a unique nonempty name/set and quantity >1 so repeat migrations must preserve actual row identity and quantity.
- `docker-compose.yml` supplies `postgresql://deckdex:deckdex@db:5432/deckdex` and postgres:15-alpine. Reuse these exact nonsecret local test values and the db network alias in the isolated smoke topology. Do not invoke the user's Compose project or load its `.env`.

## Decisions

### Smallest production correction

After the diagnostic container demonstrates the documented 2.1 selection/import failure, replace only the SQLAlchemy declaration with `sqlalchemy>=2.0,<2.1`. Retain `psycopg2-binary>=2.9.9` verbatim. Add a short adjacent comment explaining the bare-URL default-driver boundary. No new production dependencies, ports, interfaces or files are needed. If evidence contradicts the documented mechanism, emit the discrepancy as a failed check; do not guess a different correction or broaden the file boundary.

Rejected alternatives:
- Install psycopg v3: violates the ticket and leaves direct psycopg2 creation in place.
- Change URLs to explicit psycopg2: violates the required Compose URL contract and touches multiple callers unnecessarily.
- Pin an exact SQLAlchemy patch or add a lock system: larger dependency policy change than required.
- Only assert requirement text or use mocked migration tests: cannot demonstrate real startup.

### One self-contained executable regression check

Create `scripts/verify_backend_docker.py`, runnable with `python3.11 scripts/verify_backend_docker.py`, using host standard-library subprocess, JSON, timing and path helpers only. Include usage, causal explanation and the upstream reference in its module documentation. Keep helpers local and plain. Use subprocess argument arrays, explicit repository cwd and finite timeouts; never shell-interpolate environment values.

The command performs the following cohesive regression test:

1. Check Docker availability and build `backend/Dockerfile` from the repository root with `docker build --no-cache --load`, a unique tag, and the existing Dockerfile unchanged. No bind mounts of source or local environment files. Record image identity and Python/package versions. Use this unchanged image for positive assertions.
2. In a separate disposable diagnostic container from that built image, override the entrypoint only for diagnosis, install `sqlalchemy>=2.1,<2.2` there, then start a fresh Python process to report resolved SQLAlchemy/psycopg2-binary versions, psycopg availability and the dialect driver selected for the Compose URL. Use `sqlalchemy.engine.make_url(url).get_dialect().driver` (public URL.get_dialect API documented at https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.engine.URL.get_dialect). Confirm `create_engine(url)` fails specifically with ModuleNotFoundError whose name is psycopg, while psycopg2 imports. Treat the expected error as successful causal reproduction, not as a passed positive startup. Never install psycopg v3 or modify the image or repository. Emit diagnostics before assertions so a disagreement remains visible. This supplies current installed-package evidence of the incompatibility without asserting the historical patch version.
3. Start postgres:15-alpine with the Compose test database/user/password, network alias db and a unique private network. Mount PostgreSQL data on container tmpfs, so no existing or named PostgreSQL volumes are mounted, created, deleted or inspected. Poll pg_isready with a deadline before launching the backend. No host ports are published.
4. Start the unchanged freshly built backend image with the exact Compose DATABASE_URL using its default ENTRYPOINT and CMD. Only explicit disposable test environment values are passed; do not forward host secrets. Collect migration/startup logs. From inside the running backend, report installed SQLAlchemy and psycopg2-binary distribution versions, dialect driver and DBAPI module; assert 2.0.x, psycopg2 and successful real connection. No pip changes in this positive container.
5. Poll GET http://127.0.0.1:8000/api/health from inside the backend using standard-library urllib; require HTTP 200 and both status healthy and database connected. Check container state throughout, require migration completion log markers and no missing-psycopg traceback. Repeat health after a bounded settling interval and ensure the backend still runs.
6. Insert a sentinel card through test-only SQL in the disposable database, committing a single nonduplicate row with the seed user's id and quantity >1. Record id/name/set/quantity. Restart only the backend container (the database and its data remain in place), exercising the normal entrypoint/migrations again; require new completion markers, repeated healthy/connected response and unchanged sentinel fields. No SQL changes or migration workarounds are allowed in the application.
7. Emit a concise structured JSON result to stdout including diagnostic and final image versions/drivers, expected import error, migration/startup/health/restart/data-preservation assertions, and a success/failure stage. Docker/build/registry/timeouts are failures with explicit reasons, never skipped successes. Host verification captures stdout/stderr; measured evidence is not written into frozen planning artifacts or hand-recorded later.

Use UUID resource names and track only IDs created by this invocation. Cleanup in finally and on interruption removes only owned containers, network and image tag, never prune, compose down, shared images or any existing volume. Bound build/package operations (for example 15 minutes), DB readiness (60 seconds), HTTP readiness per boot (120 seconds) and each probe (5 seconds); poll briefly and fail early on container exit. On failure emit owned-container logs and preserve the original failing stage; cleanup errors must not hide it. A missing Docker daemon or failed build must produce nonzero exit. Use test-only credentials and avoid printing environment dumps or real connection URLs.

## Blast radius

Implementation file boundary (relative to repository root):

| File | Action | Required reason |
| --- | --- | --- |
| `requirements.txt` | Modify | Bound SQLAlchemy to >=2.0,<2.1 on confirmed evidence; preserve psycopg2 declaration and explain driver compatibility. |
| `scripts/verify_backend_docker.py` | Create | Executable real-container regression check, causal version/driver report, health/restart/data assertions, failure diagnostics and ownership-scoped cleanup. |

Planning artifacts authored by this role only: `openspec/changes/runtime-9562679636f1d993db6f/proposal.md`, `design.md`, `specs/backend-docker-startup/spec.md`, `tasks.md`. The developer may only tick task checkboxes in tasks.md; proposal/design/spec evidence stays frozen.

No existing user/API documents, locale strings, schema/contracts, config examples or migrations become stale: no user interface, procedure or public contract changes. Harness documentation lives in its own module docstring. `docker-compose.yml`, `backend/Dockerfile`, `backend/docker-entrypoint.sh`, `scripts/setup_db.py`, `tests/test_setup_db.py`, and all existing specs remain unchanged.

## Acceptance checks

All criteria are proved by the proposed host command `python3.11 scripts/verify_backend_docker.py`:

| Acceptance criterion | Automated evidence |
| --- | --- |
| Cause with installed versions and selected driver | Fresh-image package report plus disposable 2.1 diagnostic report and exact missing psycopg exception; causal explanation in harness documentation. |
| Fresh image migrates with Compose postgresql:// URL | No-cache actual Dockerfile build, unmodified positive image, normal entrypoint completion logs and database probe. |
| API stays running, HTTP 200 healthy/connected | Readiness poll, repeated health after settling, running-state assertion before and after backend restart. |
| Actual container startup, no mock-only proof | Docker run of shipped ENTRYPOINT/CMD, no source bind mounts, real PostgreSQL and real HTTP. |
| Preserve existing data; no volume deletion or .env edits | Isolated tmpfs PostgreSQL; sentinel card survives repeated real migrations; no access to existing volumes or .env. |

The same command can run existing focused tests with `docker exec <backend> python -m pytest tests/test_setup_db.py` only if tests were copied, but the production image does not copy tests; do not add such a command or alter the Dockerfile. Existing SQL splitting logic is unchanged, and this focused regression command is the verification proposal required for this change. Do not invent a host virtual environment prerequisite.

## Risks / Trade-offs

- Registry/package availability or Docker socket denial can block execution → report phase and stderr with nonzero exit; host Docker reachability is already established, so this is not a requester question or a planned manual gate.
- Floating patch versions still vary → record resolved packages each invocation; constrain the relevant incompatible minor series without promising byte-identical image reproducibility.
- Diagnostic 2.1 probe downloads an incompatible version deliberately → it is isolated from the final-image startup and discarded; never changes production dependencies.
- Existing SQL/Python migrations can have independent defects → use the real runner and report failures without fixing unrelated migrations. Migration 011's legacy image-table behavior is unchanged.
- Repeat migrations may mutate unrelated historical data → sentinel proves the touched startup path for a representative existing card, not a comprehensive audit of historical migrations; all actual user storage remains untouched by verification.
- Harness execution is expensive → one bounded build and two backend boots, not a general performance benchmark; no hot-path overhead or speculative optimization is introduced.
- Concurrent invocations or an interrupted run → unique IDs and ownership-scoped cleanup prevent collisions; a hard kill may leave only invocation-owned resources and must never justify a global cleanup.

## Migration Plan

No database or persisted-format migration is introduced. Rebuild and restart the backend with existing PostgreSQL data retained; the preexisting entrypoint runs the same migrations. The fix is reversible by changing the dependency bound, although reverting it can restore the import failure. Do not delete volumes, change `.env`, or change the URL to deploy or roll back.

## Out-of-scope findings

Legacy main specs omit modern Purpose structure; leave them untouched and add only the new capability delta. Existing deployment/migration docs and broader dependency policies are not repaired. SQL splitting tests reproduce implementation logic rather than exercising the runner; replacing them is outside this startup fix.
