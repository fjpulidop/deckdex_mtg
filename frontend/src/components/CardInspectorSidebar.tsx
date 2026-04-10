import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import type { CardAllocation, DeckListItem } from '../api/client';
import { useImageCache } from '../hooks/useImageCache';
import { ManaText } from './ManaText';

interface CardInspectorSidebarProps {
  allocation: CardAllocation;
  allDecks: DeckListItem[];
  onAddToDeck: (deckId: number, cardId: number) => void;
  onRemoveFromDeck: (deckId: number, cardId: number) => void;
  onRemoveFromAll: (cardId: number) => void;
  onClose: () => void;
  isPending: boolean;
}

export function CardInspectorSidebar({
  allocation,
  allDecks,
  onAddToDeck,
  onRemoveFromDeck,
  onRemoveFromAll,
  onClose,
  isPending,
}: CardInspectorSidebarProps) {
  const { t } = useTranslation();
  const closeRef = useRef<HTMLButtonElement>(null);
  const { src } = useImageCache(allocation.card_id);

  // Compute which decks contain this card and which don't
  const allocatedDeckIds = new Set(allocation.decks.map((d) => d.deck_id));
  const decksContaining = allDecks.filter((d) => allocatedDeckIds.has(d.id));
  const decksNotContaining = allDecks.filter((d) => !allocatedDeckIds.has(d.id));

  // Focus close button on mount; handle Escape key
  useEffect(() => {
    closeRef.current?.focus();

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <>
      {/* Semi-transparent backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20 dark:bg-black/40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar panel */}
      <aside
        role="dialog"
        aria-label={t('allocations.inspectorTitle')}
        className="fixed right-0 top-0 z-50 h-full w-72 md:w-80 bg-white dark:bg-gray-800 shadow-xl border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-y-auto"
      >
        {/* Header */}
        <header className="flex items-start justify-between p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white pr-2 leading-tight">
            {allocation.card_name}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label={t('allocations.close')}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </header>

        <div className="flex flex-col gap-4 p-4">
          {/* Card image */}
          {src && (
            <div className="w-full">
              <img
                src={src}
                alt={allocation.card_name}
                className="w-full rounded-lg shadow-md"
              />
            </div>
          )}

          {/* Mana cost */}
          {allocation.mana_cost && (
            <ManaText text={allocation.mana_cost} className="text-sm" />
          )}

          {/* Type line */}
          {allocation.type_line && (
            <p className="text-xs text-gray-500 dark:text-gray-400 italic">
              {allocation.type_line}
            </p>
          )}

          {/* In these decks */}
          {decksContaining.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                {t('allocations.inTheseDecks')}
              </h3>
              <ul className="space-y-1">
                {decksContaining.map((deck) => (
                  <li key={deck.id} className="flex items-center justify-between gap-2">
                    <span className="text-xs text-gray-700 dark:text-gray-300 truncate">
                      {deck.name}
                    </span>
                    <button
                      type="button"
                      disabled={isPending}
                      aria-label={t('allocations.removeFromDeckLabel', {
                        cardName: allocation.card_name,
                        deckName: deck.name,
                      })}
                      onClick={() => onRemoveFromDeck(deck.id, allocation.card_id)}
                      className="flex-shrink-0 text-xs text-red-600 dark:text-red-400 hover:underline focus:outline-none focus:ring-2 focus:ring-red-500 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {t('allocations.remove')}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Add to deck */}
          {decksNotContaining.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                {t('allocations.addToDeck')}
              </h3>
              <ul className="space-y-1">
                {decksNotContaining.map((deck) => (
                  <li key={deck.id} className="flex items-center justify-between gap-2">
                    <span className="text-xs text-gray-700 dark:text-gray-300 truncate">
                      {deck.name}
                    </span>
                    <button
                      type="button"
                      disabled={isPending}
                      aria-label={t('allocations.addToDeckLabel', {
                        cardName: allocation.card_name,
                        deckName: deck.name,
                      })}
                      onClick={() => onAddToDeck(deck.id, allocation.card_id)}
                      className="flex-shrink-0 text-xs text-indigo-600 dark:text-indigo-400 hover:underline focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {t('allocations.addToDeck')}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Remove from all */}
          <button
            type="button"
            disabled={isPending || allocation.decks.length === 0}
            aria-label={t('allocations.removeFromAllLabel', { cardName: allocation.card_name })}
            onClick={() => onRemoveFromAll(allocation.card_id)}
            className="w-full mt-2 text-xs text-red-600 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-md py-2 px-3 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('allocations.removeFromAll')}
          </button>
        </div>
      </aside>
    </>
  );
}
