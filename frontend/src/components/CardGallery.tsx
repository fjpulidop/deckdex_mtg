import { useRef, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Card } from '../api/client';
import type { CardCollectionViewProps } from '../types/collection';
import { useImageCache } from '../hooks/useImageCache';

// ---------------------------------------------------------------------------
// CardTile — internal component for a single gallery tile
// ---------------------------------------------------------------------------

interface CardTileProps {
  card: Card;
  onRowClick?: (card: Card) => void;
}

function CardTile({ card, onRowClick }: CardTileProps) {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLButtonElement>(null);

  // IntersectionObserver: trigger image fetch when tile enters viewport.
  // We use a ref for the observer so we can disconnect it from inside the
  // callback without a TDZ issue (important for testability with sync mocks).
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

  const cardId = isVisible && card.id != null ? card.id : null;
  const { src, loading, error } = useImageCache(cardId);

  return (
    <button
      ref={ref}
      type="button"
      onClick={() => onRowClick?.(card)}
      aria-label={t('gallery.tileLabel', { name: card.name ?? t('gallery.unknownCard') })}
      className="relative aspect-[63/88] rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 group w-full"
    >
      {/* Pre-intersection placeholder */}
      {!isVisible && (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700" aria-hidden />
      )}

      {/* Quantity badge — shown for multi-copy cards */}
      {(card.quantity ?? 0) > 1 && (
        <div
          className="absolute top-1 right-1 z-10 bg-indigo-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
          aria-label={t('gallery.quantityBadge', { count: card.quantity })}
        >
          {card.quantity}
        </div>
      )}

      {/* Error placeholder — static, no animation */}
      {isVisible && error && (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 gap-1 p-2"
          aria-label={t('cardDetail.imageUnavailable')}
        >
          <svg
            className="w-8 h-8 opacity-40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <rect x="3" y="2" width="18" height="20" rx="2" />
            <circle cx="12" cy="11" r="4" />
            <path d="M8 18c0-2.2 1.8-4 4-4s4 1.8 4 4" />
          </svg>
          <span className="text-xs text-center leading-tight">
            {t('cardDetail.imageUnavailable')}
          </span>
        </div>
      )}

      {/* Loading skeleton — only when genuinely loading (not error) */}
      {isVisible && !error && (loading || !src) && (
        <div className="absolute inset-0 animate-pulse bg-gray-300 dark:bg-gray-600" aria-hidden />
      )}

      {/* Card image */}
      {src && (
        <img
          src={src}
          alt={card.name ?? t('gallery.unknownCard')}
          className="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
        />
      )}

      {/* Hover overlay: name + price */}
      <div className="absolute inset-x-0 bottom-0 translate-y-full group-hover:translate-y-0 group-focus:translate-y-0 transition-transform duration-200 bg-gradient-to-t from-black/80 to-transparent p-2">
        <p className="text-white text-xs font-semibold leading-tight truncate">
          {card.name ?? '\u2014'}
        </p>
        {card.price && card.price !== 'N/A' && (
          <p className="text-gray-300 text-xs mt-0.5">&euro;{card.price}</p>
        )}
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// CardGallery — main exported component
// ---------------------------------------------------------------------------

const GRID_CLASSES =
  'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3';

export function CardGallery({
  cards,
  isLoading,
  onAdd,
  onImport,
  onUpdatePrices,
  updatingPrices,
  onRowClick,
  serverTotal,
  page = 1,
  totalPages = 1,
  onPageChange,
  sortBy,
  sortDir,
  onSortChange,
}: CardCollectionViewProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);

  // Scroll-to-top when page changes
  useEffect(() => {
    containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [page]);

  // Toolbar
  const toolbar = (onAdd || onImport || onUpdatePrices || onSortChange) && (
    <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-600 flex flex-wrap items-center gap-2">
      {onAdd && (
        <button
          type="button"
          onClick={onAdd}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm dark:bg-green-500 dark:hover:bg-green-600"
        >
          {t('cardTable.addCard')}
        </button>
      )}
      {onImport && (
        <button
          type="button"
          onClick={onImport}
          className="px-4 py-2 border border-indigo-600 text-indigo-600 bg-transparent rounded hover:bg-indigo-50 text-sm dark:border-indigo-400 dark:text-indigo-400 dark:hover:bg-indigo-950"
        >
          {t('cardTable.importList')}
        </button>
      )}
      {onUpdatePrices && (
        <button
          type="button"
          onClick={onUpdatePrices}
          disabled={updatingPrices}
          className="px-4 py-2 border border-gray-400 text-gray-600 bg-transparent rounded hover:bg-gray-50 text-sm disabled:opacity-50 dark:border-gray-500 dark:text-gray-400 dark:hover:bg-gray-800"
        >
          {updatingPrices ? t('cardTable.starting') : t('cardTable.updatePrices')}
        </button>
      )}
      {onSortChange && (
        <div className="ml-auto flex items-center gap-2">
          <select
            id="gallery-sort-by"
            value={sortBy ?? 'created_at'}
            onChange={(e) => onSortChange(e.target.value, sortDir ?? 'desc')}
            className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200"
            aria-label={t('gallery.sortBy')}
          >
            <option value="name">{t('cardTable.columns.name')}</option>
            <option value="type">{t('cardTable.columns.type')}</option>
            <option value="rarity">{t('cardTable.columns.rarity')}</option>
            <option value="price">{t('cardTable.columns.price')}</option>
            <option value="created_at">{t('cardTable.columns.added')}</option>
          </select>
          <button
            type="button"
            onClick={() => onSortChange(sortBy ?? 'created_at', sortDir === 'asc' ? 'desc' : 'asc')}
            aria-label={sortDir === 'asc' ? t('gallery.sortDirDesc') : t('gallery.sortDirAsc')}
            className="p-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            {sortDir === 'asc' ? '\u2191' : '\u2193'}
          </button>
        </div>
      )}
    </div>
  );

  // Loading skeleton
  if (isLoading) {
    return (
      <div
        ref={containerRef}
        className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden scroll-mt-20"
      >
        {toolbar}
        <div className={`p-4 ${GRID_CLASSES}`}>
          {Array.from({ length: 24 }).map((_, i) => (
            <div
              key={i}
              className="aspect-[63/88] rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  // Pagination helpers
  const displayTotal = serverTotal ?? cards.length;
  const pageSize = cards.length;
  const startIndex = serverTotal !== undefined ? (page - 1) * pageSize : 0;

  return (
    <div
      ref={containerRef}
      className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden scroll-mt-20"
    >
      {toolbar}

      {/* Grid */}
      <div role="list" className={`p-4 ${GRID_CLASSES}`}>
        {cards.map((card, index) => (
          <div key={card.id ?? index} role="listitem">
            <CardTile card={card} onRowClick={onRowClick} />
          </div>
        ))}
      </div>

      {/* Empty state */}
      {cards.length === 0 && (
        <div className="py-20 text-center text-gray-500 dark:text-gray-400">
          <p className="text-lg font-medium">{t('gallery.noCards')}</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-gray-50 dark:bg-gray-700/50 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-600">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            {t('cardTable.showing', {
              from: startIndex + 1,
              to: Math.min(startIndex + pageSize, displayTotal),
              total: displayTotal,
            })}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange?.(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1 rounded bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-sm text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              {t('common.previous')}
            </button>
            <span className="px-3 py-1 text-sm text-gray-700 dark:text-gray-300">
              {t('cardTable.page', { current: page, total: totalPages })}
            </span>
            <button
              onClick={() => onPageChange?.(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 rounded bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-sm text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              {t('common.next')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
