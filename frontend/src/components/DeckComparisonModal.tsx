import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AccessibleModal } from './AccessibleModal';
import { DeckMultiSelect } from './DeckMultiSelect';
import { ComparisonView } from './ComparisonView';
import type { DeckListItem } from '../api/client';

interface DeckComparisonModalProps {
  decks: DeckListItem[];
  onClose: () => void;
}

type Step = 'select' | 'compare';

export function DeckComparisonModal({ decks, onClose }: DeckComparisonModalProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState<Step>('select');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const handleToggle = (id: number) => {
    setSelectedIds(prev => {
      if (prev.includes(id)) {
        return prev.filter(x => x !== id);
      }
      if (prev.length < 4) {
        return [...prev, id];
      }
      return prev;
    });
  };

  const handleConfirm = () => {
    setStep('compare');
  };

  return (
    <AccessibleModal
      isOpen={true}
      onClose={onClose}
      titleId="deck-comparison-modal-title"
      showCloseButton={true}
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden">
        {step === 'select' && (
          <DeckMultiSelect
            decks={decks}
            selectedIds={selectedIds}
            onToggle={handleToggle}
            onConfirm={handleConfirm}
            onCancel={onClose}
          />
        )}
        {step === 'compare' && (
          <>
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-3">
              <button
                type="button"
                onClick={() => setStep('select')}
                className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                {t('deckComparison.backButton')}
              </button>
              <h2
                id="deck-comparison-modal-title"
                className="text-lg font-semibold text-gray-900 dark:text-white"
              >
                {t('deckComparison.title')}
              </h2>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <ComparisonView selectedIds={selectedIds} />
            </div>
          </>
        )}
      </div>
    </AccessibleModal>
  );
}
