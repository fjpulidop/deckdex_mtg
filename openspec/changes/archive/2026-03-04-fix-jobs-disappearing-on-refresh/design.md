## Context

Jobs are tracked in two places: in-memory dicts on the backend (`_active_jobs`, `_job_results`, `_job_types` in `process.py`) and React state on the frontend (`ActiveJobsContext`). Completed jobs are also persisted to Postgres via `job_repository.py`.

Current problems:
1. `_cleanup_old_jobs()` deletes all completed entries from `_active_jobs` and caps `_job_results` at 10 — too aggressive.
2. `GET /api/jobs` only recovers `running`/`pending` jobs from Postgres, ignoring recently completed ones.
3. Frontend `ActiveJobsContext` only restores `running`/`pending` jobs on mount, so completed jobs vanish on refresh.
4. `useWebSocket` has no reconnection — dropped connections mean lost progress updates.

## Goals / Non-Goals

**Goals:**
- Jobs survive browser refresh: recently completed jobs briefly visible before auto-dismiss
- In-memory cleanup is time-based (1h TTL), not count-based
- WebSocket reconnects automatically with exponential backoff
- Frontend re-syncs job list on window focus as a safety net

**Non-Goals:**
- Full job progress persistence to DB (only final results are persisted)
- Changes to WebSocket protocol or event format
- New UI for job history

## Decisions

### D1: TTL-based in-memory cleanup (backend)

**Choice:** Replace the hard cap of 10 in `_job_results` with a timestamp-based TTL of 1 hour. Store `(result, completed_at)` tuples instead of bare result dicts.

**Rationale:** A time-based approach keeps results accessible for a reasonable period without unbounded growth. 1h is generous enough for page refreshes and short sessions, but prevents memory leaks from long-running servers.

**Alternative considered:** Rely entirely on Postgres for completed results. Rejected because Google Sheets mode has no Postgres, and adding a DB read to every `GET /api/jobs/{id}` adds latency for the common case.

### D2: Include recently completed jobs in `GET /api/jobs` (backend)

**Choice:** When querying Postgres for jobs not in memory, include jobs completed within the last 2 hours (not just `running`/`pending`). This catches the case where in-memory state was cleaned up but the job is still recent.

**Rationale:** The endpoint already queries Postgres; widening the filter is minimal effort and closes the gap where a completed job isn't in memory but was recent.

### D3: Frontend restores completed jobs and auto-dismisses (frontend)

**Choice:** `ActiveJobsContext` restores all jobs from `GET /api/jobs` (not just running/pending). Completed/error/cancelled jobs are shown briefly (5s, matching existing auto-remove behavior) then removed.

**Rationale:** This ensures users see the outcome of jobs that completed while the page was refreshing. The existing auto-remove timer in `JobsBottomBar` already handles dismissal.

### D4: Window focus re-sync (frontend)

**Choice:** Add a `visibilitychange` listener in `ActiveJobsContext` that re-fetches `GET /api/jobs` when the tab regains focus. Debounced to avoid rapid re-fetches.

**Rationale:** Covers the scenario where a user switches tabs and comes back — the job list reconciles with the backend without requiring constant polling. Lightweight and no battery/network cost when tab is inactive.

**Alternative considered:** Periodic polling (every 15-30s). Rejected as too heavy for a localhost app where jobs are infrequent. Window focus is sufficient.

### D5: WebSocket reconnection with exponential backoff (frontend)

**Choice:** In `useWebSocket`, on unexpected close (not clean 1000 close), reconnect with exponential backoff: 1s → 2s → 4s → 8s → 16s max. Max 5 retries. On reconnect, fetch current state via REST `GET /api/jobs/{id}` to recover missed events.

**Rationale:** Short jobs may complete during a brief disconnection; the REST fallback on reconnect ensures the final state is captured. Max retries prevent infinite loops for genuinely dead jobs.

## Risks / Trade-offs

- **[Memory on long sessions]** TTL-based cleanup could accumulate more entries than the old cap-10 approach during burst job creation. → Mitigation: 1h TTL is short enough; a user creating >100 jobs/hour is unrealistic for this app.
- **[Race: cleanup during request]** `_cleanup_old_jobs()` modifies dicts while `list_jobs` reads them. Both run in the async event loop (single-threaded), so no actual race. No mitigation needed.
- **[Postgres unavailable]** If Postgres is down or not configured (Google Sheets mode), `GET /api/jobs` falls back to in-memory only. → Mitigation: already handled by the existing `try/except` block; behavior is unchanged for Sheets-only users.
