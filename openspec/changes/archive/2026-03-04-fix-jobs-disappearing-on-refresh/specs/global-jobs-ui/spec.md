## MODIFIED Requirements

### Requirement: Job restore includes completed jobs

On app mount, `ActiveJobsProvider` SHALL restore all jobs returned by `GET /api/jobs` — including `complete`, `error`, and `cancelled` jobs — not just `running`/`pending`. Completed/error/cancelled jobs SHALL be added to the jobs list so the `JobsBottomBar` can display and auto-dismiss them using its existing ~5s auto-remove timer.

#### Scenario: Running job restored on refresh
- **WHEN** a user refreshes the page and a job is still `running`
- **THEN** the job SHALL appear in the jobs bar with live progress tracking via WebSocket

#### Scenario: Completed job restored on refresh
- **WHEN** a user refreshes the page and a job completed within the last 2 hours
- **THEN** the job SHALL briefly appear in the jobs bar as completed and be auto-dismissed after ~5 seconds

#### Scenario: Error job restored on refresh
- **WHEN** a user refreshes the page and a job errored within the last 2 hours
- **THEN** the job SHALL briefly appear in the jobs bar with error status and be auto-dismissed after ~5 seconds

## ADDED Requirements

### Requirement: Re-sync jobs on window focus

`ActiveJobsProvider` SHALL re-fetch `GET /api/jobs` when the browser tab regains visibility (using the `visibilitychange` event). The re-fetch SHALL be debounced so that rapid focus/blur cycles do not trigger multiple requests. Newly discovered running jobs SHALL be added; jobs no longer in the backend response SHALL be removed.

#### Scenario: User switches tabs and returns
- **WHEN** the user switches to another tab for 2 minutes and returns
- **THEN** `ActiveJobsProvider` SHALL call `GET /api/jobs` and reconcile the local job list with the response

#### Scenario: Rapid tab switching
- **WHEN** the user switches tabs back and forth rapidly (within 2 seconds)
- **THEN** `ActiveJobsProvider` SHALL debounce and make at most one `GET /api/jobs` call
