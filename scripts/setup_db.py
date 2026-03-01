#!/usr/bin/env python3
"""
Create the DeckDex database (if it does not exist) and run migrations.
Uses DATABASE_URL from environment or .env. Default: postgresql://localhost:5432/deckdex

Usage (from repo root):
  python scripts/setup_db.py
  # or with explicit URL:
  DATABASE_URL=postgresql://user:pass@localhost:5432/deckdex python scripts/setup_db.py
"""
import os
import sys
from pathlib import Path

# Load .env from repo root if present
repo_root = Path(__file__).resolve().parent.parent
dotenv = repo_root / ".env"
if dotenv.exists():
    with open(dotenv) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and value and key not in os.environ:
                    os.environ[key] = value

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/deckdex").strip()


def url_to_postgres_conn_str(url: str, dbname_override: str = None) -> str:
    """Build a libpq connection string from DATABASE_URL, optionally overriding dbname."""
    from urllib.parse import urlparse, unquote
    u = urlparse(url)
    if u.scheme not in ("postgresql", "postgres"):
        raise ValueError("DATABASE_URL must be postgresql:// or postgres://")
    dbname = (dbname_override or (u.path or "").lstrip("/")) or "postgres"
    netloc = u.netloc
    if "@" in netloc:
        auth, host_port = netloc.rsplit("@", 1)
        user, _, password = auth.partition(":")
        user = unquote(user)
        password = unquote(password) if password else ""
    else:
        user = password = ""
        host_port = netloc
    if ":" in host_port:
        host, _, port = host_port.rpartition(":")
    else:
        host = host_port
        port = "5432"
    parts = [f"host={host}", f"port={port}", f"dbname={dbname}"]
    if user:
        parts.append(f"user={user}")
    if password:
        parts.append(f"password={password}")
    return " ".join(parts)


def create_database_if_not_exists():
    """Connect to 'postgres' and create target database if it doesn't exist."""
    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        print("Error: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    from urllib.parse import urlparse
    u = urlparse(DATABASE_URL)
    dbname = (u.path or "").lstrip("/") or "deckdex"
    conn_str = url_to_postgres_conn_str(DATABASE_URL, "postgres")

    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    if cur.fetchone() is None:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
        print(f"Created database '{dbname}'.")
    else:
        print(f"Database '{dbname}' already exists.")
    cur.close()
    conn.close()


def run_migrations():
    """Run SQL migration files in order."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("Error: sqlalchemy not installed. Run: pip install sqlalchemy", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    migrations_dir = repo_root / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        print("No migration files found in migrations/", file=sys.stderr)
        sys.exit(1)

    def strip_leading_comments(s: str) -> str:
        """Remove leading lines that are empty or only comments, so we don't skip real statements."""
        lines = s.strip().splitlines()
        while lines and (not lines[0].strip() or lines[0].strip().startswith("--")):
            lines.pop(0)
        return "\n".join(lines).strip()

    with engine.connect() as conn:
        for path in sql_files:
            if path.name.startswith("."):
                continue
            print(f"Running {path.name}...")
            sql_content = path.read_text()
            for stmt in sql_content.split(";"):
                stmt = strip_leading_comments(stmt)
                if stmt:
                    conn.execute(text(stmt))

    # Run Python migrations (e.g. data migrations with run(database_url) signature)
    py_files = sorted(migrations_dir.glob("*.py"))
    for path in py_files:
        if path.name.startswith(".") or path.name.startswith("__"):
            continue
        print(f"Running {path.name}...")
        import importlib.util
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "run"):
            mod.run(DATABASE_URL)

    print("Migrations completed.")


def main():
    from urllib.parse import urlparse
    u = urlparse(DATABASE_URL)
    safe = f"{u.scheme}://***@{u.hostname or 'localhost'}:{u.port or 5432}{u.path}"
    print("Using:", safe)
    create_database_if_not_exists()
    run_migrations()
    print("Database is ready.")


if __name__ == "__main__":
    main()
