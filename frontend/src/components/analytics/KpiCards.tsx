import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useCountUp } from './useCountUp';
import { formatCurrency } from './constants';
import type { RarityEntry } from './RarityChart';

interface Stats {
  total_cards: number;
  total_value: number;
  average_price: number;
}

interface KpiCardsProps {
  stats: Stats | undefined;
  rarityData: RarityEntry[] | undefined;
  isLoading: boolean;
  error: unknown;
}

function AnimatedKpi({
  label,
  value,
  format = 'number',
  accentClass,
}: {
  label: string;
  value: number;
  format?: 'number' | 'currency';
  accentClass: string;
}) {
  const animated = useCountUp(value);

  const display = format === 'currency'
    ? formatCurrency(animated)
    : Math.round(animated).toLocaleString();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
      <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
        {label}
      </div>
      <div className={`text-3xl font-bold ${accentClass}`}>
        {display}
      </div>
    </div>
  );
}

function SkeletonKpi() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 animate-pulse border border-gray-100 dark:border-gray-700">
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
    </div>
  );
}

export function KpiCards({ stats, rarityData, isLoading, error }: KpiCardsProps) {
  const { t } = useTranslation();

  const mythicCount = useMemo(() => {
    if (!rarityData) return 0;
    return rarityData
      .filter(r => r.rarity.toLowerCase() === 'mythic' || r.rarity.toLowerCase() === 'mythic rare')
      .reduce((sum, r) => sum + r.count, 0);
  }, [rarityData]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[1, 2, 3, 4].map(i => <SkeletonKpi key={i} />)}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 text-center mb-8">
        <p className="text-red-600 dark:text-red-400 mb-2">{t('analytics.failedToLoad')}</p>
        <button onClick={() => window.location.reload()} className="text-sm text-red-500 hover:underline">
          {t('analytics.retry')}
        </button>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <AnimatedKpi
        label={t('analytics.kpis.totalCards')}
        value={stats.total_cards}
        accentClass="text-gray-900 dark:text-white"
      />
      <AnimatedKpi
        label={t('analytics.kpis.totalValue')}
        value={stats.total_value}
        format="currency"
        accentClass="text-green-600 dark:text-green-400"
      />
      <AnimatedKpi
        label={t('analytics.kpis.mythicRares')}
        value={mythicCount}
        accentClass="text-orange-500 dark:text-orange-400"
      />
      <AnimatedKpi
        label={t('analytics.kpis.avgPrice')}
        value={stats.average_price}
        format="currency"
        accentClass="text-indigo-600 dark:text-indigo-400"
      />
    </div>
  );
}
