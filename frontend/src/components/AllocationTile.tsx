import { useRef, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { CardAllocation } from '../api/client';
import { useImageCache } from '../hooks/useImageCache';

export type AllocationStatus = 'available' | 'assigned' | 'shared';

/**
 * Derives a card's allocation status from the number of decks it appears in.
 * Exported for unit testing.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function getAllocationStatus(deckCount: number): AllocationStatus {
  if (deckCount === 0) return 'available';
  if (deckCount === 1) return 'assigned';
  return 'shared';
}

const STATUS_COLORS: Record<AllocationStatus, string> = {
  available: 'bg-green-500',
  assigned: 'bg-orange-500',
  shared: 'bg-red-500',
};

interface AllocationTileProps {
  allocation: CardAllocation;
  onTileClick: (allocation: CardAllocation) => void;
  isDragging?: boolean;
}

/**
 * Renders a card image tile with a color-coded status badge indicating
 * how many decks the card is currently assigned to.
 *
 * Uses IntersectionObserver for lazy loading to avoid fetching images
 * for off-screen tiles in large collections.
 */
export function AllocationTile({ allocation, onTileClick, isDragging }: AllocationTileProps) {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLButtonElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observerRef.current?.disconnect();
        }
      },
      { rootMargin: '200px' },
    );
    observerRef.current.observe(el);

    return () => observerRef.current?.disconnect();
  }, []);

  // Only pass cardId once element is in (or near) viewport
  const cardId = isVisible ? allocation.card_id : null;
  const { src } = useImageCache(cardId);
  const status = getAllocationStatus(allocation.decks.length);

  const STATUS_LABEL_KEYS: Record<AllocationStatus, string> = {
    available: t('allocations.statusAvailable'),
    assigned: t('allocations.statusAssigned'),
    shared: t('allocations.statusShared'),
  };

  return (
    <button
      ref={ref}
      type="button"
      onClick={() => onTileClick(allocation)}
      aria-label={t('allocations.tileLabel', { name: allocation.card_name, status: STATUS_LABEL_KEYS[status] })}
      className={`relative aspect-[63/88] rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 w-full${isDragging ? ' opacity-40 scale-95' : ''}`}
    >
      {src && (
        <img
          src={src}
          alt={allocation.card_name}
          className="absolute inset-0 w-full h-full object-cover"
        />
      )}
      {/* Status badge — positioned bottom-right corner */}
      <span
        aria-hidden="true"
        className={`absolute bottom-1 right-1 w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 ${STATUS_COLORS[status]}`}
      />
    </button>
  );
}
