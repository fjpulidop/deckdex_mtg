# Tasks: websocket-reconnection-polish

All changes are frontend-only. No backend, migration, or core changes required.

---

## Task 1: Extend MockWebSocket in test file to track all instances

**File:** `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Description:**
The current `MockWebSocket` mock tracks only `static lastInstance`. To test reconnection scenarios, tests must be able to drive both the first and second WebSocket instances independently.

Add `static instances: MockWebSocket[] = []` to `MockWebSocket`. In the constructor, push `this` to `instances`. In `beforeEach`, reset both `MockWebSocket.lastInstance = null` and `MockWebSocket.instances = []`.

**Acceptance criteria:**
- `MockWebSocket.instances` is an empty array at the start of each test.
- After a hook creates two WebSocket connections, `MockWebSocket.instances.length === 2`.
- `MockWebSocket.lastInstance` still refers to the most recently created instance (existing tests continue to pass).
- All 5 existing tests still pass after this change.

**Dependencies:** None (pure test infrastructure change).

---

## Task 2: Add `retryAttempt` reactive state to `useWebSocket`

**File:** `frontend/src/hooks/useApi.ts`

**Description:**
Add a new piece of React state to the `useWebSocket` hook that tracks the current reconnection attempt number.

Inside `useWebSocket`, add:
```ts
const [retryAttempt, setRetryAttempt] = React.useState(0);
```

Inside the `useEffect`:
- When the effect resets state for a new job (the block starting at line 183), also call `setRetryAttempt(0)`.

Update the return value from:
```ts
return { status, progress, errors, complete, summary };
```
to:
```ts
return { status, progress, errors, complete, summary, retryAttempt };
```

**Acceptance criteria:**
- The hook's TypeScript return type includes `retryAttempt: number`.
- `retryAttempt` is `0` on initial render with any `jobId`.
- TypeScript strict mode passes with no `any` violations.
- Existing callers that destructure `{ status, progress, errors, complete, summary }` continue to compile without changes (adding a field to the return does not break existing destructuring).

**Dependencies:** None (additive change).

---

## Task 3: Fix REST fallback — fire only on reconnect, not on initial connect

**File:** `frontend/src/hooks/useApi.ts`

**Description:**
The current `connect()` function calls `fetchRestState()` at its top, before the WebSocket opens. This fires on initial connection and on every retry, causing a redundant REST call and potential state flicker on initial load (the server already delivers current progress in the `connected` ack).

**Changes:**

1. Add a `hasConnectedOnce` flag in the `useEffect` closure (before the `connect` function definition):
   ```ts
   let hasConnectedOnce = false;
   ```

2. Remove the `fetchRestState()` call from the top of the `connect()` function.

3. Inside `ws.onopen`, check `hasConnectedOnce` and call `fetchRestState()` only on reconnect:
   ```ts
   ws.onopen = () => {
     if (cancelled) { ws.close(); return; }
     if (hasConnectedOnce) {
       fetchRestState();
     }
     hasConnectedOnce = true;
     setStatus('connected');
     retryCount = 0;
   };
   ```

**Acceptance criteria:**
- `api.getJobStatus` is NOT called after the initial `ws.onopen` fires.
- `api.getJobStatus` IS called exactly once after a drop-and-reconnect (first `onclose` with non-1000 code → retry → second `onopen`).
- If the job reconnects multiple times, `api.getJobStatus` is called once per successful reconnect.
- Existing tests for progress/complete message handling still pass.

**Dependencies:** Task 2 (to ensure `setRetryAttempt` is available).

---

## Task 4: Update `retryAttempt` state in `ws.onclose` and `ws.onopen`

**File:** `frontend/src/hooks/useApi.ts`

**Description:**
Wire up `setRetryAttempt` into the reconnection lifecycle so it reflects the current attempt number reactively.

**Changes:**

In `ws.onclose`, after incrementing `retryCount`, call `setRetryAttempt(retryCount)`:
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

In `ws.onopen` (within the same block from Task 3), reset `retryAttempt` on successful connect:
```ts
ws.onopen = () => {
  if (cancelled) { ws.close(); return; }
  if (hasConnectedOnce) {
    fetchRestState();
  }
  hasConnectedOnce = true;
  setStatus('connected');
  setRetryAttempt(0);
  retryCount = 0;
};
```

**Acceptance criteria:**
- After first unexpected close: `retryAttempt === 1`.
- After second unexpected close: `retryAttempt === 2`.
- After successful reconnect: `retryAttempt === 0`.
- After all 5 retries fail: `retryAttempt === 5` and `status === 'disconnected'`.

**Dependencies:** Tasks 2 and 3.

---

## Task 5: Add test — clean close (code 1000) does not reconnect

**File:** `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Description:**
Verify that a close event with code 1000 (normal closure, e.g., after a `complete` event) does not schedule a reconnection attempt.

