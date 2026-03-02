## MODIFIED Requirements

### Requirement: Restore active jobs on mount
On app (or global provider) mount, GET /api/jobs once; populate global list with active/pending jobs. Not route-specific; runs regardless of initial route. On API error (including 401 Unauthorized): log the error and continue without blocking. The API client SHALL NOT redirect to `/login` if the browser is already on a public page (e.g., `/login`).

#### Scenario: Job restore on authenticated route
- **WHEN** `ActiveJobsProvider` mounts while the user is on an authenticated route (e.g., `/dashboard`)
- **THEN** the provider SHALL call `GET /api/jobs` and populate the jobs list with any active/pending jobs

#### Scenario: Job restore on login page
- **WHEN** `ActiveJobsProvider` mounts while the browser is on `/login`
- **THEN** the provider SHALL call `GET /api/jobs`, receive a 401, log the error, and continue without redirecting or blocking

#### Scenario: API error on mount
- **WHEN** `GET /api/jobs` returns any non-2xx response during mount
- **THEN** the provider SHALL log the error and leave the jobs list empty — it SHALL NOT throw or redirect the user
