import { useState, useEffect } from 'react';
import { api } from '../api/client';

interface CardImageState {
  src: string | null;
  loading: boolean;
  error: boolean;
}

/**
 * Fetch a card image via authenticated request and return a Blob URL.
 * The Blob URL is revoked automatically on unmount or when cardId changes.
 */
export function useCardImage(cardId: number | null): CardImageState {
  const [state, setState] = useState<CardImageState>({ src: null, loading: false, error: false });

  useEffect(() => {
    if (cardId == null) {
      setState({ src: null, loading: false, error: false });
      return;
    }

    let blobUrl: string | null = null;
    let cancelled = false;

    setState({ src: null, loading: true, error: false });

    api.fetchCardImage(cardId).then((url) => {
      if (cancelled) {
        URL.revokeObjectURL(url);
        return;
      }
      blobUrl = url;
      setState({ src: url, loading: false, error: false });
    }).catch(() => {
      if (!cancelled) {
        setState({ src: null, loading: false, error: true });
      }
    });

    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [cardId]);

  return state;
}
