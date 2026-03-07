## 1. Route Ordering Fix

- [x] 1.1 In `backend/api/routes/process.py`, move the `get_job_history` handler (decorated with `@router.get("/jobs/history")`) to appear before the `get_job_status` handler (decorated with `@router.get("/jobs/{job_id}")`). No logic changes to either handler.
- [x] 1.2 Verify that `GET /api/jobs/history` now returns the job history list and is not intercepted by the `/{job_id}` route (manual curl test or automated test).

## 2. JobRepository: New Methods

- [x] 2.1 In `deckdex/storage/job_repository.py`, add `get_job(self, job_id: str) -> Optional[Dict[str, Any]]`. It should execute `SELECT id, user_id, type, status, created_at, completed_at, result FROM jobs WHERE id = :id::uuid` and return a dict with the same key names as `get_job_history` rows (plus `user_id`), or `None` if no row found.
- [x] 2.2 In `deckdex/storage/job_repository.py`, add `mark_orphans_as_error(self, message: str = "Server restarted while job was running") -> int`. It should execute `UPDATE jobs SET status = 'error', completed_at = NOW() AT TIME ZONE 'utc', result = :result::jsonb WHERE status = 'running'` and return the count of affected rows (via `rowcount`).

## 3. Startup Orphan Cleanup

- [x] 3.1 In `backend/api/main.py`, locate or add a startup hook (using `@app.on_event("startup")` or the existing `lifespan` handler, whichever pattern the file already uses). Call `get_job_repo()` and, if not `None`, call `job_repo.mark_orphans_as_error()`. Log a warning if the count is greater than zero.
- [x] 3.2 Confirm the hook is a no-op when `job_repo` is `None` (Google Sheets / no-DB mode).

## 4. DB Fallback in GET /api/jobs/{job_id}

- [x] 4.1 In the `get_job_status` handler in `backend/api/routes/process.py`, after the existing in-memory checks (`_active_jobs` and `_job_results`) both fail, add a DB fallback: call `get_job_repo()`, then `job_repo.get_job(job_id)` if repo is available. If a row is returned, construct and return a `JobStatus` with `status`, `progress` (from `result` field or `{}`), `start_time` (from `created_at`), and `job_type` (from `type`).
- [x] 4.2 Confirm the endpoint still raises HTTP 404 when the job is absent from both memory and Postgres.

## 5. Status Normalization

- [x] 5.1 In `backend/api/services/catalog_service.py`, change the initial value `final_status = "completed"` to `final_status = "complete"`.
- [x] 5.2 In the same file, in the `except` block inside `_run()`, change the raw SQL `status = 'failed'` to `status = 'error'`. (This block will be replaced by the refactor in task 6, so coordinate with task 6 to avoid double-editing.)

## 6. Refactor catalog_service to Use JobRepository API

- [x] 6.1 In `backend/api/services/catalog_service.py`, in `start_sync()`, replace the raw-SQL INSERT block (`engine = job_repo._engine()` / `conn.execute INSERT INTO jobs ...`) with `job_repo.create_job(user_id=None, job_type="catalog_sync", job_id=job_id)`.
- [x] 6.2 In the same file, in the success branch inside `_run()`, replace the raw-SQL UPDATE block (`status = 'completed'`) with `job_repo.update_job_status(job_id, "complete", result_summary)`.
- [x] 6.3 In the same file, in the exception branch inside `_run()`, replace the raw-SQL UPDATE block (`status = 'failed'`) with `job_repo.update_job_status(job_id, "error", result_summary)`.
- [x] 6.4 Remove all `from sqlalchemy import text` and `engine = job_repo._engine()` references from `catalog_service.py` (the service should have no direct SQLAlchemy usage after refactoring).
- [x] 6.5 Confirm that `catalog_service` still behaves correctly when `job_repo` is `None` (the existing `if job_repo:` guard must remain around all calls).

## 7. Persist Single-Card Price Update Jobs

- [x] 7.1 In `backend/api/services/processor_service.py`, in `update_single_card_price_async`, add `self._persist_job_start("update_price")` at the top of the method, immediately after setting `self.status = "running"` (mirror the pattern in `process_cards_async`).
- [x] 7.2 In the same method, in the normal completion path (after the executor returns and `self.status` is set), add `self._persist_job_end(self.status, result)` before emitting the complete event.
- [x] 7.3 In the same method, in the outer `except` block, add `self._persist_job_end("error", {"status": "error", "error": str(e)})` before re-raising.

## 8. WebSocket Job Validation DB Fallback

- [x] 8.1 In `backend/api/websockets/progress.py`, in the `websocket_progress` handler, after the existing check `if job_id not in _active_jobs and job_id not in _job_results`, add a DB fallback: import and call `get_job_repo()`, then call `job_repo.get_job(job_id)`. If the result is `None` (and repo was available), close with code 4004. If repo is `None` (no Postgres), close with code 4004 immediately (same as before).
- [x] 8.2 Ensure the existing in-memory close-4004 path still fires when no DB is configured and the job is not in memory.

## 9. Tests

- [x] 9.1 In `tests/`, add a test for `JobRepository.get_job` that covers: job found returns the expected dict; job not found returns `None`.
- [x] 9.2 Add a test for `JobRepository.mark_orphans_as_error` that: inserts two rows with `status='running'` and one with `status='complete'`, calls the method, confirms the two `running` rows are now `error` and the `complete` row is unchanged, and that the return value is `2`.
- [x] 9.3 Add a test for `GET /api/jobs/{job_id}` that verifies the DB fallback path: mock `_active_jobs` and `_job_results` as empty, mock `get_job_repo()` to return a repo whose `get_job()` returns a row, assert the endpoint returns 200 with correct fields.
- [x] 9.4 Add a test for `GET /api/jobs/{job_id}` that verifies 404 is returned when neither in-memory nor DB contain the job.
- [x] 9.5 Add a test for `GET /api/jobs/history` that confirms the route is reachable (not intercepted by `/{job_id}`).
- [x] 9.6 Add a test for `catalog_service.start_sync` that mocks `job_repo` and verifies it calls `create_job` and `update_job_status` (not `_engine`), and that the status written on success is `'complete'` and on failure is `'error'`.
- [x] 9.7 Add a test for `ProcessorService.update_single_card_price_async` that mocks `_persist_job_start` and `_persist_job_end` and verifies both are called, including in the error path.
