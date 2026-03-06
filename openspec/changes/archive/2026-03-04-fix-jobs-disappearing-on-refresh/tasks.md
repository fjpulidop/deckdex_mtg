## 1. Backend: TTL-based cleanup

- [x] 1.1 Change `_job_results` to store `(result, completed_at)` tuples — update all writes to `_job_results` in `process.py` (run_process, run_update, cancel_job, single-card update)
- [x] 1.2 Rewrite `_cleanup_old_jobs()` to evict entries older than 1 hour instead of capping at 10
- [x] 1.3 Update `list_jobs` and `get_job_status` to read from the new tuple format

## 2. Backend: GET /api/jobs returns recently completed from Postgres

- [x] 2.1 In `list_jobs`, widen the Postgres query filter to include jobs with status `complete`/`error`/`cancelled` completed within the last 2 hours (in addition to `running`/`pending`)
- [x] 2.2 Ensure in-memory jobs are not duplicated when also present in Postgres results

## 3. Frontend: Restore completed jobs on mount

- [x] 3.1 In `ActiveJobsContext`, remove the filter that discards non-running/non-pending jobs during restore — pass all jobs from `GET /api/jobs` into state
- [x] 3.2 Ensure `JobsBottomBar` auto-dismisses restored completed/error/cancelled jobs after ~5s (verify existing behavior handles this)

## 4. Frontend: Re-sync on window focus

- [x] 4.1 Add a `visibilitychange` listener in `ActiveJobsProvider` that calls `GET /api/jobs` when the tab regains visibility
- [x] 4.2 Debounce the re-fetch (at least 2s) to prevent rapid tab-switching from spamming requests
- [x] 4.3 Reconcile response with local state: add new running jobs, remove jobs no longer in response

## 5. Frontend: WebSocket reconnection

- [x] 5.1 In `useWebSocket`, detect non-1000 close codes and trigger reconnection
- [x] 5.2 Implement exponential backoff (1s → 2s → 4s → 8s → 16s) with max 5 retries
- [x] 5.3 On successful reconnect, fetch `GET /api/jobs/{id}` to recover missed state
- [x] 5.4 If REST shows job complete on reconnect, set complete state without waiting for WS event
