import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';
import { api } from '../api/client';
import { ComparisonDeckColumn } from './ComparisonDeckColumn';
import { OverlapCardList } from './OverlapCardList';

interface ComparisonViewProps {
  selectedIds: number[];
}

export function ComparisonView({ selectedIds }: ComparisonViewProps) {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const sortedIds = [...selectedIds].sort((a, b) => a - b);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['deck-comparison', sortedIds.join(',')],
    queryFn: () => api.compareDecks(selectedIds),
    enabled: selectedIds.length >= 2,
  });

  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-2">
        {selectedIds.map(id => (
          <div
            key={id}
            className="min-w-[180px] max-w-[240px] rounded-lg bg-gray-100 dark:bg-gray-800 p-3 animate-pulse flex flex-col gap-3"
          >
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-3 py-8">
        <p className="text-red-600 dark:text-red-400 text-sm">
          {t('deckComparison.error')}: {error instanceof Error ? error.message : String(error)}
        </p>
        <button
          type="button"
          onClick={() => refetch()}
          className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
        >
          {t('common.retry')}
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div>
      <div className="flex gap-4 overflow-x-auto pb-2">
        {data.decks.map(stats => (
          <ComparisonDeckColumn key={stats.deck_id} stats={stats} isDark={isDark} />
        ))}
      </div>
      <OverlapCardList cards={data.overlap_cards} decks={data.decks} />
    </div>
  );
}
