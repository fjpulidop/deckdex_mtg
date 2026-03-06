## MODIFIED Requirements

### Requirement: In-memory job cleanup uses TTL

The backend SHALL use a time-based TTL of 1 hour for cleaning up completed job results in `_job_results`, instead of a hard cap of 10 entries. Each entry in `_job_results` SHALL store the completion timestamp alongside the result. `_cleanup_old_jobs()` SHALL remove entries older than 1 hour and SHALL continue removing completed services from `_active_jobs`.

#### Scenario: Job result retained within TTL
- **WHEN** a job completes and `_cleanup_old_jobs()` runs 30 minutes later
- **THEN** the job result SHALL still be present in `_job_results`

#### Scenario: Job result evicted after TTL
- **WHEN** a job completed more than 1 hour ago and `_cleanup_old_jobs()` runs
- **THEN** the job result SHALL be removed from `_job_results` and its entry in `_job_types` SHALL also be removed

#### Scenario: Active completed jobs still cleaned from _active_jobs
- **WHEN** `_cleanup_old_jobs()` runs and `_active_jobs` contains services with status `complete`, `error`, or `cancelled`
- **THEN** those services SHALL be removed from `_active_jobs` (same behavior as before)

### Requirement: GET /api/jobs includes recently completed jobs from Postgres

The `GET /api/jobs` endpoint SHALL include jobs completed within the last 2 hours from Postgres, not just `running`/`pending` jobs. Jobs already present in the in-memory dicts SHALL NOT be duplicated.

#### Scenario: Recently completed job returned from Postgres
- **WHEN** a job completed 30 minutes ago and is no longer in `_job_results` (evicted from memory) but exists in Postgres
- **THEN** `GET /api/jobs` SHALL include that job in the response

#### Scenario: Old completed job not returned
- **WHEN** a job completed more than 2 hours ago and is not in memory
- **THEN** `GET /api/jobs` SHALL NOT include that job in the response

#### Scenario: In-memory job not duplicated
- **WHEN** a job exists in both `_job_results` and Postgres
- **THEN** `GET /api/jobs` SHALL return only the in-memory version (no duplicate)

#### Scenario: No Postgres available
- **WHEN** Postgres is not configured (Google Sheets mode)
- **THEN** `GET /api/jobs` SHALL return only in-memory jobs (existing fallback behavior unchanged)
