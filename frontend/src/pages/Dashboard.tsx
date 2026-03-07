import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useCards, useFilterOptions, useTriggerPriceUpdate } from '../hooks/useApi';
import { useActiveJobs } from '../contexts/ActiveJobsContext';
import { Filters } from '../components/Filters';
import { CardTable } from '../components/CardTable';
import { CardGallery } from '../components/CardGallery';
import { CardFormModal } from '../components/CardFormModal';
import { ImportListModal } from '../components/ImportListModal';
import { CardDetailModal } from '../components/CardDetailModal';
import { CollectionInsights } from '../components/CollectionInsights';
import { api, Card } from '../api/client';

type CollectionView = 'table' | 'gallery';

export function Dashboard() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [cardModal, setCardModal] = useState<null | 'add' | 'import'>(null);
  const [detailCard, setDetailCard] = useState<Card | null>(null);

  // Filter state owned by URL params
  const search    = searchParams.get('q')        ?? '';
  const rarity    = searchParams.get('rarity')   ?? 'all';
  const type      = searchParams.get('type')     ?? 'all';
  const setFilter = searchParams.get('set')      ?? 'all';
  const priceMin  = searchParams.get('priceMin') ?? '';
  const priceMax  = searchParams.get('priceMax') ?? '';
  // Color identity filter (local state — not in URL for simplicity)
  const [colors, setColors] = useState<string[]>([]);

  // Server-side pagination and sorting state
  const [page, setPage] = useState(1);

  // View toggle: 'table' | 'gallery', persisted to localStorage
  const [view, setView] = useState<CollectionView>(() => {
    const stored = localStorage.getItem('collectionView');
    return stored === 'gallery' ? 'gallery' : 'table';
  });

  const PAGE_SIZE = view === 'gallery' ? 24 : 50;

  const handleViewChange = useCallback((next: CollectionView) => {
    setView(next);
    localStorage.setItem('collectionView', next);
    setPage(1);
  }, []);
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  // Map frontend column keys to API sort_by values (price → price_eur for DB column name)
  const API_SORT_COLUMN: Record<string, string> = {
    price: 'price_eur',
  };
  const apiSortBy = API_SORT_COLUMN[sortBy] ?? sortBy;

  const { data: cardPage, isLoading, error } = useCards({
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
    search: search || undefined,
    rarity: rarity === 'all' ? undefined : rarity,
    type: type === 'all' ? undefined : type,
    set: setFilter === 'all' ? undefined : setFilter,
    priceMin: priceMin.trim() || undefined,
    priceMax: priceMax.trim() || undefined,
    colorIdentity: colors.length ? colors.join(',') : undefined,
    sortBy: apiSortBy,
    sortDir,
  });

  const totalPages = cardPage ? Math.max(1, Math.ceil(cardPage.total / PAGE_SIZE)) : 1;

  const handleSortChange = useCallback((key: string, dir: 'asc' | 'desc') => {
    setSortBy(key);
    setSortDir(dir);
    setPage(1);
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  // Fetch distinct type and set values for filter dropdowns (avoids loading full collection)
  const { data: filterOptions } = useFilterOptions();

  const invalidateCards = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['cards'] });
    queryClient.invalidateQueries({ queryKey: ['stats'] });
  }, [queryClient]);

  const refetchAfterPriceUpdate = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ['cards'] });
    await queryClient.invalidateQueries({ queryKey: ['stats'] });
    const cardId = detailCard?.id;
    if (cardId != null) {
      try {
        const updated = await api.getCard(String(cardId));
        setDetailCard((prev) => (prev?.id === updated.id ? updated : prev));
      } catch {
        // ignore
      }
    }
  }, [queryClient, detailCard?.id]);

  const { addJob } = useActiveJobs();
  const triggerPriceUpdate = useTriggerPriceUpdate();

  const handleUpdatePrices = useCallback(() => {
    triggerPriceUpdate.mutate(undefined, {
      onSuccess: (data) => {
        if (data?.job_id) {
          addJob(data.job_id, 'Update Prices', invalidateCards);
        }
      },
    });
  }, [triggerPriceUpdate, addJob, invalidateCards]);

  const handleAddCard = useCallback(() => setCardModal('add'), []);
  const handleImport = useCallback(() => setCardModal('import'), []);
  const handleRowClick = useCallback((card: Card) => setDetailCard(card), []);

  const handleCardSubmit = useCallback(async (payload: Partial<Card>) => {
    if (cardModal === 'add') {
      await api.createCard(payload);
    }
    invalidateCards();
    await queryClient.refetchQueries({ queryKey: ['cards'] });
    await queryClient.refetchQueries({ queryKey: ['stats'] });
  }, [cardModal, invalidateCards, queryClient]);

  // Filter handlers — write to URL, replace history entry, reset pagination
  const handleSearchChange = useCallback((value: string) => {
    setPage(1);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value) next.set('q', value); else next.delete('q');
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const handleRarityChange = useCallback((value: string) => {
    setPage(1);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value !== 'all') next.set('rarity', value); else next.delete('rarity');
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const handleTypeChange = useCallback((value: string) => {
    setPage(1);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value !== 'all') next.set('type', value); else next.delete('type');
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const handleSetChange = useCallback((value: string) => {
    setPage(1);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value !== 'all') next.set('set', value); else next.delete('set');
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const handlePriceRangeChange = useCallback((min: string, max: string) => {
    setPage(1);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (min.trim()) next.set('priceMin', min); else next.delete('priceMin');
      if (max.trim()) next.set('priceMax', max); else next.delete('priceMax');
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const handleClearFilters = useCallback(() => {
    setPage(1);
    setSearchParams({}, { replace: true });
    setColors([]);
  }, [setSearchParams, setColors]);

  // Use server-provided filter options (distinct types/sets from DB) for dropdowns.
  // Falls back to deriving from current page items if filter-options not yet loaded.
  const displayCards = cardPage?.items ?? [];
  const serverTotal = cardPage?.total;

  const typeOptions = filterOptions?.types.length
    ? filterOptions.types
    : Array.from(new Set(displayCards.map(c => c.type).filter(Boolean) as string[])).sort((a, b) => a.localeCompare(b));
  const setOptions = filterOptions?.sets.length
    ? filterOptions.sets
    : Array.from(new Set(displayCards.map(c => c.set_name).filter(Boolean) as string[])).sort((a, b) => a.localeCompare(b));

  const hasPriceRange =
    (priceMin.trim() !== '' && Number.isFinite(parseFloat(priceMin.replace(',', '.')))) ||
    (priceMax.trim() !== '' && Number.isFinite(parseFloat(priceMax.replace(',', '.'))));

  const activeChips: { id: string; label: string; onRemove: () => void }[] = [];
  if (rarity !== 'all') {
    activeChips.push({
      id: 'rarity',
      label: rarity.charAt(0).toUpperCase() + rarity.slice(1),
      onRemove: () => handleRarityChange('all'),
    });
  }
  if (type !== 'all') {
    activeChips.push({ id: 'type', label: type, onRemove: () => handleTypeChange('all') });
  }
  if (setFilter !== 'all') {
    activeChips.push({
      id: 'set',
      label: `Set: ${setFilter}`,
      onRemove: () => handleSetChange('all'),
    });
  }
  if (hasPriceRange) {
    const minStr = priceMin.trim() ? `€${priceMin}` : '';
    const maxStr = priceMax.trim() ? `€${priceMax}` : '';
    activeChips.push({
      id: 'price',
      label: minStr && maxStr ? `${minStr} – ${maxStr}` : minStr || maxStr,
      onRemove: () => handlePriceRangeChange('', ''),
    });
  }
  for (const c of colors) {
    activeChips.push({
      id: `color-${c}`,
      label: `Color: ${c}`,
      onRemove: () => setColors(prev => prev.filter(x => x !== c)),
    });
  }

  if (error) {
    return (
      <div className="relative min-h-screen flex items-center justify-center">
        <div role="alert" className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-lg">
          <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">{t('dashboard.backendError')}</h1>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            {t('dashboard.backendErrorDesc')}
          </p>
          <div className="space-y-3 text-sm">
            <p className="font-medium text-gray-800 dark:text-gray-200">{t('dashboard.dockerHint')}</p>
            <pre className="bg-gray-100 dark:bg-gray-700 p-3 rounded overflow-x-auto text-gray-900 dark:text-gray-100">
docker compose up --build
            </pre>
            <p className="font-medium text-gray-800 dark:text-gray-200 mt-2">{t('dashboard.backendHint')}</p>
            <pre className="bg-gray-100 dark:bg-gray-700 p-3 rounded overflow-x-auto text-gray-900 dark:text-gray-100">
cd backend{'\n'}
uvicorn api.main:app --reload --port 8000
            </pre>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            {t('dashboard.retryConnection')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen">
      <div className="container mx-auto px-4 py-8">
        {/* Collection Insights */}
        <CollectionInsights onCardClick={handleRowClick} />

        {/* Filters */}
        <Filters
          search={search}
          onSearchChange={handleSearchChange}
          rarity={rarity}
          onRarityChange={handleRarityChange}
          type={type}
          onTypeChange={handleTypeChange}
          typeOptions={typeOptions}
          set={setFilter}
          onSetChange={handleSetChange}
          setOptions={setOptions}
          priceMin={priceMin}
          priceMax={priceMax}
          onPriceRangeChange={handlePriceRangeChange}
          colors={colors}
          onColorsChange={setColors}
          activeChips={activeChips}
          resultCount={serverTotal ?? displayCards.length}
          onClearFilters={handleClearFilters}
        />

        {/* View toggle */}
        <div className="flex justify-end mb-3">
          <div
            role="group"
            aria-label={t('viewToggle.label')}
            className="flex border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden"
          >
            <button
              type="button"
              onClick={() => handleViewChange('table')}
              aria-pressed={view === 'table'}
              aria-label={t('viewToggle.table')}
              className={`px-3 py-2 text-sm ${view === 'table' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
            >
              {/* Table icon: three horizontal lines */}
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <rect x="0" y="2" width="16" height="2" rx="1"/>
                <rect x="0" y="7" width="16" height="2" rx="1"/>
                <rect x="0" y="12" width="16" height="2" rx="1"/>
              </svg>
            </button>
            <button
              type="button"
              onClick={() => handleViewChange('gallery')}
              aria-pressed={view === 'gallery'}
              aria-label={t('viewToggle.gallery')}
              className={`px-3 py-2 text-sm border-l border-gray-300 dark:border-gray-600 ${view === 'gallery' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
            >
              {/* Gallery icon: 2x2 grid squares */}
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <rect x="0" y="0" width="7" height="7" rx="1"/>
                <rect x="9" y="0" width="7" height="7" rx="1"/>
                <rect x="0" y="9" width="7" height="7" rx="1"/>
                <rect x="9" y="9" width="7" height="7" rx="1"/>
              </svg>
            </button>
          </div>
        </div>

        {/* Card collection: table or gallery view */}
        {view === 'table' ? (
          <CardTable
            cards={displayCards}
            isLoading={isLoading}
            onAdd={handleAddCard}
            onImport={handleImport}
            onUpdatePrices={handleUpdatePrices}
            updatingPrices={triggerPriceUpdate.isPending}
            onRowClick={handleRowClick}
            serverTotal={serverTotal}
            sortBy={sortBy}
            sortDir={sortDir}
            onSortChange={handleSortChange}
            page={page}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        ) : (
          <CardGallery
            cards={displayCards}
            isLoading={isLoading}
            onAdd={handleAddCard}
            onImport={handleImport}
            onUpdatePrices={handleUpdatePrices}
            updatingPrices={triggerPriceUpdate.isPending}
            onRowClick={handleRowClick}
            serverTotal={serverTotal}
            sortBy={sortBy}
            sortDir={sortDir}
            onSortChange={handleSortChange}
            page={page}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        )}
      </div>

      {cardModal === 'add' && (
        <CardFormModal
          mode="add"
          title={t('dashboard.addCard')}
          initial={undefined}
          onSubmit={handleCardSubmit}
          onClose={() => setCardModal(null)}
        />
      )}

      {cardModal === 'import' && (
        <ImportListModal onClose={() => setCardModal(null)} />
      )}

      {detailCard && (
        <CardDetailModal
          card={detailCard}
          onClose={() => setDetailCard(null)}
          onPriceUpdateJobComplete={refetchAfterPriceUpdate}
          onCardUpdated={(updated) => {
            setDetailCard(updated);
            invalidateCards();
          }}
          onCardDeleted={() => {
            setDetailCard(null);
            invalidateCards();
          }}
        />
      )}
    </div>
  );
}