Add to the `describe('useWebSocket')` block:
```ts
it('does not reconnect on clean close (code 1000)', async () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useWebSocket('job-123'));

  act(() => { MockWebSocket.lastInstance!.onopen!(new Event('open')); });
  act(() => { MockWebSocket.lastInstance!.onclose!(new CloseEvent('close', { code: 1000 })); });

  act(() => { vi.advanceTimersByTime(30000); });

  expect(MockWebSocket.instances).toHaveLength(1);
  expect(result.current.status).toBe('disconnected');
  vi.useRealTimers();
});
```

**Acceptance criteria:**
- Only one WebSocket instance is ever created during this test.
- Status is `'disconnected'` after the clean close.
- Timer advancement does not trigger a new connection.

**Dependencies:** Task 1.

---

## Task 6: Add test — exponential backoff schedule (1s → 2s)

**File:** `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Description:**
Verify the timing of the first two reconnection delays.

```ts
it('reconnects after 1s on first unexpected close', async () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useWebSocket('job-123'));

  act(() => { MockWebSocket.instances[0].onopen!(new Event('open')); });
  act(() => { MockWebSocket.instances[0].onclose!(new CloseEvent('close', { code: 1006 })); });

  expect(MockWebSocket.instances).toHaveLength(1);
  act(() => { vi.advanceTimersByTime(999); });
  expect(MockWebSocket.instances).toHaveLength(1);
  act(() => { vi.advanceTimersByTime(1); });
  expect(MockWebSocket.instances).toHaveLength(2);

  vi.useRealTimers();
});

it('second reconnect waits 2s after first retry fails', async () => {
  vi.useFakeTimers();
  renderHook(() => useWebSocket('job-123'));

  // First connect + close
  act(() => { MockWebSocket.instances[0].onopen!(new Event('open')); });
  act(() => { MockWebSocket.instances[0].onclose!(new CloseEvent('close', { code: 1006 })); });
  act(() => { vi.advanceTimersByTime(1000); }); // triggers 2nd instance

  // Second connect + close
  act(() => { MockWebSocket.instances[1].onclose!(new CloseEvent('close', { code: 1006 })); });

  expect(MockWebSocket.instances).toHaveLength(2);
  act(() => { vi.advanceTimersByTime(1999); });
  expect(MockWebSocket.instances).toHaveLength(2);
  act(() => { vi.advanceTimersByTime(1); });
  expect(MockWebSocket.instances).toHaveLength(3);

  vi.useRealTimers();
});
```

**Acceptance criteria:**
- First retry fires exactly at the 1000ms mark.
- Second retry fires exactly at the 2000ms mark after the second close.

**Dependencies:** Task 1.

---

## Task 7: Add test — max retries exhausted

**File:** `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Description:**
Verify that after 5 failed reconnection attempts the hook stops reconnecting and leaves status as `'disconnected'`.

```ts
it('stops reconnecting after 5 attempts and sets status disconnected', async () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useWebSocket('job-123'));

  // Initial connect + close
  act(() => { MockWebSocket.instances[0].onopen!(new Event('open')); });
  act(() => { MockWebSocket.instances[0].onclose!(new CloseEvent('close', { code: 1006 })); });

  // Drive through 5 retry attempts (each fails without opening)
  const delays = [1000, 2000, 4000, 8000, 16000];
  for (let i = 0; i < 5; i++) {
    act(() => { vi.advanceTimersByTime(delays[i]); }); // triggers instance i+1
    act(() => { MockWebSocket.instances[i + 1].onclose!(new CloseEvent('close', { code: 1006 })); });
  }

  // Should have: 1 original + 5 retries = 6 instances total
  expect(MockWebSocket.instances).toHaveLength(6);

  // No 7th instance after advancing timers further
  act(() => { vi.advanceTimersByTime(60000); });
  expect(MockWebSocket.instances).toHaveLength(6);
  expect(result.current.status).toBe('disconnected');

  vi.useRealTimers();
});
```

**Acceptance criteria:**
- Exactly 6 WebSocket instances created (1 initial + 5 retries).
- No further instances created after max retries.
- Final `status` is `'disconnected'`.
- `retryAttempt` equals `5` after the last failure.

**Dependencies:** Tasks 1, 4.

---

## Task 8: Add test — REST fallback fires on reconnect, not on initial connect

