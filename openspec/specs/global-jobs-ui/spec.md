# Global Jobs UI

App-level job visibility: one fixed bottom bar on all main views (Dashboard, Settings). Restore once on app load.

### Requirements (compact)

- **Restore:** On app (or global provider) mount, GET /api/jobs once; populate global list with active/pending jobs. Not route-specific; runs regardless of initial route. On API error (including 401 Unauthorized): log the error and continue without blocking. The API client SHALL NOT redirect to `/login` if the browser is already on a public page (e.g., `/login`, `/`).

  - **Scenario — Job restore on authenticated route:** WHEN `ActiveJobsProvider` mounts while the user is on an authenticated route (e.g., `/dashboard`), THEN the provider SHALL call `GET /api/jobs` and populate the jobs list with any active/pending jobs.
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
