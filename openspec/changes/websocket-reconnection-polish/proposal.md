## Why

When a background job is running and the user's browser tab loses its WebSocket connection (network hiccup, browser suspending inactive tabs, server restart, flaky Wi-Fi), the progress UI freezes and shows no indication of what happened. The job continues processing on the server, but the user sees a stale progress bar with no feedback.

Currently the `useWebSocket` hook in `frontend/src/hooks/useApi.ts` has a partial reconnection implementation: it schedules reconnect attempts with exponential backoff and calls `api.getJobStatus` as a REST fallback on every connect attempt. However, the implementation has correctness gaps and the test suite does not verify the reconnection scenarios defined in `openspec/specs/websocket-progress/spec.md`.

This change polishes the reconnection behavior to fully satisfy the spec, fixes the correctness issues in the existing implementation, and adds test coverage for all reconnection scenarios.

## What Changes

- **Fix reconnection logic in `useWebSocket`**: The REST fallback (`fetchRestState`) currently fires on every connection attempt including retries, before the WebSocket connects. The spec requires it fires on reconnect (after a successful re-connection) to reconcile state missed during the outage. We also add an explicit `retryCount` tracking detail to the `ws.onclose` log for observability, and add a `retryAttempt` field to the hook's return value so UI can display "reconnecting..." messaging.
- **Add missing test scenarios**: The existing test file (`frontend/src/hooks/__tests__/useWebSocket.test.ts`) covers happy path only. New tests cover: exponential backoff delay calculation, max retries exhaustion setting status to `disconnected`, REST fallback triggered on reconnect, job-complete-during-disconnect reconciliation, and clean-close (code 1000) suppressing reconnection.
- **Add `retryAttempt` to hook return value**: Consumers (e.g. `JobLogModal`) can display "Reconnecting (attempt 2/5)..." instead of showing a frozen progress bar.

## Capabilities

### Modified Capabilities
- `websocket-progress`: Delta spec clarifying when REST fallback fires (on successful reconnect, not on every attempt), adding `retryAttempt` to hook return contract, and confirming the 1s→2s→4s→8s→16s backoff schedule with max 5 attempts.

## Impact

- `frontend/src/hooks/useApi.ts` — fix `useWebSocket` reconnection logic
- `frontend/src/hooks/__tests__/useWebSocket.test.ts` — comprehensive reconnection test suite
- `openspec/specs/websocket-progress/spec.md` — delta spec for hook return contract and REST fallback timing

## Non-goals

- No backend changes: the server already sends current progress on reconnect (lines 214-231 of `progress.py`), no server-side work is needed.
- No changes to other hooks or components beyond `useWebSocket` and its callers reading the new `retryAttempt` field.
- No persistent job state: job state remains in-memory; this change only improves the client's ability to recover state that the server still holds.
- No UI redesign: callers may optionally display the `retryAttempt` field, but this change does not mandate UI changes.