**File:** `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Description:**
Verify the corrected REST fallback timing. `api.getJobStatus` mock must be changed from a never-resolving promise to a resolving mock for this test.

Note: the existing module-level mock (`vi.mock('../../api/client', ...)`) uses a never-resolving promise. This test needs a resolving mock. Use `vi.mocked(api.getJobStatus).mockResolvedValueOnce(...)` inside the test after importing `api` to override for this test only.

```ts
it('fetches REST state on reconnect but not on initial connect', async () => {
  vi.useFakeTimers();
  const { api: mockApi } = await import('../../api/client');
  vi.mocked(mockApi.getJobStatus).mockResolvedValue({
    job_id: 'job-123',
    status: 'running',
    progress: { current: 5, total: 10, percentage: 50 },
    start_time: '',
    job_type: 'process',
  });

  renderHook(() => useWebSocket('job-123'));

  // Initial connect — getJobStatus should NOT be called
  act(() => { MockWebSocket.instances[0].onopen!(new Event('open')); });
  expect(mockApi.getJobStatus).not.toHaveBeenCalled();

  // Drop the connection
  act(() => { MockWebSocket.instances[0].onclose!(new CloseEvent('close', { code: 1006 })); });
  act(() => { vi.advanceTimersByTime(1000); });

  // Reconnect — getJobStatus SHOULD be called
  act(() => { MockWebSocket.instances[1].onopen!(new Event('open')); });
  expect(mockApi.getJobStatus).toHaveBeenCalledTimes(1);
  expect(mockApi.getJobStatus).toHaveBeenCalledWith('job-123');

  vi.useRealTimers();
});
```

**Acceptance criteria:**
- `api.getJobStatus` is not called after the initial `onopen`.
- `api.getJobStatus` is called exactly once after the second `onopen` (the reconnect).

**Dependencies:** Tasks 1, 3.

---

## Task 9: Add test — job completed during disconnection reconciles via REST

**File:** `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Description:**
Verify that if the job finishes while the client is disconnected, the REST response on reconnect causes the hook to set `complete=true` and `summary` without waiting for a WebSocket `complete` event.

```ts
it('sets complete from REST response when job finished during disconnection', async () => {
  vi.useFakeTimers();
  const { api: mockApi } = await import('../../api/client');
  vi.mocked(mockApi.getJobStatus).mockResolvedValue({
    job_id: 'job-123',
    status: 'complete',
    progress: { current: 10, total: 10, percentage: 100, summary: { processed: 10 } },
    start_time: '',
    job_type: 'process',
  });

  const { result } = renderHook(() => useWebSocket('job-123'));

  act(() => { MockWebSocket.instances[0].onopen!(new Event('open')); });
  act(() => { MockWebSocket.instances[0].onclose!(new CloseEvent('close', { code: 1006 })); });
  act(() => { vi.advanceTimersByTime(1000); });

  // Reconnect fires — REST call returns complete status
  await act(async () => {
    MockWebSocket.instances[1].onopen!(new Event('open'));
    // Flush the promise from fetchRestState
    await Promise.resolve();
  });

  expect(result.current.complete).toBe(true);
  expect(result.current.status).toBe('disconnected');

  vi.useRealTimers();
});
```

**Acceptance criteria:**
- `complete === true` after the REST response resolves with `status: 'complete'`.
- `status === 'disconnected'` (hook tears down because job is done).
- No WebSocket `complete` event is needed.

**Dependencies:** Tasks 1, 3.

---

## Task 10: Add test — `retryAttempt` increments and resets

**File:** `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Description:**
Verify the `retryAttempt` reactive state behavior.

```ts
it('retryAttempt increments on each retry and resets on success', async () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useWebSocket('job-123'));

  expect(result.current.retryAttempt).toBe(0);

  // First close
  act(() => { MockWebSocket.instances[0].onopen!(new Event('open')); });
  act(() => { MockWebSocket.instances[0].onclose!(new CloseEvent('close', { code: 1006 })); });
  expect(result.current.retryAttempt).toBe(1);

  // Advance to trigger reconnect
  act(() => { vi.advanceTimersByTime(1000); });

  // Second close
  act(() => { MockWebSocket.instances[1].onclose!(new CloseEvent('close', { code: 1006 })); });
  expect(result.current.retryAttempt).toBe(2);

  // Advance to trigger second reconnect, then succeed
  act(() => { vi.advanceTimersByTime(2000); });
  act(() => { MockWebSocket.instances[2].onopen!(new Event('open')); });
  expect(result.current.retryAttempt).toBe(0);

  vi.useRealTimers();
});
```

**Acceptance criteria:**
- `retryAttempt` is `0` before any close events.
- `retryAttempt` is `1` after the first unexpected close.
- `retryAttempt` is `2` after the second consecutive close.
- `retryAttempt` resets to `0` when a reconnect succeeds.

**Dependencies:** Tasks 1, 4.

---

## Task 11: Run full test suite and verify no regressions

**Description:**
After all code and test changes are applied, run the frontend test suite to confirm:
1. All 5 original `useWebSocket` tests still pass.
2. All 7 new `useWebSocket` tests pass.
3. No other tests in the suite are broken.

```bash
cd /path/to/repo
npm --prefix frontend run test -- --reporter=verbose
```

If `vi.useFakeTimers()` and `vi.useRealTimers()` inside individual tests cause timer leakage between tests, move timer setup/teardown to `beforeEach`/`afterEach` at the describe level for the reconnection tests.

**Acceptance criteria:**
- All tests pass with exit code 0.
- No new TypeScript errors (`npm --prefix frontend run build` passes).
- The `retryAttempt` field is present in the hook return type and TypeScript does not report errors on callers.

**Dependencies:** Tasks 1–10.
