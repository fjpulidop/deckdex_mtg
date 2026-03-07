import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AccessibleModal } from './AccessibleModal';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  promptLabel?: string;
  promptDefault?: string;
  onConfirm: (value?: string) => void;
  onCancel: () => void;
}

export function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel,
  cancelLabel,
  destructive = false,
  promptLabel,
  promptDefault = '',
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  const { t } = useTranslation();
  const resolvedConfirmLabel = confirmLabel ?? t('confirmModal.confirm');
  const resolvedCancelLabel = cancelLabel ?? t('confirmModal.cancel');
  const [promptValue, setPromptValue] = useState(promptDefault);
  const confirmRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset prompt value when opened
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: reset form state when modal opens
    if (isOpen) setPromptValue(promptDefault);
  }, [isOpen, promptDefault]);

  // Focus confirm button or prompt input on open (overrides AccessibleModal's auto-focus)
  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(() => {
      if (promptLabel) inputRef.current?.focus();
      else confirmRef.current?.focus();
    }, 0);
    return () => clearTimeout(timer);
  }, [isOpen, promptLabel]);

  return (
    <AccessibleModal
      isOpen={isOpen}
      onClose={onCancel}
      titleId="confirm-modal-title"
      className="z-[70]"
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-sm w-full p-6 flex flex-col gap-4">
        <h2 id="confirm-modal-title" className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>

        {promptLabel && (
          <div>
            <label
              htmlFor="confirm-modal-prompt"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              {promptLabel}
            </label>
            <input
              id="confirm-modal-prompt"
              ref={inputRef}
              type="text"
              value={promptValue}
              onChange={e => setPromptValue(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') onConfirm(promptValue);
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium"
          >
            {resolvedCancelLabel}
          </button>
          <button
            ref={confirmRef}
            type="button"
            onClick={() => onConfirm(promptLabel ? promptValue : undefined)}
            className={`px-4 py-2 rounded-lg text-white text-sm font-medium ${
              destructive
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {resolvedConfirmLabel}
          </button>
        </div>
      </div>
    </AccessibleModal>
  );
}
