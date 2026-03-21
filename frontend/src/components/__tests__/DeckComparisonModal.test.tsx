import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeckComparisonModal } from '../DeckComparisonModal';
import type { DeckComparisonResponse } from '../../api/client';

vi.mock('../../contexts/ThemeContext', () => ({
  useTheme: () => ({ theme: 'dark', toggleTheme: vi.fn() }),
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockCompareDecks = vi.hoisted(() => vi.fn());

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
  Tooltip: () => null,
}));

vi.mock('../../api/client', () => ({
  api: {
    compareDecks: mockCompareDecks,
    getDecks: vi.fn().mockResolvedValue([]),
  },
}));

// ---------------------------------------------------------------------------
// Sample data
// ---------------------------------------------------------------------------

const SAMPLE_DECKS = [
  { id: 1, name: 'Deck Alpha', card_count: 60 },
  { id: 2, name: 'Deck Beta', card_count: 40 },
];

const MOCK_COMPARISON_RESPONSE: DeckComparisonResponse = {
  deck_ids: [1, 2],
  decks: [
    {
      deck_id: 1,
      deck_name: 'Deck Alpha',
      total_cards: 60,
      total_value: 45.0,
      creature_count: 12,
      instant_count: 8,
      mana_curve: [
        { cmc: '0', count: 0 },
        { cmc: '1', count: 10 },
        { cmc: '2', count: 20 },
        { cmc: '3', count: 15 },
        { cmc: '4', count: 10 },
        { cmc: '5', count: 3 },
        { cmc: '6', count: 2 },
        { cmc: '7+', count: 0 },
      ],
      color_distribution: [
        { color: 'W', count: 0 },
        { color: 'U', count: 0 },
        { color: 'B', count: 0 },
        { color: 'R', count: 60 },
        { color: 'G', count: 0 },
        { color: 'C', count: 0 },
      ],
    },
    {
      deck_id: 2,
      deck_name: 'Deck Beta',
      total_cards: 40,
      total_value: 25.0,
      creature_count: 8,
      instant_count: 6,
      mana_curve: [
        { cmc: '0', count: 0 },
        { cmc: '1', count: 8 },
        { cmc: '2', count: 12 },
        { cmc: '3', count: 10 },
        { cmc: '4', count: 6 },
        { cmc: '5', count: 2 },
        { cmc: '6', count: 2 },
        { cmc: '7+', count: 0 },
      ],
      color_distribution: [
        { color: 'W', count: 0 },
        { color: 'U', count: 40 },
        { color: 'B', count: 0 },
        { color: 'R', count: 0 },
        { color: 'G', count: 0 },
        { color: 'C', count: 0 },
      ],
    },
  ],
  overlap_cards: [],
};

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function renderModal(onClose = vi.fn()) {
  return render(
    <QueryClientProvider client={makeQueryClient()}>
      <DeckComparisonModal decks={SAMPLE_DECKS} onClose={onClose} />
    </QueryClientProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DeckComparisonModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCompareDecks.mockResolvedValue(MOCK_COMPARISON_RESPONSE);
  });

  it('renders DeckMultiSelect on open', () => {
    renderModal();

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Select Decks to Compare')).toBeInTheDocument();
  });

  it('disables Compare button when fewer than 2 decks selected', () => {
    renderModal();

    const compareBtn = screen.getByRole('button', { name: /compare$/i });
    expect(compareBtn).toBeDisabled();
  });

  it('enables Compare button when 2 decks selected', () => {
    renderModal();

    // Click on first deck
    fireEvent.click(screen.getByRole('checkbox', { name: /Deck Alpha/i }));
    // Click on second deck
    fireEvent.click(screen.getByRole('checkbox', { name: /Deck Beta/i }));

    const compareBtn = screen.getByRole('button', { name: /^compare$/i });
    expect(compareBtn).not.toBeDisabled();
  });

  it('transitions to ComparisonView on confirm', async () => {
    renderModal();

    fireEvent.click(screen.getByRole('checkbox', { name: /Deck Alpha/i }));
    fireEvent.click(screen.getByRole('checkbox', { name: /Deck Beta/i }));
    fireEvent.click(screen.getByRole('button', { name: /^compare$/i }));

    // After clicking compare, the comparison title should appear
    await waitFor(() => {
      expect(screen.getByText('Compare Decks')).toBeInTheDocument();
    });
  });

  it('calls onClose when X button is clicked', () => {
    const onClose = vi.fn();
    renderModal(onClose);

    const closeBtn = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeBtn);

    expect(onClose).toHaveBeenCalledOnce();
  });
});
