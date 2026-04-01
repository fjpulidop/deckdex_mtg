/**
 * @deprecated Replaced by CardInspectorSidebar (feat/card-allocation-dashboard, ticket #4).
 * This file is retained to avoid breaking any residual import paths during
 * the transition. It has no callers in the updated CardAllocations page.
 * Remove in a future cleanup chore.
 */
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import type { CardAllocation } from '../api/client';

interface AllocationPopoverProps {
  allocation: CardAllocation;
  onRemoveFromDeck: (deckId: number, cardId: number) => void;
  onClose: () => void;
}

/**
 * Popover anchored to an AllocationTile. Shows the card's deck assignments
 * and allows removing the card from any deck.
 *
 * Accessibility: role="dialog", focus on close button on mount, Escape closes.
 */
export function AllocationPopover({ allocation, onRemoveFromDeck, onClose }: AllocationPopoverProps) {
  const { t } = useTranslation();
  const closeRef = useRef<HTMLButtonElement>(null);
  // Track in-flight remove operations to show disabled state per deck
  const [pendingDeckIds, setPendingDeckIds] = useState<Set<number>>(new Set());

  // Focus the close button on mount and handle Escape key
  useEffect(() => {
    closeRef.current?.focus();

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const handleRemove = (deckId: number) => {
    setPendingDeckIds((prev) => new Set(prev).add(deckId));
    onRemoveFromDeck(deckId, allocation.card_id);
    // The parent clears selectedAllocation after success, which unmounts this
    // component. We only clear pending state if the parent does not unmount us
    // (e.g. on error). Keeping it disabled after a failed remove is acceptable
    // UX — the user can close and reopen to retry.
  };

  return (
    <div
      role="dialog"
      aria-label={`${allocation.card_name} allocation details`}
      className="absolute z-50 top-0 left-full ml-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 p-3"
    >
      {/* Header: card name + close button */}
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white pr-2 leading-tight">
          {allocation.card_name}
        </h3>
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          aria-label={t('allocations.close')}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content: either available message or deck list */}
      {allocation.decks.length === 0 ? (
        <p className="text-xs text-green-600 dark:text-green-400">
          {t('allocations.available')}
        </p>
      ) : (
        <>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('allocations.assignedTo')}</p>
          <ul className="space-y-1">
            {allocation.decks.map((deck) => {
              const isPending = pendingDeckIds.has(deck.deck_id);
              return (
                <li key={deck.deck_id} className="flex items-center justify-between gap-2">
                  <span className="text-xs text-gray-700 dark:text-gray-300 truncate">
                    {deck.deck_name}
                  </span>
                  <button
                    type="button"
                    disabled={isPending}
                    onClick={() => handleRemove(deck.deck_id)}
                    aria-label={t('allocations.removeFrom', { deckName: deck.deck_name })}
                    className="flex-shrink-0 text-xs text-red-600 dark:text-red-400 hover:underline focus:outline-none focus:ring-2 focus:ring-red-500 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isPending ? t('allocations.removing') : t('allocations.remove')}
                  </button>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}
