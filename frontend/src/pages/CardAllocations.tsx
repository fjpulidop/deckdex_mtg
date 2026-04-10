import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  DndContext,
  MouseSensor,
  TouchSensor,
  KeyboardSensor,
  useSensors,
  useSensor,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { CardAllocation, CardAllocationsResponse } from '../api/client';
import { DraggableTile } from '../components/DraggableTile';
import { AllocationDropZone } from '../components/AllocationDropZone';
import { CardInspectorSidebar } from '../components/CardInspectorSidebar';

/**
 * Page at /allocations — shows all cards in the user's collection as a grid
 * of image tiles, each with a color-coded badge indicating whether the card
 * is unassigned (green), in one deck (orange), or in multiple decks (red).
 *
 * Clicking a tile opens a CardInspectorSidebar (replaced AllocationPopover).
 * Cards can be dragged onto deck drop targets to allocate them.
 */
export function CardAllocations() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [inspectedCard, setInspectedCard] = useState<CardAllocation | null>(null);

  // Card allocations query
  const { data, isLoading, error } = useQuery({
    queryKey: ['card-allocations'],
    queryFn: api.getCardAllocations,
  });

  // Deck list query (for drop zone and sidebar)
  const { data: decksData, isLoading: decksLoading } = useQuery({
    queryKey: ['decks'],
    queryFn: api.getDecks,
  });

  // dnd-kit sensors
  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 8 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 5 } }),
    useSensor(KeyboardSensor),
  );

  // Allocate (add) mutation with optimistic update
  const allocateMutation = useMutation({
    mutationFn: ({ deckId, cardId }: { deckId: number; cardId: number }) =>
      api.allocateCardToDeck(deckId, cardId),
    onMutate: async ({ deckId, cardId }) => {
      await queryClient.cancelQueries({ queryKey: ['card-allocations'] });
      const previous = queryClient.getQueryData(['card-allocations']);
      queryClient.setQueryData(['card-allocations'], (old: CardAllocationsResponse | undefined) => {
        if (!old) return old;
        return {
          ...old,
          cards: old.cards.map((card) => {
            if (card.card_id !== cardId) return card;
            const alreadyIn = card.decks.some((d) => d.deck_id === deckId);
            if (alreadyIn) return card;
            const deck = decksData?.find((d) => d.id === deckId);
            if (!deck) return card;
            return { ...card, decks: [...card.decks, { deck_id: deckId, deck_name: deck.name }] };
          }),
        };
      });
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['card-allocations'], context.previous);
      }
    },
    onSuccess: () => {
      // Close sidebar so user re-opens with fresh data after invalidation
      setInspectedCard(null);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['card-allocations'] });
    },
  });

  // Remove from single deck mutation with optimistic update
  const removeMutation = useMutation({
    mutationFn: ({ deckId, cardId }: { deckId: number; cardId: number }) =>
      api.removeCardFromDeck(deckId, cardId),
    onMutate: async ({ deckId, cardId }) => {
      await queryClient.cancelQueries({ queryKey: ['card-allocations'] });
      const previous = queryClient.getQueryData(['card-allocations']);
      queryClient.setQueryData(['card-allocations'], (old: CardAllocationsResponse | undefined) => {
        if (!old) return old;
        return {
          ...old,
          cards: old.cards.map((card) => {
            if (card.card_id !== cardId) return card;
            return { ...card, decks: card.decks.filter((d) => d.deck_id !== deckId) };
          }),
        };
      });
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['card-allocations'], context.previous);
      }
    },
    onSuccess: () => {
      setInspectedCard(null);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['card-allocations'] });
    },
  });

  // Remove from all decks mutation with optimistic update
  const removeFromAllMutation = useMutation({
    mutationFn: async ({ cardId, deckIds }: { cardId: number; deckIds: number[] }) => {
      for (const deckId of deckIds) {
        await api.removeCardFromDeck(deckId, cardId);
      }
    },
    onMutate: async ({ cardId }) => {
      await queryClient.cancelQueries({ queryKey: ['card-allocations'] });
      const previous = queryClient.getQueryData(['card-allocations']);
      queryClient.setQueryData(['card-allocations'], (old: CardAllocationsResponse | undefined) => {
        if (!old) return old;
        return {
          ...old,
          cards: old.cards.map((card) => {
            if (card.card_id !== cardId) return card;
            return { ...card, decks: [] };
          }),
        };
      });
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['card-allocations'], context.previous);
      }
    },
    onSuccess: () => {
      setInspectedCard(null);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['card-allocations'] });
    },
  });

  // Drag end handler
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;
    const overId = over.id.toString();
    if (!overId.startsWith('deck-')) return;
    const deckId = parseInt(overId.replace('deck-', ''), 10);
    const allocation = active.data.current?.allocation as CardAllocation | undefined;
    if (!allocation) return;
    allocateMutation.mutate({ deckId, cardId: allocation.card_id });
  };

  const handleAddToDeck = (deckId: number, cardId: number) => {
    allocateMutation.mutate({ deckId, cardId });
  };

  const handleRemoveFromDeck = (deckId: number, cardId: number) => {
    removeMutation.mutate({ deckId, cardId });
  };

  const handleRemoveFromAll = (cardId: number) => {
    const card = data?.cards.find((c) => c.card_id === cardId);
    if (!card) return;
    const deckIds = card.decks.map((d) => d.deck_id);
    if (deckIds.length === 0) return;
    removeFromAllMutation.mutate({ cardId, deckIds });
  };

  const isPending =
    allocateMutation.isPending ||
    removeMutation.isPending ||
    removeFromAllMutation.isPending;

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

      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        {/* Deck drop zone */}
        <AllocationDropZone decks={decksData ?? []} isLoading={decksLoading} />

        {/* Card grid */}
        <div className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3">
          {data?.cards.map((allocation) => (
            <DraggableTile
              key={allocation.card_id}
              allocation={allocation}
              onTileClick={setInspectedCard}
            />
          ))}
        </div>
      </DndContext>

      {/* Card inspector sidebar */}
      {inspectedCard !== null && (
        <CardInspectorSidebar
          allocation={inspectedCard}
          allDecks={decksData ?? []}
          onAddToDeck={handleAddToDeck}
          onRemoveFromDeck={handleRemoveFromDeck}
          onRemoveFromAll={handleRemoveFromAll}
          onClose={() => setInspectedCard(null)}
          isPending={isPending}
        />
      )}
    </div>
  );
}
