import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { CardAllocation } from '../api/client';
import { AllocationTile } from '../components/AllocationTile';
import { AllocationPopover } from '../components/AllocationPopover';

/**
 * Page at /allocations — shows all cards in the user's collection as a grid
 * of image tiles, each with a color-coded badge indicating whether the card
 * is unassigned (green), in one deck (orange), or in multiple decks (red).
 *
 * Clicking a tile opens a popover that lists the card's deck assignments and
 * allows removing the card from a specific deck.
 */
export function CardAllocations() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<CardAllocation | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['card-allocations'],
    queryFn: api.getCardAllocations,
  });

  const handleRemoveFromDeck = async (deckId: number, cardId: number) => {
    try {
      await api.removeCardFromDeck(deckId, cardId);
      await queryClient.invalidateQueries({ queryKey: ['card-allocations'] });
      setSelected(null);
    } catch (err) {
      // Surface the error inline — tile stays open so user can retry
      console.error('Failed to remove card from deck:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    const msg = error instanceof Error ? error.message : '';
    const isNoPostgres = msg.includes('501');
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        {isNoPostgres
          ? t('allocations.errorNoPostgres')
          : t('allocations.errorGeneric')}
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('allocations.title')}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('allocations.subtitle')}
        </p>
      </div>

      {/* Card grid */}
      <div className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3">
        {data?.cards.map((allocation) => (
          <div key={allocation.card_id} className="relative">
            <AllocationTile
              allocation={allocation}
              onTileClick={setSelected}
            />
            {selected?.card_id === allocation.card_id && (
              <AllocationPopover
                allocation={allocation}
                onRemoveFromDeck={handleRemoveFromDeck}
                onClose={() => setSelected(null)}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
