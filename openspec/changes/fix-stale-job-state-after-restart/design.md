## Context

Background jobs (catalog sync, card processing, price updates) use a hybrid state model:
- **In-memory**: `_active_jobs` dict in `process.py`, `_sync_lock` in `catalog_service.py`
- **Postgres**: `jobs` table (status, timestamps, results) and `catalog_sync_state` table (sync phase)

On restart, in-memory state resets but Postgres retains stale `running`/`syncing_*` statuses. The existing `mark_orphans_as_error()` handles the `jobs` table but nothing handles `catalog_sync_state`. The frontend's `ActiveJobsContext` restores jobs without checking status, creating ghost entries.

## Goals / Non-Goals

**Goals:**
- Catalog sync UI recovers to idle state after unclean restart
- Active jobs list does not show ghost jobs after restart
- No user intervention required to recover from stale state

**Non-Goals:**
- Persisting in-memory job state across restarts (that's a larger effort)
- Resuming interrupted jobs automatically
- Adding health-check polling for job liveness

## Decisions

1. **Startup cleanup for catalog sync state**: Add `mark_orphan_syncs()` to `CatalogRepository` that resets any `syncing_*` status to `idle`. Called from `startup_event()` alongside existing `mark_orphans_as_error()`.

2. **Frontend filtering by status**: `ActiveJobsContext.restoreJobs()` will only add jobs with status `running` or `pending` to the active list. Jobs marked as `error`/`complete`/`cancelled` by `mark_orphans_as_error()` will be excluded. This is the simplest fix — the backend already returns status, the frontend just ignores it.

3. **No new API endpoints**: The existing `GET /api/jobs` response already includes `status`. The frontend just needs to use it.

## Risks / Trade-offs

- **Race condition**: If the frontend fetches `/api/jobs` before `startup_event` completes, it could still see stale `running` jobs. Mitigation: FastAPI's `on_event("startup")` runs before the first request is served, so this is safe.
- **Catalog sync state reset**: If the server crashes mid-sync, resetting to `idle` means the partial sync data stays. This is acceptable — the user can re-trigger sync, and partial data is better than a permanently locked UI.
