import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { AccessibleModal } from './AccessibleModal';
import { DeckHistoryTimeline } from './DeckHistoryTimeline';

interface DeckHistoryModalProps {
  deckId: number;
  onClose: () => void;
  onReverted: () => void;
}

export function DeckHistoryModal({ deckId, onClose, onReverted }: DeckHistoryModalProps) {
  const { t } = useTranslation();

  const { data, isLoading, error } = useQuery({
    queryKey: ['deck-history', deckId],
    queryFn: () => api.getDeckHistory(deckId),
  });

  return (
    <AccessibleModal isOpen titleId="deck-history-modal-title" onClose={onClose} className="z-[60]">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <h2 id="deck-history-modal-title" className="text-base font-semibold text-gray-900 dark:text-white">
            {t('deckHistory.title')}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm"
          >
            {t('deckHistory.close')}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('deckHistory.loading')}</p>
          )}
          {error && (
            <p role="alert" className="text-sm text-red-600 dark:text-red-400">
              {error instanceof Error ? error.message : t('deckHistory.revertError')}
            </p>
          )}
          {data && (
            <DeckHistoryTimeline
              deckId={deckId}
              snapshots={data.snapshots}
              onReverted={() => {
                onReverted();
                onClose();
              }}
            />
          )}
        </div>
      </div>
    </AccessibleModal>
  );
}
