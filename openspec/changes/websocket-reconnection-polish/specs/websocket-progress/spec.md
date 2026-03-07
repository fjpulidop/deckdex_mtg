# Delta Spec: websocket-progress — Reconnection Polish

This file documents requirement changes relative to the base spec at `openspec/specs/websocket-progress/spec.md`. All requirements in the base spec remain in effect unless explicitly superseded below.

---

## Changed Requirement: REST fallback timing on reconnect

**Supersedes:** The base spec states "On each reconnect, the hook SHALL fetch the current job state via `GET /api/jobs/{id}` to recover any missed events."

**Clarification:** The REST fetch SHALL fire inside `ws.onopen` only when this is a reconnection (a prior connection was established and then dropped). It SHALL NOT fire on the initial connection attempt. The server already delivers the current progress snapshot in the `connected` acknowledgment event and a follow-up `progress` event on connect (backend behavior defined in base spec), making an initial REST call redundant and a source of state flicker.

**Updated scenario: WebSocket drops mid-job**
- WHEN the WebSocket connection closes with a non-1000 code while a job is still running
- AND the hook has previously successfully opened this connection (i.e., `onopen` has fired at least once)
- THEN the hook SHALL wait the appropriate backoff delay and attempt to reconnect
- AND on successful reconnect (`onopen` fires), the hook SHALL call `GET /api/jobs/{id}` to recover state missed during the outage
- AND if the REST response shows the job as `complete`, `error`, or `cancelled`, the hook SHALL set `complete=true` and `summary` from the response without waiting for a WebSocket `complete` event

---

## New Requirement: `retryAttempt` in hook return value

The `useWebSocket` hook SHALL expose a `retryAttempt: number` field in its return value.

- `retryAttempt` SHALL be `0` when the connection is idle, connected, or has never retried.
- `retryAttempt` SHALL be incremented to reflect the current retry attempt number when a reconnection is scheduled (e.g., `1` after the first unexpected close, `2` after the second, etc.).
- `retryAttempt` SHALL reset to `0` when a connection opens successfully.

**Scenario: Retry count is observable**
- WHEN the connection has dropped and the hook is on its second retry attempt
- THEN `retryAttempt` SHALL equal `2`

**Scenario: Retry count resets on success**
- WHEN a reconnection attempt succeeds
- THEN `retryAttempt` SHALL equal `0`

---

## Unchanged Requirements (confirmed)

The following requirements from the base spec are confirmed correct and unchanged:

- Exponential backoff: 1s, 2s, 4s, 8s, 16s (max), at most 5 attempts.
- Clean close (code 1000) SHALL NOT trigger reconnection.
- After 5 failed attempts, `status` SHALL be `disconnected` and no further reconnection SHALL be attempted.
- Job completed during disconnection: if REST response shows job as `complete`, set `complete=true` and `summary` from REST response.
