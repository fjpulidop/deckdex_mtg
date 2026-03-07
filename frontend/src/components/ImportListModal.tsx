import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { AccessibleModal } from './AccessibleModal';

interface ImportListModalProps {
  onClose: () => void;
}

type InputMode = 'file' | 'text';

export function ImportListModal({ onClose }: ImportListModalProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [inputMode, setInputMode] = useState<InputMode>('text');
  const [pastedText, setPastedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResolve = async (file?: File, text?: string) => {
    setError(null);
    setLoading(true);
    try {
      const data = await api.importResolve(file, text);
      onClose();
      navigate('/import', { state: { resolveData: data } });
    } catch (e) {
      setError(e instanceof Error ? e.message : t('import.errorParsingFile'));
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (selected: File) => {
    handleResolve(selected);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFileSelect(f);
  };

  const handleTextSubmit = () => {
    if (!pastedText.trim()) return;
    handleResolve(undefined, pastedText);
  };

  return (
    <AccessibleModal isOpen titleId="import-list-modal-title" onClose={onClose} showCloseButton>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <h2 id="import-list-modal-title" className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">{t('importListModal.title')}</h2>

        {error && <div role="alert" className="mb-4 text-red-600 dark:text-red-400 text-sm">{error}</div>}

        {/* Tab toggle */}
        <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden mb-4">
          <button
            type="button"
            onClick={() => setInputMode('file')}
            className={`flex-1 py-2 text-sm font-medium transition ${inputMode === 'file' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
          >
            {t('importListModal.fileTab')}
          </button>
          <button
            type="button"
            onClick={() => setInputMode('text')}
            className={`flex-1 py-2 text-sm font-medium transition ${inputMode === 'text' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
          >
            {t('importListModal.textTab')}
          </button>
        </div>

        {inputMode === 'file' ? (
          <div
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center hover:border-indigo-400 transition"
          >
            <div className="text-3xl mb-3">📁</div>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{t('importListModal.dragDrop')}</p>
            <label className="cursor-pointer">
              <span className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm">
                {loading ? t('importListModal.resolving') : t('importListModal.selectFile')}
              </span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.txt"
                className="sr-only"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
              />
            </label>
          </div>
        ) : (
          <div className="space-y-3">
            <textarea
              value={pastedText}
              onChange={e => setPastedText(e.target.value)}
              placeholder={t('importListModal.textPlaceholder')}
              rows={8}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-800 dark:text-gray-100 p-3 font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}

        {/* Footer buttons */}
        <div className="flex gap-2 justify-end pt-4">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 text-sm"
          >
            {t('common.cancel')}
          </button>
          {inputMode === 'text' && (
            <button
              type="button"
              onClick={handleTextSubmit}
              disabled={loading || !pastedText.trim()}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 text-sm"
            >
              {loading ? t('importListModal.resolving') : t('importListModal.continue')}
            </button>
          )}
        </div>
      </div>
    </AccessibleModal>
  );
}
