import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { CardGallery } from '../CardGallery';
import type { Card } from '../../api/client';

// ---------------------------------------------------------------------------
// Mock useImageCache so no real API calls are made
// ---------------------------------------------------------------------------
vi.mock('../../hooks/useImageCache', () => ({
  useImageCache: vi.fn(() => ({ src: 'blob:test', loading: false, error: false })),
}));

// ---------------------------------------------------------------------------
// Mock IntersectionObserver — set tiles as immediately visible
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();

  // IntersectionObserver must be a constructor (regular function, not arrow fn)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).IntersectionObserver = function MockIntersectionObserver(
    callback: IntersectionObserverCallback,
  ) {
    // Call callback synchronously so isVisible becomes true immediately
    callback([{ isIntersecting: true } as IntersectionObserverEntry], this as unknown as IntersectionObserver);
    return {
      observe: vi.fn(),
      disconnect: vi.fn(),
      unobserve: vi.fn(),
      takeRecords: vi.fn(),
      root: null,
      rootMargin: '',
      thresholds: [],
    };
  };

  Element.prototype.scrollIntoView = vi.fn();
});

const MOCK_CARDS: Card[] = [
  { id: 1, name: 'Lightning Bolt', rarity: 'common', type: 'Instant', set_name: 'M10', price: '0.5' },
  { id: 2, name: 'Black Lotus', rarity: 'rare', type: 'Artifact', set_name: 'LEA', price: '25000' },
  { id: 3, name: 'Counterspell', rarity: 'uncommon', type: 'Instant', set_name: 'M10', price: '1.2' },
];

describe('CardGallery', () => {
  it('renders 24 skeleton placeholders when isLoading is true', () => {
    render(<CardGallery cards={[]} isLoading={true} />);
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBe(24);
  });

  it('renders one tile button per card with correct aria-label', () => {
    render(<CardGallery cards={MOCK_CARDS} isLoading={false} />);
    const tiles = screen.getAllByRole('button', { name: /View details for/i });
    expect(tiles).toHaveLength(3);
    expect(tiles[0]).toHaveAttribute('aria-label', 'View details for Lightning Bolt');
    expect(tiles[1]).toHaveAttribute('aria-label', 'View details for Black Lotus');
    expect(tiles[2]).toHaveAttribute('aria-label', 'View details for Counterspell');
  });

  it('calls onRowClick with the correct card when a tile is clicked', async () => {
    const user = userEvent.setup();
    const onRowClick = vi.fn();
    render(<CardGallery cards={MOCK_CARDS} isLoading={false} onRowClick={onRowClick} />);

    const tile = screen.getByRole('button', { name: 'View details for Lightning Bolt' });
    await user.click(tile);

    expect(onRowClick).toHaveBeenCalledOnce();
    expect(onRowClick).toHaveBeenCalledWith(MOCK_CARDS[0]);
  });

  it('shows empty state message when cards array is empty and not loading', () => {
    render(<CardGallery cards={[]} isLoading={false} />);
    expect(
      screen.getByText('No cards found. Try adjusting your filters.'),
    ).toBeInTheDocument();
  });

  it('renders toolbar buttons when corresponding props are provided', () => {
    const onAdd = vi.fn();
    const onImport = vi.fn();
    const onUpdatePrices = vi.fn();
    render(
      <CardGallery
        cards={MOCK_CARDS}
        isLoading={false}
        onAdd={onAdd}
        onImport={onImport}
        onUpdatePrices={onUpdatePrices}
      />,
    );

    expect(screen.getByText('Add card')).toBeInTheDocument();
    expect(screen.getByText('Import list')).toBeInTheDocument();
    expect(screen.getByText('Update Prices')).toBeInTheDocument();
  });

  it('does not render toolbar buttons when props are not provided', () => {
    render(<CardGallery cards={MOCK_CARDS} isLoading={false} />);
    expect(screen.queryByText('Add card')).not.toBeInTheDocument();
  });
});
