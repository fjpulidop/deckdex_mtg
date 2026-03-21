import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

interface RevertButtonProps {
  deckId: number;
  snapshotId: number;
  onReverted: () => void;
  disabled?: boolean;
}

export function RevertButton({ deckId, snapshotId, onReverted, disabled = false }: RevertButtonProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRevert = async () => {
    setError(null);
    setPending(true);
    try {
      const deck = await api.revertDeck(deckId, snapshotId);
      // Update deck detail cache immediately with the reverted state
      queryClient.setQueryData(['deck', deckId], deck);
      // Invalidate history so the new revert snapshot appears
      await queryClient.invalidateQueries({ queryKey: ['deck-history', deckId] });
      // Invalidate deck list for updated card count
      await queryClient.invalidateQueries({ queryKey: ['decks'] });
      onReverted();
    } catch (e) {
      const msg = e instanceof Error ? e.message : t('deckHistory.revertError');
      setError(msg.includes('no longer exists') ? t('deckHistory.revertCardMissing') : msg);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={handleRevert}
        disabled={disabled || pending}
        className="px-2 py-1 text-xs rounded bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-800/50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {pending ? t('deckHistory.reverting') : t('deckHistory.revert')}
      </button>
      {error && (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400 max-w-[180px] text-right">
          {error}
        </p>
      )}
    </div>
  );
}
