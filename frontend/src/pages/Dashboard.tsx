import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useCards } from '../hooks/useApi';
import { StatsCards } from '../components/StatsCards';
import { Filters } from '../components/Filters';
import { CardTable } from '../components/CardTable';
import { CardFormModal } from '../components/CardFormModal';
import { CardDetailModal } from '../components/CardDetailModal';
import { api, Card } from '../api/client';

export function Dashboard() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('all');
  const [type, setType] = useState('all');
  const [setFilter, setSetFilter] = useState('all');
  const [priceMin, setPriceMin] = useState('');
  const [priceMax, setPriceMax] = useState('');
  const [cardModal, setCardModal] = useState<null | 'add'>(null);
  const [detailCard, setDetailCard] = useState<Card | null>(null);

  // Fetch cards with current filters so list and stats match (API applies filters server-side)
  const { data: cards, isLoading, error } = useCards({
    search: search || undefined,
    rarity: rarity === 'all' ? undefined : rarity,
    type: type === 'all' ? undefined : type,
    set: setFilter === 'all' ? undefined : setFilter,
    priceMin: priceMin.trim() || undefined,
    priceMax: priceMax.trim() || undefined,
    limit: 10000,
  });

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

  const handleAddCard = useCallback(() => setCardModal('add'), []);
  const handleRowClick = useCallback((card: Card) => setDetailCard(card), []);

  const handleCardSubmit = useCallback(async (payload: Partial<Card>) => {
    if (cardModal === 'add') {
      await api.createCard(payload);
    }
    invalidateCards();
    // Refetch so Total Cards and Total Value are updated when the modal closes
    await queryClient.refetchQueries({ queryKey: ['cards'] });
    await queryClient.refetchQueries({ queryKey: ['stats'] });
  }, [cardModal, invalidateCards, queryClient]);

  // Derive type and set options from API response (filtered result)
  const typeOptions = Array.from(
    new Set((cards || []).map(c => c.type).filter(Boolean) as string[])
  ).sort((a, b) => a.localeCompare(b));
  const setOptions = Array.from(
    new Set((cards || []).map(c => c.set_name).filter(Boolean) as string[])
  ).sort((a, b) => a.localeCompare(b));

  // List is the API response (filters applied server-side); no client-side filter
  const displayCards = cards ?? [];

  const handleSearchChange = (value: string) => setSearch(value);
  const handleRarityChange = (value: string) => setRarity(value);
  const handleTypeChange = (value: string) => setType(value);
  const handleSetChange = (value: string) => setSetFilter(value);
  const handlePriceRangeChange = (min: string, max: string) => {
    setPriceMin(min);
    setPriceMax(max);
  };

  const handleClearFilters = () => {
    setSearch('');
    setRarity('all');
    setType('all');
    setSetFilter('all');
    setPriceMin('');
    setPriceMax('');
  };

  const hasPriceRange =
    (priceMin.trim() !== '' && Number.isFinite(parseFloat(priceMin.replace(',', '.')))) ||
    (priceMax.trim() !== '' && Number.isFinite(parseFloat(priceMax.replace(',', '.'))));

  const activeChips: { id: string; label: string; onRemove: () => void }[] = [];
  if (rarity !== 'all') {
    activeChips.push({
      id: 'rarity',
      label: rarity.charAt(0).toUpperCase() + rarity.slice(1),
      onRemove: () => setRarity('all'),
    });
  }
  if (type !== 'all') {
    activeChips.push({ id: 'type', label: type, onRemove: () => setType('all') });
  }
  if (setFilter !== 'all') {
    activeChips.push({
      id: 'set',
      label: `Set: ${setFilter}`,
      onRemove: () => setSetFilter('all'),
    });
  }
  if (hasPriceRange) {
    const minStr = priceMin.trim() ? `€${priceMin}` : '';
    const maxStr = priceMax.trim() ? `€${priceMax}` : '';
    activeChips.push({
      id: 'price',
      label: minStr && maxStr ? `${minStr} – ${maxStr}` : minStr || maxStr,
      onRemove: () => {
        setPriceMin('');
        setPriceMax('');
      },
    });
  }

  // Show error if backend is not accessible (after all hooks)
  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-lg">
          <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">Backend Connection Error</h1>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            Cannot connect to the backend API at http://localhost:8000. Start it in one of these ways:
          </p>
          <div className="space-y-3 text-sm">
            <p className="font-medium text-gray-800 dark:text-gray-200">Docker (all services):</p>
            <pre className="bg-gray-100 dark:bg-gray-700 p-3 rounded overflow-x-auto text-gray-900 dark:text-gray-100">
docker compose up --build
            </pre>
            <p className="font-medium text-gray-800 dark:text-gray-200 mt-2">Or run backend only (from repo root):</p>
            <pre className="bg-gray-100 dark:bg-gray-700 p-3 rounded overflow-x-auto text-gray-900 dark:text-gray-100">
cd backend{'\n'}
uvicorn api.main:app --reload --port 8000
            </pre>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            DeckDex MTG
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your Magic: The Gathering collection
          </p>
        </div>

        {/* Stats Cards: pass current filters so totals reflect the filtered set */}
        <StatsCards
          filters={{
            search: search || undefined,
            rarity: rarity === 'all' ? undefined : rarity,
            type: type === 'all' ? undefined : type,
            set: setFilter === 'all' ? undefined : setFilter,
            priceMin: priceMin.trim() || undefined,
            priceMax: priceMax.trim() || undefined,
          }}
        />

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
          activeChips={activeChips}
          resultCount={displayCards.length}
          onClearFilters={handleClearFilters}
        />

        {/* Card Table */}
        <CardTable
          cards={displayCards}
          isLoading={isLoading}
          onAdd={handleAddCard}
          onRowClick={handleRowClick}
        />
      </div>

      {cardModal === 'add' && (
        <CardFormModal
          mode="add"
          title="Add card"
          initial={undefined}
          onSubmit={handleCardSubmit}
          onClose={() => setCardModal(null)}
        />
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
