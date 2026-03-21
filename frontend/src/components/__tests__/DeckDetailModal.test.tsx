import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeckDetailModal } from '../DeckDetailModal';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../../hooks/useCardImage', () => ({
  useCardImage: vi.fn(() => ({ src: null, loading: false, error: false })),
}));

vi.mock('../../api/client', () => ({
  api: {
    getDeck: vi.fn(() =>
      Promise.resolve({
        id: 1,
        name: 'Test Deck',
        card_count: 0,
        commander_card_id: null,
        cards: [],
      }),
    ),
  },
}));

// Mock recharts — renders no SVG in jsdom; the wrapper div still renders normally
vi.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  Cell: () => null,
}));

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function renderWithQuery(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={makeQueryClient()}>{ui}</QueryClientProvider>,
  );
}

// ---------------------------------------------------------------------------
// Mana curve dark mode structural tests
// ---------------------------------------------------------------------------

describe('DeckDetailModal mana curve dark mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('mana curve wrapper carries dark:text-gray-200 class for currentColor inheritance', () => {
    renderWithQuery(
      <DeckDetailModal deckId={1} onClose={() => {}} onDeleted={() => {}} />,
    );

    // The wrapper div with class "deck-detail-mana-curve" must be present
    const curveWrapper = document.querySelector('.deck-detail-mana-curve');
    expect(curveWrapper).not.toBeNull();

    // It must carry dark:text-gray-200 so SVG currentColor resolves to light gray in dark mode
    expect(curveWrapper?.className).toContain('dark:text-gray-200');
  });
});

// ---------------------------------------------------------------------------
// Mobile remove button visibility tests
// ---------------------------------------------------------------------------

// Import the mocked api module to allow per-test overrides
import { api as mockApi } from '../../api/client';

describe('DeckDetailModal mobile remove button', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();

    // Override getDeck to return a deck with one card so the remove button renders
    (mockApi.getDeck as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      name: 'Test Deck',
      card_count: 1,
      commander_card_id: null,
      cards: [
        {
          id: 42,
          name: 'Lightning Bolt',
          type: 'Instant',
          quantity: 1,
          is_commander: false,
        },
      ],
    });
  });

  it('remove button uses sm:opacity-0 sm:group-hover:opacity-100 (not unconditional opacity-0)', async () => {
    renderWithQuery(
      <DeckDetailModal deckId={1} onClose={() => {}} onDeleted={() => {}} />,
    );

    // Wait for the card to appear
    const removeBtn = await screen.findByLabelText('Remove Lightning Bolt');
    expect(removeBtn).toBeTruthy();

    // The button should NOT have unconditional opacity-0 — it must be sm:opacity-0
    expect(removeBtn.className).not.toMatch(/\bopacity-0\b(?!.*sm:)/);
    expect(removeBtn.className).toContain('sm:opacity-0');
  });
});
