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

  constructor(url: string) {
    this.url = url;
    MockWebSocket.lastInstance = this;
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
  }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.lastInstance = null;
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

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
});
