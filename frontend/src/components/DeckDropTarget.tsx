import { useDroppable } from '@dnd-kit/core';
import { useTranslation } from 'react-i18next';
import type { DeckListItem } from '../api/client';

interface DeckDropTargetProps {
  deck: DeckListItem;
}

export function DeckDropTarget({ deck }: DeckDropTargetProps) {
  const { t } = useTranslation();
  const { setNodeRef, isOver } = useDroppable({ id: `deck-${deck.id}` });

  return (
    <div
      ref={setNodeRef}
      aria-label={t('allocations.deckDropTargetLabel', { deckName: deck.name })}
      className={`
        flex-shrink-0 w-28 h-16 rounded-lg border-2 border-dashed
        flex items-center justify-center text-center px-2
        text-xs font-medium transition-colors
        ${isOver
          ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
          : 'border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-400'}
      `}
    >
      <span className="truncate">{deck.name}</span>
    </div>
  );
}
