# Design: WebSocket Reconnection Polish

## Context

The `useWebSocket` hook lives entirely in `frontend/src/hooks/useApi.ts` (lines 168-287). It manages a single WebSocket connection to `/ws/progress/{jobId}`, tracks progress/error/complete events, and already contains a partial reconnection implementation.

The backend WebSocket handler at `backend/api/websockets/progress.py` already supports reconnecting clients correctly: on connect it sends a `connected` ack with `job_status`, then immediately sends the current progress snapshot if the job is still running (lines 214-224). The REST endpoint `GET /api/jobs/{job_id}` at `backend/api/routes/process.py:379` returns `JobStatus` with progress data and is already typed in `frontend/src/api/client.ts` as `api.getJobStatus`.

No backend changes are required.

---

## Current Implementation Analysis

```
frontend/src/hooks/useApi.ts — useWebSocket (lines 168–287)
```

The existing code has the following structure (paraphrased):

```
connect() {
  fetchRestState()           // REST poll fires on EVERY connect attempt
  ws = new WebSocket(...)
  ws.onopen = () => { retryCount = 0 }
  ws.onclose = (e) => {
    if (e.code !== 1000 && retryCount < MAX_RETRIES) {
      delay = min(BASE_DELAY * 2^retryCount, 16000)
      retryCount++           // increments AFTER delay calc
      setTimeout(connect, delay)
    }
  }
}
```

**Issue 1 — REST fallback fires before connection is established.**
`fetchRestState()` is called at the top of `connect()`, so it fires on the initial connect and on every retry before the WebSocket opens. The spec requirement is that REST state recovery happens on reconnect (i.e., when a previously-established connection drops and the client reconnects). On the initial connect the WebSocket server sends the current snapshot in the `connected` ack and a follow-up `progress` event, so the REST call is redundant and can cause a state flicker (REST response arriving after a WebSocket `progress` event).

**Issue 2 — `retryAttempt` not exposed.**
Callers have no way to display "Reconnecting (attempt 2 of 5)..." messaging. The hook returns `{ status, progress, errors, complete, summary }` but nothing about reconnection state.

**Issue 3 — Test coverage gaps.**
`frontend/src/hooks/__tests__/useWebSocket.test.ts` has 5 tests covering only: null jobId, initial connecting state, onopen fires, progress message, complete message, onclose fires. Missing: backoff timing, max-retry exhaustion, REST fallback on reconnect, completed-job reconciliation via REST, clean-close suppression.

---

## Design Decisions

### Decision 1: When to call `fetchRestState`

The REST fallback must only fire after a reconnect (a drop followed by a successful re-open), not on the initial connection attempt. The server already handles initial-connect state delivery via the `connected` ack and the subsequent `progress` event (backend `progress.py` lines 214-224).

Implementation: track `hasConnectedOnce: boolean` (a `let` in the closure). In `ws.onopen`, if `hasConnectedOnce === true` (this is a reconnect), call `fetchRestState()` then set `retryCount = 0`. On the very first open, skip `fetchRestState` and set `hasConnectedOnce = true`.

This eliminates the race condition between REST and the server's initial progress snapshot delivery.

### Decision 2: Backoff schedule correctness

The spec requires: 1s → 2s → 4s → 8s → 16s (max), with at most 5 attempts.

Current code:
```ts
const delay = Math.min(BASE_DELAY * Math.pow(2, retryCount), 16000);
retryCount++;
```

With `retryCount` starting at 0:
- Attempt 1: delay = 1000 * 2^0 = 1000ms, then retryCount = 1
- Attempt 2: delay = 1000 * 2^1 = 2000ms, then retryCount = 2
- Attempt 3: delay = 1000 * 2^2 = 4000ms, then retryCount = 3
- Attempt 4: delay = 1000 * 2^3 = 8000ms, then retryCount = 4
- Attempt 5: delay = 1000 * 2^4 = 16000ms, then retryCount = 5

This is mathematically correct per the spec. The existing backoff formula is correct and requires no change.

The guard `retryCount < MAX_RETRIES` (where MAX_RETRIES = 5) correctly allows 5 attempts before stopping. No change needed here either.

### Decision 3: Expose `retryAttempt`

Add `retryAttempt: number` to the hook's return value. This is the current `retryCount` at the moment the hook's state is read. Since `retryCount` is a closure variable (not React state), we expose it via a React ref or a separate `useState`.

Use `const [retryAttempt, setRetryAttempt] = React.useState(0)` so the value is reactive. Call `setRetryAttempt(retryCount)` when scheduling a reconnect, and `setRetryAttempt(0)` when a connection succeeds.

### Decision 4: `status` remains `'connecting'` during backoff wait

Between a close event and the next `connect()` call, `status` should clearly indicate the hook is in a reconnection cycle. Since `setStatus('connecting')` is already called at the top of `connect()`, the status is `'disconnected'` during the backoff sleep period (the `onclose` handler sets it to `'disconnected'`).

This is acceptable behavior — `disconnected` during the delay window is accurate. When `connect()` fires again it sets `connecting` immediately. No change required.

