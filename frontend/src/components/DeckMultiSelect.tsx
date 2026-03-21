import { useTranslation } from 'react-i18next';
import type { DeckListItem } from '../api/client';

interface DeckMultiSelectProps {
  decks: DeckListItem[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeckMultiSelect({
  decks,
  selectedIds,
  onToggle,
  onConfirm,
  onCancel,
}: DeckMultiSelectProps) {
  const { t } = useTranslation();
  const atMax = selectedIds.length >= 4;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6 flex flex-col gap-4">
      <h2
        id="deck-comparison-modal-title"
        className="text-lg font-semibold text-gray-900 dark:text-white"
      >
        {t('deckComparison.selectTitle')}
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        {t('deckComparison.selectPrompt')}
      </p>

      <ul className="max-h-64 overflow-y-auto space-y-2">
        {decks.map(deck => {
          const isSelected = selectedIds.includes(deck.id);
          const isDisabled = atMax && !isSelected;

          return (
            <li key={deck.id}>
              <button
                type="button"
                role="checkbox"
                aria-checked={isSelected}
                disabled={isDisabled}
                onClick={() => onToggle(deck.id)}
                className={[
                  'w-full text-left rounded-lg px-3 py-2 border transition-colors',
                  isSelected
                    ? 'ring-2 ring-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 border-indigo-300 dark:border-indigo-600'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700',
                  isDisabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
                ].join(' ')}
              >
                <span className="block font-medium text-sm text-gray-900 dark:text-white truncate">
                  {deck.name}
                </span>
                <span className="block text-xs text-gray-500 dark:text-gray-400">
                  {t('deckComparison.cards_other', { count: deck.card_count ?? 0 })}
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      {atMax && (
        <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">
          {t('deckComparison.maxDecksReached')}
        </p>
      )}

      <div className="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          {t('deckComparison.cancelButton')}
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={selectedIds.length < 2}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-indigo-500 dark:hover:bg-indigo-600"
        >
          {t('deckComparison.compareButton')}
        </button>
      </div>
    </div>
  );
}
