import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CardAllocations } from '../CardAllocations';
import type { CardAllocationsResponse, DeckListItem } from '../../api/client';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGetCardAllocations = vi.fn<() => Promise<CardAllocationsResponse>>();
const mockGetDecks = vi.fn<() => Promise<DeckListItem[]>>();
const mockRemoveCardFromDeck = vi.fn<(a: number, b: number) => Promise<void>>();
const mockAllocateCardToDeck = vi.fn();

vi.mock('../../api/client', () => ({
  api: {
    getCardAllocations: (...args: unknown[]) => mockGetCardAllocations(...(args as [])),
    getDecks: (...args: unknown[]) => mockGetDecks(...(args as [])),
    removeCardFromDeck: (...args: unknown[]) =>
      mockRemoveCardFromDeck(...(args as [number, number])),
    allocateCardToDeck: (...args: unknown[]) => mockAllocateCardToDeck(...args),
  },
}));

// Stable src avoids needing a real image in tests; also eliminates IntersectionObserver
vi.mock('../../hooks/useImageCache', () => ({
  useImageCache: vi.fn(() => ({ src: 'mock-image-url', loading: false, error: false })),
}));

// react-i18next stub
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string>) => {
      if (opts) {
        return Object.entries(opts).reduce(
          (acc, [k, v]) => acc.replace(`{{${k}}}`, v),
          key,
        );
      }
      return key;
    },
  }),
}));

// Stub IntersectionObserver — not available in jsdom.
const mockObserve = vi.fn();
class MockIntersectionObserver {
  observe = mockObserve;
  disconnect = vi.fn();
  unobserve = vi.fn();
  constructor() {}
}
vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderWithQuery(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={makeQueryClient()}>{ui}</QueryClientProvider>,
  );
}

const SAMPLE_RESPONSE: CardAllocationsResponse = {
  cards: [
    {
      card_id: 1,
      card_name: 'Lightning Bolt',
      image_url: null,
      type_line: 'Instant',
      mana_cost: '{R}',
      quantity: 2,
      decks: [],
    },
    {
      card_id: 2,
      card_name: 'Sol Ring',
      image_url: null,
      type_line: 'Artifact',
      mana_cost: '{1}',
      quantity: 1,
      decks: [{ deck_id: 10, deck_name: 'Commander Deck' }],
    },
  ],
};

const SAMPLE_DECKS: DeckListItem[] = [
  { id: 10, name: 'Commander Deck' },
  { id: 20, name: 'Aggro Deck' },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CardAllocations page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: decks query always resolves with sample decks
    mockGetDecks.mockResolvedValue(SAMPLE_DECKS);
  });

  it('shows a loading spinner while the query is in-flight', () => {
    // Never resolves — keeps the component in loading state
    mockGetCardAllocations.mockReturnValue(new Promise(() => {}));

    renderWithQuery(<CardAllocations />);

    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('renders the correct number of tiles after data loads', async () => {
    mockGetCardAllocations.mockResolvedValue(SAMPLE_RESPONSE);

    renderWithQuery(<CardAllocations />);

    await waitFor(() => {
      // Two tile buttons — one per card in the response.
      // aria-label is "allocations.tileLabel" (mock t() returns key).
      const tiles = screen.getAllByRole('button', { name: /allocations.tileLabel/i });
      expect(tiles).toHaveLength(2);
    });
  });

  it('opens the inspector sidebar for the clicked tile', async () => {
    mockGetCardAllocations.mockResolvedValue(SAMPLE_RESPONSE);

    renderWithQuery(<CardAllocations />);

    // Wait for tiles to appear (aria-label is "allocations.tileLabel" via mock t())
    const tiles = await screen.findAllByRole('button', { name: /allocations.tileLabel/i });
    await userEvent.click(tiles[0]);

    // Inspector sidebar dialog should now be visible
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('shows an informative message for a 501 response (no Postgres)', async () => {
    mockGetCardAllocations.mockRejectedValue(
      new Error('Failed to fetch allocations: 501'),
    );

    renderWithQuery(<CardAllocations />);

    // t() mock returns the i18n key — check for the error key text
    await waitFor(() => {
      expect(screen.getByText(/allocations.errorNoPostgres/i)).toBeInTheDocument();
    });
  });
});
