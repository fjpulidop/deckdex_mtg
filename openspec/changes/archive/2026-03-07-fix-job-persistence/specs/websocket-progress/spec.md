## MODIFIED Requirements

### Requirement: Job validation on WebSocket connect
The WebSocket endpoint `/ws/progress/{job_id}` SHALL validate that the requested `job_id` exists before accepting the connection. Validation SHALL check in-memory state first (active jobs dict, completed results dict), then fall back to `JobRepository.get_job()` when Postgres is configured. If the job is not found in any source, the server SHALL close the connection with code 4004 and reason "Job not found". If `JobRepository` is not configured (Google Sheets mode), the in-memory check is the only check.

#### Scenario: Valid in-memory job connects
- **WHEN** a client connects to `/ws/progress/{job_id}` and the job exists in `_active_jobs` or `_job_results`
- **THEN** the server SHALL accept the connection and send a `connected` acknowledgment event

#### Scenario: Valid DB-only job connects after restart
- **WHEN** a client connects to `/ws/progress/{job_id}` and the job is not in memory but exists in the Postgres `jobs` table
- **THEN** the server SHALL accept the connection and send a `connected` acknowledgment with the persisted job status

#### Scenario: Unknown job is rejected
- **WHEN** a client connects to `/ws/progress/{job_id}` and the job does not exist in memory or Postgres
- **THEN** the server SHALL close the connection with code 4004 and reason "Job not found"

#### Scenario: No Postgres configured — in-memory check only
- **WHEN** `JobRepository` is not configured (Google Sheets mode) and `job_id` is not in memory
- **THEN** the server SHALL close the connection with code 4004 (no DB fallback attempted)
