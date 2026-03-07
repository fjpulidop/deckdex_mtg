import { useImageCache } from './useImageCache';

interface CardImageState {
  src: string | null;
  loading: boolean;
  error: boolean;
}

/**
 * Fetch a card image via authenticated request and return a cached Blob URL.
 *
 * Delegates to useImageCache — images are cached for the browser session and
 * never re-fetched, regardless of how many times the hook mounts or unmounts.
 */
export function useCardImage(cardId: number | null): CardImageState {
  return useImageCache(cardId);
}
