import { useTranslation } from 'react-i18next';

interface ChartCardProps {
  title: string;
  isLoading: boolean;
  error: unknown;
  onRetry?: () => void;
  badge?: React.ReactNode;
  children: React.ReactNode;
}

export function ChartCard({ title, isLoading, error, onRetry, badge, children }: ChartCardProps) {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">{title}</h3>
        {badge}
      </div>
      {isLoading ? (
        <div className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse flex flex-col items-center gap-2">
            <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded" />
            <div className="w-24 h-4 bg-gray-200 dark:bg-gray-700 rounded" />
            <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        </div>
      ) : error ? (
        <div className="h-[300px] flex flex-col items-center justify-center text-center">
          <p className="text-red-500 dark:text-red-400 mb-2 text-sm">{t('analytics.failedToLoadData')}</p>
          {onRetry && (
            <button onClick={() => onRetry()} className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
              {t('analytics.retry')}
            </button>
          )}
        </div>
      ) : (
        children
      )}
    </div>
  );
}
