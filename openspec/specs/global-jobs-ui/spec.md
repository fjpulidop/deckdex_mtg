# Global Jobs UI

App-level job visibility: one fixed bottom bar on all main views (Dashboard, Settings). Restore once on app load.

### Requirements (compact)

- **Restore:** On app (or global provider) mount, GET /api/jobs once; populate global list with all returned jobs (including completed, error, cancelled — not just active/pending). Completed/error/cancelled jobs are shown briefly and auto-dismissed after ~5s. Not route-specific; runs regardless of initial route. On API error (including 401 Unauthorized): log the error and continue without blocking. The API client SHALL NOT redirect to `/login` if the browser is already on a public page (e.g., `/login`, `/`).

  - **Scenario — Job restore on authenticated route:** WHEN `ActiveJobsProvider` mounts while the user is on an authenticated route (e.g., `/dashboard`), THEN the provider SHALL call `GET /api/jobs` and populate the jobs list with all returned jobs.
  - **Scenario — Running job restored on refresh:** WHEN a user refreshes the page and a job is still `running`, THEN the job SHALL appear in the jobs bar with live progress tracking via WebSocket.
  - **Scenario — Completed job restored on refresh:** WHEN a user refreshes the page and a job completed within the last 2 hours, THEN the job SHALL briefly appear in the jobs bar as completed and be auto-dismissed after ~5 seconds.
  - **Scenario — Error job restored on refresh:** WHEN a user refreshes the page and a job errored within the last 2 hours, THEN the job SHALL briefly appear in the jobs bar with error status and be auto-dismissed after ~5 seconds.
  - **Scenario — Job restore on public page:** WHEN `ActiveJobsProvider` mounts while the browser is on a public page (`/login`, `/`), THEN the provider SHALL call `GET /api/jobs`, receive a 401, log the error, and continue without redirecting or blocking.
  - **Scenario — API error on mount:** WHEN `GET /api/jobs` returns any non-2xx response during mount, THEN the provider SHALL log the error and leave the jobs list empty — it SHALL NOT throw or redirect the user.
### Requirement: Jobs bar excluded from public pages
The `JobsBottomBar` component SHALL NOT render on public pages (landing `/` and login `/login`). It SHALL only render on authenticated application routes where job management is relevant.

#### Scenario: Landing page has no jobs bar
- **WHEN** a visitor navigates to the landing page (`/`)
- **THEN** the `JobsBottomBar` component is not present in the DOM

#### Scenario: Login page has no jobs bar
- **WHEN** a user navigates to the login page (`/login`)
- **THEN** the `JobsBottomBar` component is not present in the DOM

#### Scenario: Authenticated route shows jobs bar
- **WHEN** an authenticated user navigates to `/dashboard`
- **THEN** the `JobsBottomBar` component is rendered as usual

- **Bar:** Single bar at app level when jobs exist; list jobs vertically; open modal per job; auto-remove completed after ~5s; cancelled → orange + "Cancelled". Progress via WebSocket or GET /api/jobs/{id}. Same bar across navigation.
- **Layout:** Main content on all views reserves bottom space so bar doesn’t overlap (Dashboard table/pagination, Settings sections fully visible).

### Requirement: Re-sync jobs on window focus

`ActiveJobsProvider` SHALL re-fetch `GET /api/jobs` when the browser tab regains visibility (using the `visibilitychange` event). The re-fetch SHALL be debounced so that rapid focus/blur cycles do not trigger multiple requests. Newly discovered running jobs SHALL be added; jobs no longer in the backend response SHALL be removed.

#### Scenario: User switches tabs and returns
- **WHEN** the user switches to another tab for 2 minutes and returns
- **THEN** `ActiveJobsProvider` SHALL call `GET /api/jobs` and reconcile the local job list with the response

#### Scenario: Rapid tab switching
- **WHEN** the user switches tabs back and forth rapidly (within 2 seconds)
- **THEN** `ActiveJobsProvider` SHALL debounce and make at most one `GET /api/jobs` call
