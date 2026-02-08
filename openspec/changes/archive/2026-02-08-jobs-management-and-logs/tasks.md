## 1. Layout: reserve space for jobs bar

- [x] 1.1 Add bottom padding (or equivalent) to the main dashboard content container when `backgroundJobs.length > 0` so the jobs bar does not cover the table or pagination (e.g. padding-bottom based on estimated or measured bar height)
- [x] 1.2 Ensure the card table and pagination controls remain visible when the user scrolls to the bottom with one or more jobs active; verify with 1 job and with 2+ jobs

## 2. Job log modal

- [x] 2.1 Add a "View log" (or "View progress") control to each job entry in `ActiveJobs` that opens a modal for that job
- [x] 2.2 Implement a modal (or slide-over) component that displays the selected job's progress (percentage, current/total, elapsed), status, and log/errors using existing WebSocket or job state
- [x] 2.3 Ensure the modal updates in real time while the job is running and can be closed without affecting the job; keep the modal keyed by jobId so switching between jobs (if supported) shows the correct content
