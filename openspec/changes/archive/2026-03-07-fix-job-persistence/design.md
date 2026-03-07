## Context

The job system is hybrid: three module-level dicts in `process.py` (`_active_jobs`, `_job_results`, `_job_types`) hold runtime state; a `jobs` table (migration 008) persists lifecycle via `JobRepository`. This gives the system resilience after crashes, but only if code actually uses the repository consistently. Six gaps mean it does not.

Current call paths for job persistence:
- `ProcessorService.process_cards_async` → calls `_persist_job_start` / `_persist_job_end` (correct)
- `ProcessorService.update_prices_async` → calls `_persist_job_start` / `_persist_job_end` (correct)
- `ProcessorService.update_single_card_price_async` → does NOT call either (bug 5)
- `ImporterService.run_async` → calls `job_repo.create_job` / `job_repo.update_job_status` inline (correct)
- `catalog_service.start_sync` → uses `job_repo._engine()` with raw SQL; writes `'completed'`/`'failed'` (bugs 4, 6)
- `GET /api/jobs/{job_id}` → only checks in-memory (bug 1)
- `GET /api/jobs/history` → shadowed by `GET /api/jobs/{job_id}` (bug 3)
- Startup → no orphan cleanup (bug 2)
- `websocket_progress` → validates job only against in-memory dicts (related to bug 1)

## Goals / Non-Goals

**Goals:**

1. Fix route ordering so `/history` is reachable.
2. Make `GET /api/jobs/{job_id}` return jobs that exist only in Postgres.
3. Mark stale `running` jobs as `error` on backend startup.
4. Normalize status values to `'complete'` / `'error'` across all writers.
5. Add DB persistence to `update_single_card_price_async`.
6. Refactor `catalog_service` to use `JobRepository` public methods.
7. Extend WebSocket job-validation to include DB lookup.

**Non-Goals:**

- Persisting in-memory `_active_jobs` / `_job_results` to Postgres (remains hybrid).
- Changing eviction TTL or result caching.
- Frontend changes (the API contract is already correct for the frontend once server bugs are fixed).
- Adding a new migration (status normalization uses existing VARCHAR column; no schema change needed).

## Decisions

### Decision 1: Add `get_job` and `mark_orphans_as_error` to `JobRepository`

**Why**: Two new repository methods are needed—a single-row lookup (`get_job(job_id)`) used by the `GET /api/jobs/{job_id}` DB fallback and the WebSocket validator, and a bulk update (`mark_orphans_as_error`) for startup cleanup. Adding these to `JobRepository` keeps all DB ops in one place, consistent with the core convention that all DB operations go through the storage layer.

**Alternative considered**: Inline SQL in the route handler or a startup hook in `main.py`. Rejected because it violates the "no raw SQL outside repository" convention and makes the logic untestable in isolation.

### Decision 2: Run orphan cleanup as a FastAPI `startup` event handler in `main.py`

**Why**: `main.py` already has the `app` instance and is the natural place to register startup hooks. The cleanup is a one-shot operation that should run before any request is served. `JobRepository` is accessed via `get_job_repo()` (the existing DI factory), so the startup handler stays thin.

**Implementation**: `mark_orphans_as_error` issues:
```sql
UPDATE jobs
SET status = 'error',
    completed_at = NOW() AT TIME ZONE 'utc',
    result = '{"error": "Server restarted while job was running"}'::jsonb
WHERE status = 'running';
```
This is intentionally broad (no `user_id` filter) because orphans from any user are stale after a restart.

**Caveat**: If `job_repo` is `None` (Google Sheets mode), the startup hook is a no-op. This is correct.

### Decision 3: Status canonical set is `'running'`, `'complete'`, `'error'`, `'cancelled'`

**Why**: `JobRepository.update_job_status` already uses `'complete'` / `'error'` in its `CASE` expression for setting `completed_at`. `process.py` list endpoint filters on `("complete", "error", "cancelled")`. Making catalog_service and the DB `completed_at` logic consistent requires the catalog to write the same values.

The `catalog_service` must write `'complete'` (not `'completed'`) on success and `'error'` (not `'failed'`) on failure.

**Migration note**: No migration needed. The `status` column is `VARCHAR(32)` with no `CHECK` constraint; existing rows with `'completed'`/`'failed'` are legacy and will simply not match the standard filter. The orphan cleanup at startup will have already zeroed out any `'running'` rows; the few old `'completed'`/`'failed'` rows in history are cosmetic and do not affect correctness going forward.

### Decision 4: DB fallback in `get_job_status` returns a synthesized `JobStatus` from `get_job()`

**Why**: The `JobStatus` Pydantic model expects `start_time` (ISO string). `JobRepository.get_job()` returns `created_at` from the DB, which maps directly to `start_time`. The `progress` field is populated from the DB `result` JSONB (or empty dict if null).

### Decision 5: WebSocket job validation falls back to DB

**Why**: Without this, a reconnecting client after a restart gets a 4004 close even though the job exists in Postgres (now with `status='error'` after orphan cleanup). The validator should call `get_job()` as a secondary check. If the DB job exists (even as error/complete), accept the connection—the `connected` ack will include the real status, and if the job is complete the handler will immediately send the complete event.

**Alternative considered**: Skip DB validation entirely (trust any UUID). Rejected because the spec explicitly requires 4004 for unknown job IDs, and we want to preserve that safety property.

### Decision 6: `catalog_service` uses `job_repo.create_job()` and `job_repo.update_job_status()`

