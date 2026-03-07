## Why

The hybrid in-memory + Postgres job architecture has six concrete bugs that cause data loss, silent failures, and broken API contracts: jobs vanish after a backend restart, stale "running" rows accumulate in the DB after crashes, the `/history` route is unreachable due to FastAPI route-ordering, status values are inconsistent between job types causing list filtering to misreport state, the single-card price update never writes to Postgres, and `catalog_service` bypasses `JobRepository` entirely via a private `_engine()` call. These bugs undermine the reliability guarantees that the global-jobs-ui and websocket-progress specs require.

## What Changes

- **Route ordering**: Move `GET /api/jobs/history` before `GET /api/jobs/{job_id}` in `process.py` so FastAPI doesn't shadow it with the parameterized route.
- **DB fallback in GET /api/jobs/{job_id}**: After checking in-memory dicts, query `JobRepository` as a fallback so jobs persisted to Postgres survive a backend restart.
- **Orphan cleanup on startup**: On backend startup, mark any job with `status = 'running'` as `status = 'error'` with a "server restarted" message, so stale rows don't accumulate.
- **Status normalization**: Standardize on `'complete'` / `'error'` across all job writers. `catalog_service` currently writes `'completed'` and `'failed'`; these deviate from the canonical enum used by `JobRepository.update_job_status` and the list-endpoint filter.
- **Persist single-card price update**: `update_single_card_price_async` in `ProcessorService` must call `_persist_job_start("update_price")` and `_persist_job_end(status, result)` exactly like `process_cards_async` and `update_prices_async`.
- **Refactor catalog_service**: Replace direct `job_repo._engine()` raw SQL with `job_repo.create_job()` and `job_repo.update_job_status()` calls.
- **WebSocket job validation fallback**: `websocket_progress` currently rejects connections when `job_id` is absent from the in-memory dicts. After DB fallback is in place, it should also accept connections for jobs known to Postgres.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `websocket-progress`: The job-validation rule ("invalid job_id → close 4004") must be extended to allow connections for job IDs found in Postgres (not only in-memory dicts).
- `global-jobs-ui`: No spec-level requirement changes; implementation fixes only.

## Impact

- `backend/api/routes/process.py` — route reordering, DB fallback in `get_job_status`, startup orphan cleanup hook
- `backend/api/services/processor_service.py` — add persist calls to `update_single_card_price_async`
- `backend/api/services/catalog_service.py` — replace raw SQL with `JobRepository` methods
- `backend/api/websockets/progress.py` — extend job-validation to include DB lookup
- `deckdex/storage/job_repository.py` — add `get_job` (single-row lookup) method; add `mark_orphans_as_error` method
- `backend/api/main.py` — call orphan cleanup on startup
- `tests/` — unit tests for each fix

## Non-goals

- No change to the in-memory eviction TTL or job result caching logic.
- No migration to make all job state fully persistent (remains hybrid).
- No new job types or new API endpoints beyond what the fixes require.
- No frontend changes (the API contract is already compatible once server-side bugs are fixed).
