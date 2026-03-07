import { useState, useEffect } from 'react';
import { api } from '../api/client';

interface ImageCacheState {
  src: string | null;
  loading: boolean;
  error: boolean;
}

// Module-level cache — lives for the browser session (keyed by card id)
const imageCache = new Map<number, string>();

// Tracks in-flight requests to avoid duplicate fetches for the same card
const inflightRequests = new Map<number, Promise<string>>();

/**
 * Returns a cached blob URL for a card image.
 *
 * - Returns immediately (no loading flash) if the image is already cached.
 * - Deduplicates concurrent fetches for the same card id.
 * - Blob URLs are never revoked — intentional, as revocation defeats the cache.
 */
export function useImageCache(cardId: number | null): ImageCacheState {
  const cached = cardId != null ? imageCache.get(cardId) : undefined;

  const [state, setState] = useState<ImageCacheState>(() => {
    if (cardId == null) return { src: null, loading: false, error: false };
    if (cached !== undefined) return { src: cached, loading: false, error: false };
    return { src: null, loading: true, error: false };
  });

  useEffect(() => {
    if (cardId == null) {
      setState({ src: null, loading: false, error: false });
      return;
    }

    // Return cached value immediately
    const cachedUrl = imageCache.get(cardId);
    if (cachedUrl !== undefined) {
      setState({ src: cachedUrl, loading: false, error: false });
      return;
    }

    let cancelled = false;
    setState({ src: null, loading: true, error: false });

    // Reuse in-flight promise if one exists for this card
    let fetchPromise = inflightRequests.get(cardId);
    if (!fetchPromise) {
      fetchPromise = api.fetchCardImage(cardId);
      inflightRequests.set(cardId, fetchPromise);
      fetchPromise.then(
        (url) => {
          imageCache.set(cardId, url);
          inflightRequests.delete(cardId);
        },
        () => {
          inflightRequests.delete(cardId);
        },
      );
    }

    fetchPromise.then(
      (url) => {
        if (!cancelled) setState({ src: url, loading: false, error: false });
      },
      () => {
        if (!cancelled) setState({ src: null, loading: false, error: true });
      },
    );

    return () => {
      cancelled = true;
    };
  }, [cardId]);

  return state;
}
