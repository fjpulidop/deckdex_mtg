import { useCallback, useSyncExternalStore } from 'react';
import { api } from '../api/client';

interface ImageCacheState {
  src: string | null;
  loading: boolean;
  error: boolean;
}

// Module-level cache — lives for the browser session (keyed by card id)
const imageCache = new Map<number, string>();

// Tracks cards that errored
const errorCards = new Set<number>();

// Tracks in-flight requests to avoid duplicate fetches for the same card
const inflightRequests = new Map<number, Promise<string>>();

// Subscriber management for useSyncExternalStore
const listeners = new Set<() => void>();
function emitChange() {
  listeners.forEach((fn) => fn());
}
function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

// Stable snapshot objects — avoids infinite loops in useSyncExternalStore
const NULL_STATE: ImageCacheState = { src: null, loading: false, error: false };
const LOADING_STATE: ImageCacheState = { src: null, loading: true, error: false };
const ERROR_STATE: ImageCacheState = { src: null, loading: false, error: true };
const srcSnapshots = new Map<string, ImageCacheState>();
function getSrcSnapshot(url: string): ImageCacheState {
  let s = srcSnapshots.get(url);
  if (!s) {
    s = { src: url, loading: false, error: false };
    srcSnapshots.set(url, s);
  }
  return s;
}

function ensureFetching(cardId: number) {
  if (imageCache.has(cardId) || inflightRequests.has(cardId)) return;
  const promise = api.fetchCardImage(cardId);
  inflightRequests.set(cardId, promise);
  promise.then(
    (url) => {
      imageCache.set(cardId, url);
      errorCards.delete(cardId);
      inflightRequests.delete(cardId);
      emitChange();
    },
    () => {
      errorCards.add(cardId);
      inflightRequests.delete(cardId);
      emitChange();
    },
  );
}

/**
 * Returns a cached blob URL for a card image.
 *
 * - Returns immediately (no loading flash) if the image is already cached.
 * - Deduplicates concurrent fetches for the same card id.
 * - Blob URLs are never revoked — intentional, as revocation defeats the cache.
 */
export function useImageCache(cardId: number | null): ImageCacheState {
  // Kick off fetch outside of getSnapshot (side-effect at render time is fine
  // for fire-and-forget data fetching — React docs explicitly allow this for
  // subscriptions to external stores).
  if (cardId != null) ensureFetching(cardId);

  const getSnapshot = useCallback((): ImageCacheState => {
    if (cardId == null) return NULL_STATE;
    const url = imageCache.get(cardId);
    if (url !== undefined) return getSrcSnapshot(url);
    if (errorCards.has(cardId)) return ERROR_STATE;
    return LOADING_STATE;
  }, [cardId]);

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
