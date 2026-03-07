import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useImageCache } from '../useImageCache';

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------
vi.mock('../../api/client', () => ({
  api: {
    fetchCardImage: vi.fn(),
  },
}));

import { api } from '../../api/client';
const mockFetchCardImage = api.fetchCardImage as ReturnType<typeof vi.fn>;

// ---------------------------------------------------------------------------
// Note on the module-level cache
// ---------------------------------------------------------------------------
// The cache is module-level (Map<number, string>). Tests use unique card ids
// to avoid state pollution between tests. Card ids 1000–1099 are reserved
// for this test file to avoid collisions with other test files.
//
// The only test that requires two hook renders for the same card id is the
// deduplication test — it uses id 1001 and clears the mock carefully.

describe('useImageCache', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns null state synchronously when cardId is null', () => {
    const { result } = renderHook(() => useImageCache(null));
    expect(result.current).toEqual({ src: null, loading: false, error: false });
    expect(mockFetchCardImage).not.toHaveBeenCalled();
  });

  it('fetches image and returns blob URL for a valid card id', async () => {
    mockFetchCardImage.mockResolvedValue('blob:test-url-1010');
    const { result } = renderHook(() => useImageCache(1010));

    // Should start loading
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.src).toBe('blob:test-url-1010');
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(false);
    expect(mockFetchCardImage).toHaveBeenCalledTimes(1);
    expect(mockFetchCardImage).toHaveBeenCalledWith(1010);
  });

  it('returns error state when fetch rejects', async () => {
    mockFetchCardImage.mockRejectedValue(new Error('fetch failed'));
    const { result } = renderHook(() => useImageCache(1020));

    await waitFor(() => {
      expect(result.current.error).toBe(true);
    });

    expect(result.current.src).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('deduplicates in-flight requests — only one fetch for two simultaneous calls', async () => {
    let resolve!: (url: string) => void;
    const promise = new Promise<string>((res) => { resolve = res; });
    mockFetchCardImage.mockReturnValue(promise);

    // Render two hooks with same card id simultaneously
    const { result: r1 } = renderHook(() => useImageCache(1030));
    const { result: r2 } = renderHook(() => useImageCache(1030));

    // Both should be loading
    expect(r1.current.loading).toBe(true);
    expect(r2.current.loading).toBe(true);

    // Only one API call should have been made (deduplication)
    expect(mockFetchCardImage).toHaveBeenCalledTimes(1);

    // Resolve the shared promise
    await act(async () => {
      resolve('blob:shared-url-1030');
      await promise;
    });

    await waitFor(() => {
      expect(r1.current.src).toBe('blob:shared-url-1030');
    });
    await waitFor(() => {
      expect(r2.current.src).toBe('blob:shared-url-1030');
    });

    // Still only one call total
    expect(mockFetchCardImage).toHaveBeenCalledTimes(1);
  });

  it('returns cached result immediately on second mount (no extra fetch)', async () => {
    mockFetchCardImage.mockResolvedValue('blob:cached-url-1040');

    // First render — fetch happens and caches the result
    const { result: r1, unmount } = renderHook(() => useImageCache(1040));
    await waitFor(() => expect(r1.current.src).toBe('blob:cached-url-1040'));
    unmount();

    vi.clearAllMocks();

    // Second render — should get cached value immediately (no new fetch)
    const { result: r2 } = renderHook(() => useImageCache(1040));
    expect(r2.current.src).toBe('blob:cached-url-1040');
    expect(r2.current.loading).toBe(false);

    // No additional fetch calls were made
    expect(mockFetchCardImage).not.toHaveBeenCalled();
  });
});
