import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '../useApi';

// ---------------------------------------------------------------------------
// Mock api.getJobStatus so the initial REST fetch doesn't throw
// ---------------------------------------------------------------------------
// Return a never-resolving promise so the async pre-fetch doesn't trigger
// state updates during tests (avoids act(...) warnings).
vi.mock('../../api/client', () => ({
  api: {
    getJobStatus: vi.fn().mockReturnValue(new Promise(() => {})),
  },
}));

// ---------------------------------------------------------------------------
// Minimal WebSocket mock
// ---------------------------------------------------------------------------
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  onopen: ((e: Event) => void) | null = null;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onclose: ((e: CloseEvent) => void) | null = null;
  onerror: ((e: Event) => void) | null = null;
  readyState = MockWebSocket.CONNECTING;

  // Track the last created instance so tests can drive it
  static lastInstance: MockWebSocket | null = null;
  // Track all instances so reconnection tests can drive each one independently
  static instances: MockWebSocket[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.lastInstance = this;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
  }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.lastInstance = null;
    MockWebSocket.instances = [];
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  // -------------------------------------------------------------------------
  // Original tests (must continue to pass)
  // -------------------------------------------------------------------------

  it('starts disconnected when jobId is null', () => {
    const { result } = renderHook(() => useWebSocket(null));
    expect(result.current.status).toBe('disconnected');
  });

  it('transitions to connecting when a jobId is provided', () => {
    const { result } = renderHook(() => useWebSocket('job-123'));
    expect(result.current.status).toBe('connecting');
  });

  it('becomes connected after onopen fires', () => {
    const { result } = renderHook(() => useWebSocket('job-123'));

    act(() => {
      MockWebSocket.lastInstance!.onopen!(new Event('open'));
    });

    expect(result.current.status).toBe('connected');
  });

  it('updates progress state on a progress message', () => {
    const { result } = renderHook(() => useWebSocket('job-123'));

    act(() => {
      const msg = new MessageEvent('message', {
        data: JSON.stringify({ type: 'progress', current: 3, total: 10, percentage: 30 }),
      });
      MockWebSocket.lastInstance!.onmessage!(msg);
    });

    expect(result.current.progress.current).toBe(3);
    expect(result.current.progress.total).toBe(10);
    expect(result.current.progress.percentage).toBe(30);
  });

  it('sets complete and summary on a complete message', () => {
    const { result } = renderHook(() => useWebSocket('job-123'));
    const summaryPayload = { processed: 5, errors: 0 };

    act(() => {
      const msg = new MessageEvent('message', {
        data: JSON.stringify({ type: 'complete', summary: summaryPayload }),
      });
      MockWebSocket.lastInstance!.onmessage!(msg);
    });

    expect(result.current.complete).toBe(true);
    expect(result.current.summary).toEqual(summaryPayload);
  });

  it('becomes disconnected after onclose fires', () => {
    const { result } = renderHook(() => useWebSocket('job-123'));

    act(() => {
      MockWebSocket.lastInstance!.onopen!(new Event('open'));
    });

    act(() => {
      MockWebSocket.lastInstance!.onclose!(new CloseEvent('close'));
    });

    expect(result.current.status).toBe('disconnected');
  });

  // -------------------------------------------------------------------------
  // New reconnection tests
  // -------------------------------------------------------------------------

  it('does not reconnect on clean close (code 1000)', async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useWebSocket('job-123'));

    act(() => { MockWebSocket.lastInstance!.onopen!(new Event('open')); });
    act(() => { MockWebSocket.lastInstance!.onclose!(new CloseEvent('close', { code: 1000 })); });

    act(() => { vi.advanceTimersByTime(30000); });

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(result.current.status).toBe('disconnected');
  });

  it('reconnects after 1s on first unexpected close', async () => {
    vi.useFakeTimers();
    renderHook(() => useWebSocket('job-123'));

    act(() => { MockWebSocket.instances[0].onopen!(new Event('open')); });
    act(() => { MockWebSocket.instances[0].onclose!(new CloseEvent('close', { code: 1006 })); });

    expect(MockWebSocket.instances).toHaveLength(1);
    act(() => { vi.advanceTimersByTime(999); });
    expect(MockWebSocket.instances).toHaveLength(1);
    act(() => { vi.advanceTimersByTime(1); });
    expect(MockWebSocket.instances).toHaveLength(2);
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
  });

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
  });

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
  });

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
  });

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
  });
});
