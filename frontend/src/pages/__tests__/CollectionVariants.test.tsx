import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CollectionVariants } from '../CollectionVariants';

// ---------------------------------------------------------------------------
// Mock heavy child component so tests focus on page-level behavior
// ---------------------------------------------------------------------------
vi.mock('../../components/VariantGroupCard', () => ({
  VariantGroupCard: ({ group }: { group: { card_name: string } }) => (
    <div data-testid="variant-group-card">{group.card_name}</div>
  ),
}));

// ---------------------------------------------------------------------------
// Mock useCollectionVariants hook
// ---------------------------------------------------------------------------
const mockUseCollectionVariants = vi.fn();

vi.mock('../../hooks/useApi', () => ({
  useCollectionVariants: (...args: unknown[]) => mockUseCollectionVariants(...args),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeGroup(cardName: string) {
  return {
    card_name: cardName,
    total_known_variants: 2,
    owned_variant_count: 1,
    slots: [],
  };
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <CollectionVariants />
    </QueryClientProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CollectionVariants page', () => {
  beforeEach(() => {
    mockUseCollectionVariants.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page title', () => {
    renderPage();
    expect(screen.getByText('Collection Variants')).toBeInTheDocument();
  });

  it('renders the search input', () => {
    renderPage();
    expect(screen.getByRole('searchbox')).toBeInTheDocument();
  });

  it('shows loading skeletons when isLoading=true', () => {
    mockUseCollectionVariants.mockReturnValue({ data: undefined, isLoading: true, error: null });
    const { container } = renderPage();
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows empty state when collection has no groups', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: { groups: [], total_cards: 0 },
      isLoading: false,
      error: null,
    });
    renderPage();
    expect(screen.getByText('No cards in your collection yet.')).toBeInTheDocument();
  });

  it('renders one VariantGroupCard per group', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: {
        groups: [makeGroup('Lightning Bolt'), makeGroup('Counterspell')],
        total_cards: 2,
      },
      isLoading: false,
      error: null,
    });
    renderPage();
    const cards = screen.getAllByTestId('variant-group-card');
    expect(cards).toHaveLength(2);
  });

  it('renders card names inside VariantGroupCards', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: {
        groups: [makeGroup('Lightning Bolt')],
        total_cards: 1,
      },
      isLoading: false,
      error: null,
    });
    renderPage();
    expect(screen.getByText('Lightning Bolt')).toBeInTheDocument();
  });

  it('shows PostgreSQL notice for 501 error', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('getCollectionVariants failed: 501'),
    });
    renderPage();
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/PostgreSQL/i)).toBeInTheDocument();
  });

  it('shows generic error alert for non-501 errors', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
    });
    renderPage();
    const alerts = screen.getAllByRole('alert');
    expect(alerts.length).toBeGreaterThan(0);
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('does not show empty state when loading', () => {
    mockUseCollectionVariants.mockReturnValue({ data: undefined, isLoading: true, error: null });
    renderPage();
    expect(screen.queryByText('No cards in your collection yet.')).not.toBeInTheDocument();
  });

  it('does not show pagination when total_cards <= PAGE_SIZE', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: { groups: [makeGroup('Lightning Bolt')], total_cards: 1 },
      isLoading: false,
      error: null,
    });
    renderPage();
    // No previous/next buttons should be present
    expect(screen.queryByRole('button', { name: /previous/i })).not.toBeInTheDocument();
  });

  it('shows pagination when total_cards > PAGE_SIZE (50)', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: {
        groups: Array.from({ length: 50 }, (_, i) => makeGroup(`Card ${i}`)),
        total_cards: 100,
      },
      isLoading: false,
      error: null,
    });
    renderPage();
    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });

  it('previous button is disabled on first page', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: {
        groups: Array.from({ length: 50 }, (_, i) => makeGroup(`Card ${i}`)),
        total_cards: 100,
      },
      isLoading: false,
      error: null,
    });
    renderPage();
    const prevButton = screen.getByRole('button', { name: /previous/i });
    expect(prevButton).toBeDisabled();
  });

  it('next button is enabled on first page with more data', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: {
        groups: Array.from({ length: 50 }, (_, i) => makeGroup(`Card ${i}`)),
        total_cards: 100,
      },
      isLoading: false,
      error: null,
    });
    renderPage();
    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).not.toBeDisabled();
  });

  it('calls useCollectionVariants with correct default params', () => {
    renderPage();
    expect(mockUseCollectionVariants).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 50, offset: 0 }),
    );
  });

  it('calls useCollectionVariants without search param when input is empty', () => {
    renderPage();
    const call = mockUseCollectionVariants.mock.calls[0][0];
    expect(call.search).toBeUndefined();
  });

  it('passes page offset when navigating to next page', async () => {
    const user = userEvent.setup();
    mockUseCollectionVariants.mockReturnValue({
      data: {
        groups: Array.from({ length: 50 }, (_, i) => makeGroup(`Card ${i}`)),
        total_cards: 100,
      },
      isLoading: false,
      error: null,
    });
    renderPage();

    await user.click(screen.getByRole('button', { name: /next/i }));

    await waitFor(() => {
      const lastCall = mockUseCollectionVariants.mock.calls[mockUseCollectionVariants.mock.calls.length - 1][0];
      expect(lastCall.offset).toBe(50);
    });
  });

  it('shows page indicator with page number and total pages', () => {
    mockUseCollectionVariants.mockReturnValue({
      data: {
        groups: Array.from({ length: 50 }, (_, i) => makeGroup(`Card ${i}`)),
        total_cards: 100,
      },
      isLoading: false,
      error: null,
    });
    renderPage();
    // e.g. "1 / 2"
    expect(screen.getByText(/1 \/ 2/)).toBeInTheDocument();
  });
});
