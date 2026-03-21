import { useTranslation } from 'react-i18next';
import { formatCurrency } from './analytics/constants';
import { ComparisonManaCurve } from './ComparisonManaCurve';
import { ComparisonColorBar } from './ComparisonColorBar';
import type { DeckComparisonStats } from '../api/client';

interface ComparisonDeckColumnProps {
  stats: DeckComparisonStats;
  isDark: boolean;
}

export function ComparisonDeckColumn({ stats, isDark }: ComparisonDeckColumnProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-3 min-w-[180px] max-w-[240px] bg-gray-50 dark:bg-gray-900/40 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
      <h3 className="font-semibold text-gray-900 dark:text-white text-sm truncate" title={stats.deck_name}>
        {stats.deck_name}
      </h3>

      <div className="flex flex-col gap-1 text-xs">
        <span className="text-gray-700 dark:text-gray-300">
          {t('deckComparison.cards_other', { count: stats.total_cards })}
        </span>
        <span className="text-gray-700 dark:text-gray-300">
          {formatCurrency(stats.total_value)}
        </span>
        <span className="text-gray-700 dark:text-gray-300">
          {t('deckComparison.creatureInstantRatio')}: {stats.creature_count}:{stats.instant_count}
        </span>
      </div>

      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
          {t('deckComparison.manaCurve')}
        </p>
        <ComparisonManaCurve data={stats.mana_curve} isDark={isDark} />
      </div>

      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
          {t('deckComparison.colorDistribution')}
        </p>
        <ComparisonColorBar data={stats.color_distribution} isDark={isDark} />
      </div>
    </div>
  );
}
