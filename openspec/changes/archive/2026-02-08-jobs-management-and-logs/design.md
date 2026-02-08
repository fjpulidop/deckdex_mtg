## Context

The dashboard uses a fixed bottom bar (`ActiveJobs`) when background jobs exist. The main content lives in a single scrollable page (header, stats, action buttons, filters, card table with pagination). Because the bar is `fixed bottom-0`, it overlays the content and can hide the end of the table and pagination. Job progress is shown only in the bar (progress bar, X/Y, errors expandable); there is no full-screen or modal view for log/progress.

## Goals / Non-Goals

**Goals:**
- When the jobs bar is visible (1 to N jobs), the user can always see the end of the card table and the pagination controls without them being covered.
- Each job has a way to open a dedicated view (modal) to see that job’s progress and log.

**Non-Goals:**
- Changing how jobs are started or how the backend runs them.
- Adding new backend endpoints for logs (reuse existing WebSocket and/or GET /api/jobs/{id} if sufficient).

## Decisions

### 1. Layout: reserve space for the jobs bar

**Choice:** When `jobs.length > 0`, add bottom padding to the main content container equal to the height of the jobs bar, so the last content (table end + pagination) sits above the bar and is never covered.

**Alternatives considered:**
- **Bar in document flow:** Move the jobs bar out of `fixed` and render it below the table. Simpler but pushes the bar off-screen until the user scrolls; less visible for long-running jobs.
- **Flex layout with scrollable content:** Make the main area a flex column with `flex-1 min-h-0` and an inner scroll. More robust for complex layouts but a larger refactor.

**Rationale:** Padding is a small, localized change and achieves the requirement. Bar height can be estimated (e.g. ~N × single-row height + padding) or measured (e.g. ref + ResizeObserver) for accuracy.

### 2. Job log modal content and data

**Choice:** Reuse existing job state: WebSocket (progress, errors, summary) and any existing REST job details. The modal shows the same progress (percentage, current/total), elapsed time, errors list, and status. If the backend exposes a log stream (e.g. via WebSocket or a log endpoint), include it in the modal; otherwise the “log” is the progress and errors already available.

**Rationale:** Keeps backend scope minimal; no new API contract required unless we later add a dedicated log stream.

### 3. Modal UX

**Choice:** A single modal (or slide-over panel) opened by a “View log” (or “View progress”) control on each job row. The modal is keyed by `jobId` and shows that job’s live data. If the user opens another job’s “View log”, the modal content switches to that job (or a second modal could be allowed; single modal is simpler).

**Rationale:** Matches user request (“botón que mostrara una ventana emergente”) and keeps UI simple.

## Risks / Trade-offs

- **Estimated bar height:** If we use a fixed padding (e.g. 80px per job), it may be too small for multiple rows or long labels. Mitigation: use a conservative per-job height or measure the bar (ResizeObserver) and set padding from state.
- **Log content:** If “log” is only progress + errors, some users might expect raw backend logs. Mitigation: label the modal as “Progress & log” and document that “log” is progress and errors unless a log API is added later.
