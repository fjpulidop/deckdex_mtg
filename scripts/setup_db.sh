#!/usr/bin/env bash
# Create DeckDex DB and run migrations.
# Option 1: With Docker (recommended) – start Postgres and run migrations.
# Option 2: Local Postgres – use DATABASE_URL and psql, or run scripts/setup_db.py from a venv.

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
  echo "Using Docker to start Postgres and run migrations..."
  docker compose up -d db
  echo "Waiting for Postgres to be ready..."
  sleep 3
  for f in migrations/*.sql; do
    [ -f "$f" ] || continue
    echo "Running $f..."
    docker compose exec -T db psql -U deckdex -d deckdex < "$f"
  done
  # Run Python migrations inside the backend container (has Python + deps)
  for f in migrations/*.py; do
    [ -f "$f" ] || continue
    echo "Running $f..."
    docker compose exec -T backend python "/app/$f"
  done
  echo "Database is ready. DATABASE_URL for local backend: postgresql://deckdex:deckdex@localhost:5432/deckdex"
  exit 0
fi

if command -v psql >/dev/null 2>&1; then
  export DATABASE_URL="${DATABASE_URL:-postgresql://localhost:5432/deckdex}"
  echo "Using psql with DATABASE_URL..."
  for f in migrations/*.sql; do
    [ -f "$f" ] || continue
    echo "Running $f..."
    psql "$DATABASE_URL" -f "$f"
  done
  # Run Python migrations locally
  for f in migrations/*.py; do
    [ -f "$f" ] || continue
    echo "Running $f..."
    python "$f"
  done
  echo "Database is ready."
  exit 0
fi

echo "No Docker nor psql found. Use a Python venv and run: pip install -r requirements.txt && python scripts/setup_db.py"
exit 1
