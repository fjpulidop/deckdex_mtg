import { useTranslation } from 'react-i18next';
import type { DeckListItem } from '../api/client';
import { DeckDropTarget } from './DeckDropTarget';

interface AllocationDropZoneProps {
  decks: DeckListItem[];
  isLoading: boolean;
}

export function AllocationDropZone({ decks, isLoading }: AllocationDropZoneProps) {
  const { t } = useTranslation();

  return (
    <div
      role="region"
      aria-label={t('allocations.dropZoneLabel')}
      className="mb-4"
    >
      <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">
        {t('allocations.dragToAdd')}
      </p>
      <div className="flex gap-2 overflow-x-auto pb-2">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex-shrink-0 w-28 h-16 rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse" />
            ))
          : decks.length === 0
            ? <p className="text-xs text-gray-400 dark:text-gray-500">{t('allocations.noDecks')}</p>
            : decks.map((deck) => <DeckDropTarget key={deck.id} deck={deck} />)
        }
      </div>
    </div>
  );
}
