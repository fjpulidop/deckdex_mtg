## MODIFIED Requirements

### Requirement: Re-sync jobs on window focus

The `ActiveJobsContext` restoreJobs function must filter jobs by status when populating the active jobs list.

#### Scenario: Jobs restored on mount filter by status
- **WHEN** `ActiveJobsContext` mounts and fetches jobs from `GET /api/jobs`
- **THEN** only jobs with status `running` or `pending` are added to the active jobs list
- **AND** jobs with status `error`, `complete`, or `cancelled` are excluded

#### Scenario: User switches tabs and returns
- **WHEN** the browser tab regains focus and jobs are re-synced
- **THEN** only jobs with status `running` or `pending` are kept or added
- **AND** previously active jobs no longer on the server are removed
