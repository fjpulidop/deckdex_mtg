## ADDED Requirements

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