### Decision 5: Test strategy for timing-sensitive code

Tests use `vi.useFakeTimers()` to control `setTimeout`. The existing `MockWebSocket` pattern (a class with `static lastInstance` for test control) is already established and will be extended to track multiple instances during reconnection tests.

For reconnection tests that need a "second" WebSocket instance, the mock needs `static instances: MockWebSocket[]` in addition to `static lastInstance` so tests can drive the second connection independently.

---

## Detailed Implementation Plan

### File: `frontend/src/hooks/useApi.ts`

Changes confined to the `useWebSocket` function body (lines 168-287).

**Changes:**

1. Add `retryAttempt` state: `const [retryAttempt, setRetryAttempt] = React.useState(0);`

2. Add `hasConnectedOnce` flag in the `useEffect` closure: `let hasConnectedOnce = false;`

3. Move `fetchRestState()` call from the top of `connect()` to inside `ws.onopen`:
   ```ts
   ws.onopen = () => {
     if (cancelled) { ws.close(); return; }
     if (hasConnectedOnce) {
       // This is a reconnect — recover any state missed during outage
       fetchRestState();
     }
     hasConnectedOnce = true;
     setStatus('connected');
     setRetryAttempt(0);
     retryCount = 0;
   };
   ```

4. In `ws.onclose`, update `setRetryAttempt` when scheduling retry:
   ```ts
   ws.onclose = (event) => {
     if (cancelled) return;
     setStatus('disconnected');
     if (event.code !== 1000 && retryCount < MAX_RETRIES) {
       const delay = Math.min(BASE_DELAY * Math.pow(2, retryCount), 16000);
       retryCount++;
       setRetryAttempt(retryCount);
       retryTimer = setTimeout(connect, delay);
     }
   };
   ```

5. Update the return value: `return { status, progress, errors, complete, summary, retryAttempt };`

6. Remove the stale `fetchRestState()` call from the top of `connect()`.

### File: `frontend/src/hooks/__tests__/useWebSocket.test.ts`

Extend the existing test file. The `MockWebSocket` class needs:
- `static instances: MockWebSocket[] = []` reset in `beforeEach`
- Constructor pushes to `instances`

New test cases (all using `vi.useFakeTimers()` + `vi.useRealTimers()` in afterEach):

1. **Clean close (code 1000) does not reconnect**: Fire `onclose` with code 1000, advance timers, assert only one WebSocket was created.

2. **Unexpected close schedules reconnect after 1s**: Fire `onclose` with code 1006, advance 999ms — no new instance. Advance 1ms more — second instance created.

3. **Exponential backoff: second failure delays 2s**: First close → 1s → reconnect → second close → 2s → third instance.

4. **Max retries exhausted — status becomes disconnected and no more instances**: Simulate 5 consecutive failures. After the 5th close, advance all timers. Assert no 6th instance was created and `status === 'disconnected'`.

5. **`retryAttempt` increments on each retry**: After first close, `retryAttempt` is 1. After second retry close, `retryAttempt` is 2. After successful reconnect, `retryAttempt` resets to 0.

6. **REST fallback fires on reconnect but not on initial connect**: `api.getJobStatus` mock starts resolving. Assert it is NOT called after initial `onopen`. Simulate close + reconnect + second `onopen`. Assert `api.getJobStatus` IS called once.

7. **Job completed during disconnection — REST response sets complete**: `api.getJobStatus` resolves with `status: 'complete'`. After reconnect's `onopen`, assert `complete === true` and `status === 'disconnected'`.

---

## Affected Files Summary

| File | Change Type | Scope |
|------|-------------|-------|
| `frontend/src/hooks/useApi.ts` | Modify | `useWebSocket` function only |
| `frontend/src/hooks/__tests__/useWebSocket.test.ts` | Modify | Add 7 new test cases, extend MockWebSocket |
| `openspec/changes/websocket-reconnection-polish/specs/websocket-progress/spec.md` | New (delta) | Hook return contract + REST fallback timing |

---

## Risks and Edge Cases

**Race condition: REST response arrives after WebSocket `progress` event on reconnect.**
When `fetchRestState()` fires on reconnect and the server also sends a `progress` event shortly after the `connected` ack, the REST response may arrive later and overwrite the WebSocket's fresher data. Mitigation: `fetchRestState` only sets progress if there is no more recent data (current implementation uses the REST response for progress state; since the server's `connected` ack snapshot and the REST response come from the same in-memory `service.progress_data`, they will be consistent). This is acceptable for the polling use case — if the job is still running, subsequent WebSocket `progress` events will overwrite the REST data within seconds.

**`cancelled` flag and async REST call.**
If the hook unmounts while `fetchRestState` is in flight, the `if (cancelled) return` guard inside the `.then()` callback prevents stale state updates. This guard already exists in the current code (line 200 of `useApi.ts`).

**`retryAttempt` is reactive state — causes an extra render.**
Setting `retryAttempt` via `useState` triggers a re-render. This is intentional — callers need a reactive value to display reconnection UI. The render is small and infrequent (at most 5 times per job).
