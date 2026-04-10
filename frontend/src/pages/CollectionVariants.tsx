import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useCollectionVariants } from '../hooks/useApi';
import { VariantGroupCard } from '../components/VariantGroupCard';

const PAGE_SIZE = 50;

export function CollectionVariants() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [page, setPage] = useState(1);

  // Debounce search 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset to first page on new search
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, isLoading, error } = useCollectionVariants({
    search: debouncedSearch || undefined,
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
  });

  const isPostgresError =
    error instanceof Error && error.message.includes('501');

  const totalPages = data ? Math.ceil(data.total_cards / PAGE_SIZE) : 1;

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Page title */}
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        {t('variants.title')}
      </h1>

      {/* Search input */}
      <div className="mb-6">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('variants.searchPlaceholder')}
          aria-label={t('variants.searchPlaceholder')}
          className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
        />
      </div>

      {/* PostgreSQL notice */}
      {isPostgresError && (
        <div
          role="alert"
          className="mb-6 p-4 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 text-amber-800 dark:text-amber-300"
        >
          {t('variants.notAvailablePostgresOnly')}
        </div>
      )}

      {/* Generic error state */}
      {error && !isPostgresError && (
        <div
          role="alert"
          className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 text-red-800 dark:text-red-300"
        >
          {error instanceof Error ? error.message : String(error)}
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 p-4"
            >
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-3" />
              <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded w-full" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && data && data.groups.length === 0 && (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400">
          <p className="text-lg">{t('variants.empty')}</p>
        </div>
      )}

      {/* Variant groups list */}
      {!isLoading && !error && data && data.groups.length > 0 && (
        <div className="space-y-4">
          {data.groups.map((group) => (
            <VariantGroupCard key={group.card_name} group={group} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!isLoading && !error && data && data.total_cards > PAGE_SIZE && (
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium text-gray-700 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            {t('common.previous')}
          </button>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {page} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium text-gray-700 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            {t('common.next')}
          </button>
        </div>
      )}
    </div>
  );
}
