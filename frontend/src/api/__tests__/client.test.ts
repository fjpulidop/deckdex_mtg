import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { api } from '../client';

describe('api client (apiFetch behaviour)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends credentials: include for cookie-based auth', async () => {
    const mockResponse = new Response(JSON.stringify([]), { status: 200 });
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(mockResponse);

    await api.getCards();

    expect(fetchSpy).toHaveBeenCalledOnce();
    const [, init] = fetchSpy.mock.calls[0];
    expect(init?.credentials).toBe('include');
  });

  it('throws a user-friendly error on "Failed to fetch"', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Failed to fetch'));

    await expect(api.getCards()).rejects.toThrow('Cannot reach the backend');
  });

  it('re-throws unknown errors unchanged', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Some other error'));

    await expect(api.getCards()).rejects.toThrow('Some other error');
  });

  it('returns parsed JSON from a successful getCards response', async () => {
    const cards = [{ name: 'Lightning Bolt', rarity: 'common' }];
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(cards), { status: 200 })
    );

    const result = await api.getCards();
    expect(result).toEqual(cards);
  });
});
