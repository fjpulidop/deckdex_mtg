# Job Persistence Exploration

**Date:** 2026-03-07
**Status:** Complete

## What Exists

### Backend Job System Architecture

The job system has a **hybrid in-memory + Postgres** design:

**In-memory (process.py module-level globals):**
- `_active_jobs: Dict[str, ProcessorService]` -- running job service instances
- `_job_results: Dict[str, Tuple[dict, float]]` -- completed results with monotonic timestamp
- `_job_types: Dict[str, str]` -- maps job_id to type string
- TTL-based cleanup: `_JOB_RESULT_TTL_SECONDS = 3600` (1 hour), triggered lazily on next job creation

**Postgres persistence (migration 008_jobs_table.sql):**
- `jobs` table: `id UUID PK`, `user_id FK`, `type VARCHAR(64)`, `status VARCHAR(32) DEFAULT 'running'`, `created_at TIMESTAMPTZ`, `completed_at TIMESTAMPTZ`, `result JSONB`
- Index: `idx_jobs_user_created ON (user_id, created_at DESC)`
- `JobRepository` in `deckdex/storage/job_repository.py`: `create_job()`, `update_job_status()`, `get_job_history()`

**Which jobs persist to Postgres:**
- Process jobs (card processing): YES -- `ProcessorService._persist_job_start()` / `_persist_job_end()` called
- Price update jobs: YES -- same `ProcessorService` pattern
- Import jobs (`/api/import/external`, `/api/import/external/cards`): YES -- `ImporterService` calls `job_repo.create_job()` / `update_job_status()`
- Catalog sync jobs: PARTIALLY -- uses raw SQL directly (not through `JobRepository`), writes 'completed'/'failed' instead of 'complete'/'error'

**Job types in the system:**
- `process` -- full card data processing
- `update_prices` -- bulk price refresh
- `Update price` -- single card price (note: inconsistent capitalization)
- `import` -- collection import from file/text
- `catalog_sync` -- Scryfall bulk data sync (admin-only)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | List active + recently completed jobs (hybrid: in-memory + DB within 2h cutoff) |
| `/api/jobs/{job_id}` | GET | Single job status (in-memory only -- does NOT check DB) |
| `/api/jobs/history` | GET | DB-persisted job history (up to 100 rows) |
| `/api/jobs/{job_id}/cancel` | POST | Cancel running job (in-memory only) |
| `/api/process` | POST | Trigger card processing |
| `/api/prices/update` | POST | Trigger bulk price update |
| `/api/prices/update/{card_id}` | POST | Trigger single-card price update |

### WebSocket Progress

- `/ws/progress/{job_id}` -- real-time progress events (progress/error/complete)
- `ConnectionManager` handles multi-client broadcast per job_id
- On connect: validates job exists in `_active_jobs` or `_job_results` (in-memory)
- Sends initial progress snapshot on reconnect
- 30s heartbeat ping cycle
- Auth via `access_token` HTTP-only cookie

### Frontend Components

- `ActiveJobsContext` -- global React context; restores jobs via `GET /api/jobs` on mount; re-syncs on tab visibility change (debounced 2s)
- `JobsBottomBar` -- fixed bottom-right pill; expanded panel with Active/History tabs
- `ActiveJobs` -- full-width bottom bar with detailed job entries (progress, elapsed, cancel, errors)
- `JobLogModal` -- modal with detailed job progress, errors, timestamps
- Jobs auto-dismiss 5s after completion

## What's Missing

### Critical Issues

1. **`GET /api/jobs/{job_id}` does not check Postgres.** If the server restarts mid-job, in-memory state is lost, and this endpoint returns 404 even though the job row exists in the DB with status='running'. The WebSocket endpoint has the same problem -- it validates against `_active_jobs`/`_job_results` only.

2. **No recovery for running jobs on restart.** Jobs with `status='running'` in the DB after a restart are orphaned -- they never get updated to 'error' or 'cancelled'. The frontend will see them as running forever (via `GET /api/jobs` which does check DB), but WebSocket connections will fail (4004 "Job not found").

3. **Inconsistent status values.** Catalog sync writes `'completed'`/`'failed'` to the DB; all other job types write `'complete'`/`'error'`. The `GET /api/jobs` endpoint only checks for `'complete'`, `'error'`, `'cancelled'` statuses -- so catalog sync completed jobs may not appear correctly.

4. **Inconsistent job type naming.** `'Update price'` (capitalized, single card) vs `'update_prices'` (snake_case, bulk). Frontend has to display these as-is since there's no normalization.

### Missing Features

