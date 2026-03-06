## Why

Jobs disappear from the UI when the user refreshes the browser. The root cause is a combination of aggressive in-memory cleanup on the backend (only 10 completed results kept), the REST endpoint not returning completed jobs from Postgres, and the frontend only restoring running/pending jobs on mount. This makes job tracking unreliable — users lose visibility of recently completed imports and price updates.

## What Changes

- Backend: Replace the hard limit of 10 in `_job_results` with a TTL-based cleanup (1 hour)
- Backend: `GET /api/jobs` returns recently completed jobs from Postgres (not just running/pending)
- Frontend: `ActiveJobsContext` restores completed jobs on mount (not just active ones) and shows them briefly before auto-removing
- Frontend: Add WebSocket reconnection with exponential backoff in `useWebSocket`
- Frontend: Add periodic job list polling as a fallback when WebSocket is unavailable

## Non-goals

- Persisting full job progress history to Postgres (only final results are persisted today, that's fine)
- Changing the WebSocket protocol or event format
- Adding a dedicated job history page (existing history tab in JobsBottomBar is sufficient)

## Capabilities

### New Capabilities

_(none — this is a bug fix across existing capabilities)_

### Modified Capabilities

- `web-api-backend`: `GET /api/jobs` must include recently completed jobs from DB; in-memory cleanup uses TTL instead of hard cap
- `global-jobs-ui`: Restore completed jobs on mount; auto-remove after display; re-fetch on window focus
- `websocket-progress`: Add client-side reconnection with exponential backoff

## Impact

- **Backend**: `backend/api/routes/process.py` — cleanup logic and `GET /api/jobs` response
- **Frontend**: `frontend/src/contexts/ActiveJobsContext.tsx` — restore logic and polling
- **Frontend**: `frontend/src/hooks/useApi.ts` — WebSocket reconnection
- **No breaking changes** — all changes are backward-compatible
