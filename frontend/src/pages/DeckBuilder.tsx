import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, DeckListItem } from '../api/client';
import { ThemeToggle } from '../components/ThemeToggle';
import { DeckDetailModal } from '../components/DeckDetailModal';

export function DeckBuilder() {
  const queryClient = useQueryClient();
  const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const {
    data: decks,
    isLoading,
    error: decksError,
    refetch: refetchDecks,
  } = useQuery({
    queryKey: ['decks'],
    queryFn: () => api.getDecks(),
    retry: (_, err) => !(err instanceof Error && err.message.includes('Postgres')),
  });

  const decksUnavailable =
    decksError instanceof Error && decksError.message.includes('Postgres');
  const list: DeckListItem[] = decks ?? [];

  const handleAddDeck = useCallback(async () => {
    setCreateError(null);
    const name = window.prompt('Deck name', 'Unnamed Deck') ?? 'Unnamed Deck';
    try {
      const deck = await api.createDeck(name);
      await queryClient.invalidateQueries({ queryKey: ['decks'] });
      setSelectedDeckId(deck.id);
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : 'Failed to create deck');
    }
  }, [queryClient]);

  const handleCloseModal = useCallback(() => {
    setSelectedDeckId(null);
    refetchDecks();
  }, [refetchDecks]);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              DeckDex MTG
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Commander decks (alpha)
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link to="/" className="text-blue-600 hover:underline dark:text-blue-400">
              Dashboard
            </Link>
            <Link to="/analytics" className="text-indigo-600 hover:underline dark:text-indigo-400">
              Analytics
            </Link>
            <Link to="/settings" className="text-blue-600 hover:underline dark:text-blue-400">
              Settings
            </Link>
          </div>
        </div>

        {decksUnavailable && (
          <div className="mb-6 p-4 rounded-lg bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200">
            Decks require Postgres. Set DATABASE_URL to use the deck builder.
          </div>
        )}

        {createError && (
          <div className="mb-6 p-4 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200">
            {createError}
          </div>
        )}

        {isLoading && (
          <p className="text-gray-500 dark:text-gray-400">Loading decks...</p>
        )}

        {!decksUnavailable && !isLoading && (
          <div
            className="grid gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5"
            style={{ gridAutoRows: 'minmax(120px, auto)' }}
          >
            <button
              type="button"
              onClick={handleAddDeck}
              className="flex items-center justify-center rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:border-indigo-500 hover:text-indigo-600 dark:hover:border-indigo-400 dark:hover:text-indigo-300 transition-colors min-h-[120px]"
              aria-label="Add deck"
            >
              <span className="text-3xl font-light">+</span>
            </button>
            {list.map((deck) => {
              const commanderImageUrl =
                deck.commander_card_id != null
                  ? api.getCardImageUrl(deck.commander_card_id)
                  : null;
              return (
                <button
                  key={deck.id}
                  type="button"
                  onClick={() => setSelectedDeckId(deck.id)}
                  className="relative flex flex-col items-stretch justify-end rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden p-4 text-left shadow-sm hover:ring-2 hover:ring-indigo-500 dark:hover:ring-indigo-400 min-h-[120px] h-full bg-gray-200 dark:bg-gray-700"
                >
                  {commanderImageUrl && (
                    <div
                      className="absolute inset-0 rounded-xl overflow-hidden"
                      aria-hidden
                    >
                      {/* Imagen del comandante: cubre todo el botón, alineada arriba */}
                      <div
                        className="absolute inset-0 bg-cover bg-top bg-no-repeat"
                        style={{ backgroundImage: `url(${commanderImageUrl})` }}
                      />
                      {/* Oscurecer todo el fondo de forma uniforme para que se lea bien el texto */}
                      <div className="absolute inset-0 bg-black/55 pointer-events-none" />
                    </div>
                  )}
                  <span
                    className={`relative z-10 font-medium truncate w-full ${
                      commanderImageUrl
                        ? 'text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]'
                        : 'text-gray-900 dark:text-white'
                    }`}
                  >
                    {deck.name}
                  </span>
                  <span
                    className={`relative z-10 text-sm ${
                      commanderImageUrl
                        ? 'text-white/90 drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {deck.card_count ?? 0} cards
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {selectedDeckId != null && (
        <DeckDetailModal
          deckId={selectedDeckId}
          onClose={handleCloseModal}
          onDeleted={handleCloseModal}
        />
      )}
    </div>
  );
}