5. **No progress persistence.** During a running job, progress (current/total/percentage) lives only in `ProcessorService.progress_data`. If the user refreshes and the job is still running, the frontend re-fetches via `GET /api/jobs` which returns `progress: {}` from the DB row (no progress field in the jobs table). WebSocket reconnection helps if the server hasn't restarted, but doesn't help if it has.

6. **No error log persistence.** Per-card errors are tracked in `ProcessorService.progress_data["errors"]` (in-memory only). These are broadcast via WebSocket but never stored in the DB. The `result` JSONB stores final summary but not individual card errors.

7. **No job cleanup policy.** The `jobs` table grows unbounded. No cleanup migration, no auto-delete of old records, no retention policy.

8. **No duplicate job detection across restarts.** The "only one process job at a time" check uses `_active_jobs` (in-memory). If a server crashes mid-job and restarts, the user can start a new process job while the old one's DB row still says 'running'.

9. **Single-card price update job not persisted.** `update_single_card_price_async()` does NOT call `_persist_job_start()` or `_persist_job_end()` -- it's completely ephemeral.

10. **Catalog sync uses raw SQL instead of JobRepository.** The catalog_service.py accesses `job_repo._engine()` (private method) and writes raw SQL to the jobs table, bypassing the repository pattern and using different status values.

### Minor Issues

11. **No pagination on job history.** `GET /api/jobs/history` returns up to 100 rows with no offset/cursor -- works for now but won't scale.

12. **Route ordering bug risk.** `GET /api/jobs/history` is defined AFTER `GET /api/jobs/{job_id}` -- FastAPI may match "history" as a job_id. (Actually tested: FastAPI routes are matched in order, so `/api/jobs/history` would match `{job_id}` first, returning 404.)

13. **No job duration in DB.** `created_at` and `completed_at` exist but no computed duration column or field in the API response. Frontend calculates elapsed from `startedAt` only.

## Improvement Ideas