**Why**: `job_repo._engine()` is a private method (underscore prefix) and directly coupling to it violates encapsulation. The public `create_job` / `update_job_status` interface already handles everything the catalog needs. The only reason it was using raw SQL is that the catalog sync predates `JobRepository`'s public API being complete.

**Concrete change**: Replace the two raw-SQL INSERT/UPDATE blocks with:
```python
job_repo.create_job(user_id=None, job_type="catalog_sync", job_id=job_id)
# ... on success:
job_repo.update_job_status(job_id, "complete", result_summary)
# ... on failure:
job_repo.update_job_status(job_id, "error", result_summary)
```

Note: `catalog_service.start_sync` does not receive a `user_id`. The `create_job` signature already accepts `user_id=None` (nullable FK), so this is compatible with the DB schema.

### Decision 7: Route reordering — `/history` before `/{job_id}`

**Why**: FastAPI matches routes in registration order. `GET /api/jobs/{job_id}` matches the literal string "history" as a path parameter. The fix is purely a reorder: define the `get_job_history` route handler before `get_job_status`. No logic changes.

## Detailed Implementation Per Fix

### Fix 1: Route reordering (`process.py`)

Move the `@router.get("/jobs/history")` handler to appear before `@router.get("/jobs/{job_id}")` in the file. No other changes to either handler.

### Fix 2: DB fallback in `get_job_status` (`process.py` + `job_repository.py`)

Add to `JobRepository`:
```python
def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
    """Return a single job row by UUID, or None if not found."""
```

In `get_job_status`, after the two in-memory checks fail, call:
```python
job_repo = get_job_repo()
if job_repo:
    db_job = job_repo.get_job(job_id)
    if db_job:
        return JobStatus(
            job_id=job_id,
            status=db_job["status"],
            progress=db_job.get("result") or {},
            start_time=db_job.get("created_at") or "",
            job_type=db_job.get("type", "unknown"),
        )
raise HTTPException(status_code=404, ...)
```

### Fix 3: Orphan cleanup on startup (`job_repository.py` + `main.py`)

Add to `JobRepository`:
```python
def mark_orphans_as_error(self, message: str = "Server restarted while job was running") -> int:
    """Mark all running jobs as error. Returns count of affected rows."""
```

In `main.py`:
```python
@app.on_event("startup")
async def cleanup_orphaned_jobs():
    job_repo = get_job_repo()
    if job_repo:
        count = job_repo.mark_orphans_as_error()
        if count:
            logger.warning(f"Marked {count} orphaned running jobs as error on startup")
```

### Fix 4: Status normalization (`catalog_service.py`)

- `final_status = "complete"` (was `"completed"`)
- On exception: `final_status = "error"` (was set to `"error"` already—but the raw SQL wrote `'failed'`). Both the in-memory `final_status` variable and the raw SQL must be corrected.

### Fix 5: Persist single-card price update (`processor_service.py`)

At the top of `update_single_card_price_async`, add:
```python
self._persist_job_start("update_price")
```

After the executor returns, before emitting the complete event, add:
```python
self._persist_job_end(self.status, result)
```

In the `except` branch:
```python
self._persist_job_end("error", {"status": "error", "error": str(e)})
```

### Fix 6: Refactor catalog_service (`catalog_service.py`)

Replace the two `engine = job_repo._engine()` blocks with calls to `job_repo.create_job()` and `job_repo.update_job_status()`.

### Fix 7: WebSocket job validation fallback (`websockets/progress.py`)

After the existing check `if job_id not in _active_jobs and job_id not in _job_results`, add:
```python
from ..dependencies import get_job_repo
job_repo = get_job_repo()
db_job = job_repo.get_job(job_id) if job_repo else None
if db_job is None:
    await websocket.close(code=4004, reason="Job not found")
    return
```

The existing initial-progress/complete logic already handles `job_id in _job_results`; for DB-only jobs (post-restart) the `elif job_id in _job_results` branch won't match, so the handler sends just the `connected` ack. The client's REST fallback in the `useWebSocket` hook will retrieve the full status—this is acceptable given the spec requirement that the hook fetches `GET /api/jobs/{id}` on reconnect.

## Risks / Trade-offs

- **Startup performance**: `mark_orphans_as_error` runs at startup and blocks until complete. The query is a full table scan on the `status` column. At expected scale (hundreds of jobs max), this is negligible. A `CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)` could be added as a follow-up migration if profiling ever shows it as a concern.

- **Status row legacy data**: Existing `'completed'` / `'failed'` rows in the DB are not back-filled. The `/api/jobs` list endpoint only includes them via the `completed_at` recency filter, and their status strings will render as-is on the frontend. This is acceptable cosmetic debt; a one-time migration can fix it if needed.

- **catalog_service `user_id=None`**: Catalog sync jobs will have a `NULL` user_id in the `jobs` table (always has been, since raw SQL didn't set it either). The `get_job_history` query filters by `user_id`, so catalog sync jobs will not appear in user-specific history. This is the existing behavior and is not changed by this fix.

- **`on_event("startup")` deprecation**: FastAPI 0.95+ deprecates `on_event` in favor of `lifespan`. However, the codebase already uses `on_event` elsewhere (if any). If the project uses `lifespan`, the startup hook should be placed there instead. The developer should check `main.py` and use the existing pattern.

## Migration Plan

1. Apply code changes (no DB migration required).
2. Restart the backend — the startup hook fires, orphans are cleaned.
3. Verify via `GET /api/jobs/history` (now reachable) that no `running` rows remain.
4. No rollback complexity: all changes are additive or reorders. If catalog_service writes break, the `except` block already logs and continues.

## Open Questions

- None. All decisions have been made above.
