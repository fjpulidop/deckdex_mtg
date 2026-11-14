# Proposal

## Why

A fresh backend image can resolve SQLAlchemy outside the psycopg2-compatible default-driver line and fail during migrations with `ModuleNotFoundError: No module named 'psycopg'`. Local Docker startup must complete migrations and serve a database-connected health response without changing PostgreSQL data or local secrets.

## What Changes

- Confirm driver selection using installed packages in disposable containers and emit reproducible version/driver/error evidence.
- Once confirmed, constrain `sqlalchemy` to `>=2.0,<2.1`, retaining `psycopg2-binary>=2.9.9`, direct psycopg2 usage and the Compose `postgresql://` URL.
- Add an executable automated Docker smoke check that builds the actual backend image without cached dependency layers, runs its normal migration/API entrypoint against isolated PostgreSQL, checks health and checks data survival across restart. Its output records versions, driver, results and environment failures.

## Capabilities

### New Capabilities

- `backend-docker-startup`: Fresh-image PostgreSQL driver compatibility, migration-to-API startup and isolated regression evidence.

### Modified Capabilities

None. Existing health behavior in `openspec/specs/web-api-backend/spec.md` remains unchanged. That legacy capability lacks `## Purpose`; this change adds only requirements for Docker startup in the new capability rather than rewriting the existing spec. Deployment context in `openspec/specs/architecture/spec.md` remains unchanged.

## Impact

Only `requirements.txt` and a new `scripts/verify_backend_docker.py` verification harness. No API signatures, schemas, migrations, Compose configuration, Docker entrypoint, production environment, or persisted formats change. Verification requires reachable Docker and package/image registries; it uses its own resources and no host Python packages beyond the standard library.

## Non-goals

No psycopg v3 adoption, dependency refresh, frontend/mobile work, port or CORS changes, volume deletion, `.env` edits, or unrelated migration fixes.