| # | Idea | Description | Value (1-5) | Complexity (1-5) | Impact/Effort |
|---|------|-------------|-------------|-------------------|---------------|
| 1 | **Fix orphaned running jobs on startup** | On app startup (FastAPI lifespan), query `jobs WHERE status='running'` and update them to `status='error', result='{"error":"server_restarted"}'`. Prevents phantom "running" jobs in the frontend. | 5 | 1 | 5.0 |
| 2 | **Fix GET /api/jobs/{job_id} to check DB** | Fall through to `job_repo.get_job_by_id()` when job_id not in memory. Add `get_job_by_id()` to `JobRepository`. Makes individual job status queries reliable after restart. | 5 | 1 | 5.0 |
| 3 | **Normalize status values** | Fix catalog_service to use 'complete'/'error' (not 'completed'/'failed'). Fix single-card price type to 'update_price' (lowercase). Add a migration/fixup for existing rows. | 4 | 1 | 4.0 |
| 4 | **Persist single-card price update jobs** | Add `_persist_job_start()`/`_persist_job_end()` calls to `update_single_card_price_async()`. Currently the only fire-and-forget job type. | 3 | 1 | 3.0 |
| 5 | **Fix route ordering: /jobs/history before /jobs/{job_id}** | Move the `GET /api/jobs/history` route definition above `GET /api/jobs/{job_id}` to prevent FastAPI matching "history" as a path parameter. | 5 | 1 | 5.0 |
| 6 | **Add progress column to jobs table** | Add `progress JSONB` column to `jobs` table. Update `ProcessorService` and `ImporterService` to periodically persist current/total/percentage (throttled, e.g., every 5% or 10s). Enables progress recovery on refresh even after restart. | 4 | 3 | 1.3 |
| 7 | **Add error log persistence** | Store per-card errors in the `result` JSONB (or a separate `job_errors` table). Currently errors are lost when the job completes -- only error_count and not_found_cards[:20] survive. | 3 | 2 | 1.5 |
| 8 | **Refactor catalog_service to use JobRepository** | Replace raw SQL in catalog_service.py with `JobRepository.create_job()` / `update_job_status()`. Use consistent status values. Eliminates the `_engine()` private method access. | 4 | 2 | 2.0 |
| 9 | **Add job cleanup migration / retention policy** | Add a scheduled cleanup (e.g., on startup or as a periodic task) to DELETE jobs older than N days (e.g., 30). Or add a migration that creates a partial index + cron trigger. | 3 | 2 | 1.5 |
| 10 | **WebSocket validation against DB** | When WebSocket connects and job_id not in `_active_jobs`/`_job_results`, check the `jobs` table. If job exists with status='running', accept the connection (even though we can't resume progress). If complete/error, send final event. | 4 | 2 | 2.0 |
| 11 | **Add job duration to API response** | Compute `duration_seconds` from `created_at` and `completed_at` in the `get_job_history()` response. Saves frontend from calculating it. | 2 | 1 | 2.0 |
| 12 | **Consolidate in-memory job state into JobRepository** | Move `_active_jobs`, `_job_results`, `_job_types` into a proper `JobManager` class (injected via DI) rather than module globals. Enables testing and removes the implicit coupling between process.py and progress.py. | 4 | 3 | 1.3 |
| 13 | **Job retry mechanism** | Allow users to retry failed/errored jobs with a single click from the History tab. The backend would clone the original job parameters and create a new job. | 3 | 3 | 1.0 |

## Recommended Priority

### Tier 1: Quick fixes (< 1 hour each, high impact)
1. **Fix orphaned running jobs on startup** (#1) -- prevents confusing UX after any restart
2. **Fix route ordering** (#5) -- actual bug, trivial fix
3. **Normalize status values** (#3) -- data consistency
4. **Persist single-card price updates** (#4) -- consistency

### Tier 2: Reliability improvements (1-3 hours each)
5. **Fix GET /api/jobs/{job_id} to check DB** (#2) -- required for robust WebSocket reconnection
6. **WebSocket validation against DB** (#10) -- unblocks reconnection after restart
7. **Refactor catalog_service to use JobRepository** (#8) -- architectural cleanliness

### Tier 3: Feature enhancements (half-day each)
8. **Add progress column to jobs table** (#6) -- enables seamless restart recovery
9. **Job cleanup / retention policy** (#9) -- prevent unbounded growth
10. **Consolidate into JobManager** (#12) -- better architecture, easier testing

### Tier 4: Nice-to-have
11. **Error log persistence** (#7)
12. **Job duration in API** (#11)
13. **Job retry mechanism** (#13)

## Key Architectural Observations

- The hybrid in-memory + DB approach was intentional (MVP pragmatism) and works well for the single-server, localhost-only deployment model. Full DB-backed job management is only needed for restart recovery -- not for horizontal scaling.
- The `ProcessorService` already calls `_persist_job_start` / `_persist_job_end`, so the DB side mostly works. The gaps are in (a) reading from DB when memory is empty and (b) cleaning up stale running rows.
- The WebSocket layer couples tightly to `process.py` module globals (`_active_jobs`, `_job_results`). Introducing a `JobManager` class would decouple these.
- Catalog sync is the oddball -- it runs in a raw `threading.Thread` (not `BackgroundTasks`), uses raw SQL, and has its own status vocabulary. It should be brought in line with the rest.

## Files Reviewed

- `/Users/javi/repos/deckdex_mtg/backend/api/routes/process.py` -- main job endpoints + in-memory stores
- `/Users/javi/repos/deckdex_mtg/backend/api/services/processor_service.py` -- ProcessorService with job lifecycle
- `/Users/javi/repos/deckdex_mtg/backend/api/services/importer_service.py` -- ImporterService with job persistence
- `/Users/javi/repos/deckdex_mtg/backend/api/services/catalog_service.py` -- catalog sync with raw SQL job tracking
- `/Users/javi/repos/deckdex_mtg/backend/api/routes/import_routes.py` -- import endpoints creating background jobs
- `/Users/javi/repos/deckdex_mtg/backend/api/routes/catalog_routes.py` -- catalog sync trigger
- `/Users/javi/repos/deckdex_mtg/backend/api/routes/admin_routes.py` -- admin catalog sync
- `/Users/javi/repos/deckdex_mtg/backend/api/routes/stats.py` -- no job-related content
- `/Users/javi/repos/deckdex_mtg/backend/api/websockets/progress.py` -- WebSocket handler
- `/Users/javi/repos/deckdex_mtg/backend/api/dependencies.py` -- get_job_repo() factory
- `/Users/javi/repos/deckdex_mtg/deckdex/storage/job_repository.py` -- JobRepository class
- `/Users/javi/repos/deckdex_mtg/migrations/008_jobs_table.sql` -- jobs table schema
- `/Users/javi/repos/deckdex_mtg/openspec/specs/websocket-progress/spec.md` -- WebSocket spec
- `/Users/javi/repos/deckdex_mtg/openspec/specs/global-jobs-ui/spec.md` -- Global jobs UI spec
- `/Users/javi/repos/deckdex_mtg/frontend/src/contexts/ActiveJobsContext.tsx` -- React context for jobs
- `/Users/javi/repos/deckdex_mtg/frontend/src/components/JobsBottomBar.tsx` -- Bottom bar UI
- `/Users/javi/repos/deckdex_mtg/frontend/src/components/ActiveJobs.tsx` -- Active jobs component
- `/Users/javi/repos/deckdex_mtg/frontend/src/components/JobLogModal.tsx` -- Job log modal
