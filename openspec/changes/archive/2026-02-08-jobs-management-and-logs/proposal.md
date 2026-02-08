## Why

When background jobs (Process Cards, Update Prices) are running, the fixed bottom jobs bar overlaps the card table and pagination controls. Users cannot scroll to see the end of the table or use the pagination without the bar covering them. In addition, there is no way to open a dedicated view to see job progress and log output; users only see the compact bar.

## What Changes

- **Layout**: When one or more jobs are active, the main content area (stats, filters, card table, and pagination) SHALL adjust so that the jobs bar never covers it. The user SHALL always be able to see the bottom of the table and the pagination controls (e.g. via reserved space or scrollable region).
- **Job log modal**: Each job in the bottom bar SHALL have a control (e.g. "View log" or "View progress") that opens a modal (or slide-out) showing that job’s progress and log output. The modal SHALL show live progress and log content for the selected job.

## Capabilities

### New Capabilities
<!-- None - all changes are within existing web dashboard UI -->

### Modified Capabilities
- `web-dashboard-ui`: Layout must reserve space (or otherwise adjust) when the jobs bar is visible so the table and pagination are never covered; each job entry must expose a way to open a modal (or equivalent) to view that job’s progress and log.

## Impact

- **Frontend**: `frontend/src/pages/Dashboard.tsx` (layout / padding or flex when jobs exist), `frontend/src/components/ActiveJobs.tsx` (per-job "view log" control, modal or panel for progress + log). Possibly a new component for the job log modal.
- **Backend**: Only if log/progress is not already exposed (e.g. WebSocket or GET /api/jobs/{id}); current design assumes existing job progress and error data can be reused for the modal.
