import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { api, DeckSuggestion } from '../api/client';
import { AccessibleModal } from './AccessibleModal';
import { ManaText } from './ManaText';

interface SuggestionModalProps {
  deckId: number;
  isOpen: boolean;
  onClose: () => void;
}

const MODAL_TITLE_ID = 'suggestion-modal-title';

export function SuggestionModal({ deckId, isOpen, onClose }: SuggestionModalProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['deckSuggestions', deckId],
    queryFn: () => api.getDeckSuggestions(deckId),
    enabled: isOpen,
    staleTime: 5 * 60 * 1000,
  });

  const [localSuggestions, setLocalSuggestions] = useState<DeckSuggestion[]>([]);
  const [addingId, setAddingId] = useState<string | null>(null);
  const [addError, setAddError] = useState<string | null>(null);
  const [dismissingAll, setDismissingAll] = useState(false);

  // Sync local suggestions from server data
  useEffect(() => {
    if (data) {
      setLocalSuggestions(data.suggestions);
    }
  }, [data]);

  const setName = data?.set_name ?? data?.set_code ?? null;

  const handleAddToDeck = async (suggestion: DeckSuggestion) => {
    setAddingId(suggestion.scryfall_id);
    setAddError(null);
    try {
      // Resolve card data from collection or Scryfall
      const resolved = await api.resolveCardByName(suggestion.card_name);

      // Ensure the card is in the collection — createCard is idempotent on name conflict
      let cardId: number | undefined = resolved.id;
      if (!cardId) {
        const created = await api.createCard({
          name: resolved.name ?? suggestion.card_name,
          english_name: resolved.english_name,
          type: resolved.type,
          mana_cost: resolved.mana_cost ?? suggestion.mana_cost ?? undefined,
          cmc: resolved.cmc ?? (suggestion.cmc ?? undefined),
          color_identity: resolved.color_identity ?? suggestion.color_identity ?? undefined,
          rarity: resolved.rarity,
          set_name: resolved.set_name,
        });
        cardId = created.id;
      }

      if (!cardId) {
        throw new Error('Could not resolve card id');
      }

      await api.addCardToDeck(deckId, cardId, { quantity: 1 });

      // Optimistic removal
      setLocalSuggestions((prev) => prev.filter((s) => s.scryfall_id !== suggestion.scryfall_id));

      // Invalidate queries
      await queryClient.invalidateQueries({ queryKey: ['deckSuggestions', deckId] });
      await queryClient.invalidateQueries({ queryKey: ['deck', deckId] });
    } catch {
      setAddError(t('suggestions.errorAdding'));
    } finally {
      setAddingId(null);
    }
  };

  const handleDismissAll = async () => {
    setDismissingAll(true);
    try {
      for (const s of localSuggestions) {
        await api.dismissSuggestion(deckId, s.scryfall_id);
      }
      setLocalSuggestions([]);
      await queryClient.invalidateQueries({ queryKey: ['deckSuggestions', deckId] });
      onClose();
    } finally {
      setDismissingAll(false);
    }
  };

  return (
    <AccessibleModal
      isOpen={isOpen}
      onClose={onClose}
      titleId={MODAL_TITLE_ID}
      showCloseButton
      className="z-50"
    >
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2
            id={MODAL_TITLE_ID}
            className="text-lg font-semibold text-gray-900 dark:text-white"
          >
            {t('suggestions.modalTitle')}
            {setName ? ` — ${setName}` : ''}
          </h2>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <span
                className="inline-block w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"
                aria-label={t('common.loading')}
              />
            </div>
          )}

          {!isLoading && localSuggestions.length === 0 && (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              {t('suggestions.emptyState')}
            </p>
          )}

          {addError && (
            <div role="alert" className="p-3 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 text-sm">
              {addError}
            </div>
          )}

          {localSuggestions.map((s) => (
            <SuggestionRow
              key={s.scryfall_id}
              suggestion={s}
              isAdding={addingId === s.scryfall_id}
              onAdd={() => handleAddToDeck(s)}
            />
          ))}
        </div>

        {/* Footer */}
        {localSuggestions.length > 0 && (
          <div className="flex items-center justify-end px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleDismissAll}
              disabled={dismissingAll}
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50"
            >
              {dismissingAll ? t('suggestions.dismissing') : t('suggestions.dismissAll')}
            </button>
          </div>
        )}
      </div>
    </AccessibleModal>
  );
}

// ---------------------------------------------------------------------------
// SuggestionRow sub-component
// ---------------------------------------------------------------------------

interface SuggestionRowProps {
  suggestion: DeckSuggestion;
  isAdding: boolean;
  onAdd: () => void;
}

function SuggestionRow({ suggestion, isAdding, onAdd }: SuggestionRowProps) {
  const { t } = useTranslation();

  return (
    <div className="flex gap-3 items-start p-3 rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Card image */}
      <img
        src={suggestion.image_uri ?? '/placeholder-card.png'}
        alt={suggestion.card_name}
        width={60}
        height={84}
        className="rounded object-cover flex-shrink-0"
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).src = '/placeholder-card.png';
        }}
      />

      {/* Card info */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-gray-900 dark:text-white truncate">
          {suggestion.card_name}
        </p>
        {suggestion.type_line && (
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
            {suggestion.type_line}
          </p>
        )}
        {suggestion.mana_cost && (
          <div className="mt-0.5">
            <ManaText text={suggestion.mana_cost} className="text-sm" />
          </div>
        )}
        {suggestion.oracle_text && (
          <p className="mt-1 text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
            {suggestion.oracle_text}
          </p>
        )}
        <div className="mt-1.5">
          <span className="inline-block text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded px-1.5 py-0.5">
            {t('suggestions.reason', { reason: suggestion.reason })}
          </span>
        </div>
      </div>

      {/* Action */}
      <div className="flex-shrink-0">
        <button
          type="button"
          onClick={onAdd}
          disabled={isAdding}
          className="inline-flex items-center gap-1 text-sm bg-purple-600 hover:bg-purple-500 text-white px-3 py-1.5 rounded transition-colors disabled:opacity-50"
        >
          {isAdding && (
            <span className="inline-block w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
          )}
          {isAdding ? t('suggestions.adding') : t('suggestions.addToDeck')}
        </button>
      </div>
    </div>
  );
}
