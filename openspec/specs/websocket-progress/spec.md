# WebSocket Progress

Real-time progress for jobs. **Endpoint:** /ws/progress/{job_id}. Valid job_id required; invalid → close 4004 "Job not found". Multiple clients per job; broadcast to all.

**Authentication:** WebSocket connections SHALL be authenticated via the `access_token` HTTP-only cookie (same JWT used by REST endpoints). The server reads `websocket.cookies.get("access_token")` on connect; if missing or invalid, closes with code 4001 "Authentication required". Query parameter tokens are NOT supported (prevents token leakage in server logs and browser history).

**Events (JSON):** type (progress|error|complete), timestamp ISO8601. Progress: current, total, percentage, batch_size, elapsed_seconds, estimated_remaining_seconds. Error: card_name, error_type, message; connection stays open; cap individual errors (e.g. 100) then summary. Complete: status (success|cancelled), total_processed, success_count, error_count, duration_seconds; then close 1000. **Lifecycle:** Client disconnect → process continues. Server error → error event, close 1011. Ping every 30s if idle. Cleanup job state 5 min after all disconnect + complete. **On connect:** If job running and progress>0, send current progress after "connected" ack. If job complete/error, send complete event from _job_results. "connected" includes job_status. New job (total 0) → ack only. Integrate with ProcessorService callback; queue events for async loop from thread. Isolate state per job_id. Log connect/disconnect at INFO; errors at ERROR.

### Requirement: Job validation on WebSocket connect

The WebSocket endpoint `/ws/progress/{job_id}` SHALL validate that the requested `job_id` exists before accepting the connection. If the job is not found, the server SHALL close the connection with code 4004 and reason "Job not found".

#### Scenario: Valid in-memory job connects
- **WHEN** a client connects to `/ws/progress/{job_id}` and the job exists in `_active_jobs` or `_job_results`
- **THEN** the server SHALL accept the connection and send a `connected` acknowledgment event

#### Scenario: Unknown job is rejected
- **WHEN** a client connects to `/ws/progress/{job_id}` and the job does not exist
- **THEN** the server SHALL close the connection with code 4004 and reason "Job not found"

### Requirement: Client-side WebSocket reconnection with exponential backoff

The `useWebSocket` hook SHALL automatically reconnect when the WebSocket connection closes unexpectedly (close code other than 1000 normal closure). Reconnection SHALL use exponential backoff starting at 1 second, doubling each attempt up to a maximum interval of 16 seconds. The hook SHALL attempt at most 5 reconnections before giving up. On each reconnect, the hook SHALL fetch the current job state via `GET /api/jobs/{id}` to recover any missed events.

#### Scenario: WebSocket drops mid-job
- **WHEN** the WebSocket connection closes with a non-1000 code while a job is still running
- **THEN** the hook SHALL wait 1 second and attempt to reconnect, fetching current state via REST on success

#### Scenario: Exponential backoff on repeated failures
- **WHEN** reconnection fails 3 times in a row
- **THEN** the 4th attempt SHALL wait at least 8 seconds before trying again

#### Scenario: Max retries exhausted
- **WHEN** 5 reconnection attempts have all failed
- **THEN** the hook SHALL stop reconnecting and set connection status to `disconnected`

#### Scenario: Job completed during disconnection
- **WHEN** the WebSocket reconnects and the REST fallback shows the job as `complete`
- **THEN** the hook SHALL set `complete=true` and `summary` from the REST response without waiting for a WebSocket `complete` event

#### Scenario: Clean close does not trigger reconnection
- **WHEN** the WebSocket closes with code 1000 (normal closure, e.g., after a `complete` event)
- **THEN** the hook SHALL NOT attempt to reconnect
