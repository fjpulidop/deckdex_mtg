import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { api, DeckImportResponse } from '../api/client';
import { AccessibleModal } from './AccessibleModal';

interface DeckImportModalProps {
  deckId: number;
  onClose: () => void;
  onImported: (result: DeckImportResponse) => void;
}

export function DeckImportModal({ deckId, onClose, onImported }: DeckImportModalProps) {
  const { t } = useTranslation();
  const [text, setText] = useState('');
  const [result, setResult] = useState<DeckImportResponse | null>(null);

  const mutation = useMutation({
    mutationFn: (deckText: string) => api.importDeckText(deckId, deckText),
    onSuccess: (data) => {
      setResult(data);
      onImported(data);
    },
  });

  const handleSubmit = useCallback(() => {
    if (!text.trim()) return;
    mutation.mutate(text);
  }, [text, mutation]);

  const handleDone = useCallback(() => {
    onClose();
  }, [onClose]);

  return (
    <AccessibleModal isOpen titleId="deck-import-modal-title" onClose={onClose} className="z-[70]" showCloseButton>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <h2 id="deck-import-modal-title" className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('deckImport.title')}
          </h2>
        </div>

        {/* Body */}
        <div className="px-6 py-4 flex flex-col gap-4">
          {result === null ? (
            <>
              <textarea
                className="w-full h-48 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono placeholder:text-gray-400 dark:placeholder:text-gray-500"
                placeholder={t('deckImport.placeholder')}
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={mutation.isPending}
                autoFocus
              />
              {mutation.isError && (
                <p role="alert" className="text-sm text-red-600 dark:text-red-400">
                  {mutation.error instanceof Error
                    ? mutation.error.message
                    : 'Import failed'}
                </p>
              )}
            </>
          ) : (
            <div className="flex flex-col gap-3">
              {/* Success summary */}
              <p className="text-sm font-medium text-green-700 dark:text-green-400">
                {t('deckImport.success', { count: result.imported_count })}
              </p>
              {/* Skipped cards */}
              {result.skipped.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('deckImport.skippedTitle', { count: result.skipped.length })}
                  </p>
                  <ul className="max-h-40 overflow-y-auto rounded border border-gray-200 dark:border-gray-600 divide-y divide-gray-100 dark:divide-gray-700">
                    {result.skipped.map((card, idx) => (
                      <li
                        key={idx}
                        className="flex items-center justify-between px-3 py-1.5 text-sm"
                      >
                        <span className="text-gray-800 dark:text-gray-200">
                          {card.quantity}x {card.name}
                        </span>
                        <span className="text-gray-400 dark:text-gray-500 text-xs ml-2">
                          {t('deckImport.notInCollection')}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end gap-3">
          {result === null ? (
            <>
              <button
                type="button"
                onClick={onClose}
                disabled={mutation.isPending}
                className="px-4 py-2 rounded text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
              >
                {t('deckImport.cancel')}
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={mutation.isPending || !text.trim()}
                className="px-4 py-2 rounded text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 disabled:opacity-50"
              >
                {mutation.isPending ? t('deckImport.loading') : t('deckImport.submit')}
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleDone}
              className="px-4 py-2 rounded text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
            >
              {t('deckImport.done')}
            </button>
          )}
        </div>
      </div>
    </AccessibleModal>
  );
}
