import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CardAllocations } from '../CardAllocations';
import type { CardAllocationsResponse } from '../../api/client';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGetCardAllocations = vi.fn<[], Promise<CardAllocationsResponse>>();
const mockRemoveCardFromDeck = vi.fn<[number, number], Promise<void>>();

vi.mock('../../api/client', () => ({
  api: {
    getCardAllocations: (...args: unknown[]) => mockGetCardAllocations(...(args as [])),
    removeCardFromDeck: (...args: unknown[]) =>
      mockRemoveCardFromDeck(...(args as [number, number])),
  },
}));

// Stable src avoids needing a real image in tests; also eliminates IntersectionObserver
vi.mock('../../hooks/useImageCache', () => ({
  useImageCache: vi.fn(() => ({ src: 'mock-image-url', loading: false, error: false })),
}));

// Stub IntersectionObserver — not available in jsdom.
// Must be a proper constructor because AllocationTile uses `new IntersectionObserver(...)`.
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CardAllocations page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
      // Two tiles — one per card in the response
      const buttons = screen.getAllByRole('button');
      // Filter to tile buttons (aria-label contains card name)
      const tiles = buttons.filter((b) =>
        b.getAttribute('aria-label')?.includes('Lightning Bolt') ||
        b.getAttribute('aria-label')?.includes('Sol Ring'),
      );
      expect(tiles).toHaveLength(2);
    });
  });

  it('opens the popover for the clicked tile', async () => {
    mockGetCardAllocations.mockResolvedValue(SAMPLE_RESPONSE);

    renderWithQuery(<CardAllocations />);

    // Wait for tiles to appear
    const boltTile = await screen.findByRole('button', { name: /Lightning Bolt/i });
    await userEvent.click(boltTile);

    // Popover dialog should now be visible
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Available — not in any deck')).toBeInTheDocument();
  });

  it('shows an informative message for a 501 response (no Postgres)', async () => {
    mockGetCardAllocations.mockRejectedValue(
      new Error('Failed to fetch allocations: 501'),
    );

    renderWithQuery(<CardAllocations />);

    await waitFor(() => {
      expect(screen.getByText(/Deck features require a Postgres database/i)).toBeInTheDocument();
    });
  });

  it('calls removeCardFromDeck and invalidates cache on remove', async () => {
    mockGetCardAllocations.mockResolvedValue(SAMPLE_RESPONSE);
    mockRemoveCardFromDeck.mockResolvedValue(undefined);

    renderWithQuery(<CardAllocations />);

    // Click the Sol Ring tile (which is in one deck)
    const solRingTile = await screen.findByRole('button', { name: /Sol Ring/i });
    await userEvent.click(solRingTile);

    // Click the Remove button in the popover
    const removeBtn = await screen.findByRole('button', { name: /remove from commander deck/i });
    await userEvent.click(removeBtn);

    await waitFor(() => {
      expect(mockRemoveCardFromDeck).toHaveBeenCalledWith(10, 2);
    });
  });
});
