import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';

interface SuggestionChipProps {
  deckId: number;
  onClick: () => void;
}

export function SuggestionChip({ deckId, onClick }: SuggestionChipProps) {
  const { t } = useTranslation();
  const { data } = useQuery({
    queryKey: ['deckSuggestions', deckId],
    queryFn: () => api.getDeckSuggestions(deckId),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const count = data?.suggestions.length ?? 0;
  if (count === 0) return null;

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      aria-label={t('suggestions.ariaChip', { count })}
      className="absolute bottom-2 left-2 z-30 bg-purple-600 text-white text-xs font-semibold px-1.5 py-0.5 rounded hover:bg-purple-500 transition-colors"
    >
      {t('suggestions.chipLabel', { count })}
    </button>
  );
}
