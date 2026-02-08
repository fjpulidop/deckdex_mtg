#!/bin/sh
set -e
# Run DB migrations when DATABASE_URL is set (e.g. in Docker with Postgres)
if [ -n "$DATABASE_URL" ] && [ "$DATABASE_URL" != "" ]; then
  echo "Running database migrations..."
  cd /app && python scripts/setup_db.py
fi
exec "$@"
