import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AllocationTile, getAllocationStatus } from '../AllocationTile';
import type { CardAllocation } from '../../api/client';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Stable src to avoid needing a real image fetch in tests
vi.mock('../../hooks/useImageCache', () => ({
  useImageCache: vi.fn(() => ({ src: 'mock-image-url', loading: false, error: false })),
}));

// Stub IntersectionObserver — jsdom does not implement it.
// Must be a proper constructor (class/function) because the component uses `new IntersectionObserver(...)`.
const mockObserve = vi.fn();
const mockDisconnect = vi.fn();
class MockIntersectionObserver {
  observe = mockObserve;
  disconnect = mockDisconnect;
  unobserve = vi.fn();
  constructor() {}
}
vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeAllocation(deckCount: number): CardAllocation {
  return {
    card_id: 1,
    card_name: 'Lightning Bolt',
    image_url: null,
    type_line: 'Instant',
    mana_cost: '{R}',
    quantity: 1,
    decks: Array.from({ length: deckCount }, (_, i) => ({
      deck_id: i + 1,
      deck_name: `Deck ${i + 1}`,
    })),
  };
}

// ---------------------------------------------------------------------------
// getAllocationStatus unit tests
// ---------------------------------------------------------------------------

describe('getAllocationStatus', () => {
  it('returns "available" for 0 decks', () => {
    expect(getAllocationStatus(0)).toBe('available');
  });

  it('returns "assigned" for 1 deck', () => {
    expect(getAllocationStatus(1)).toBe('assigned');
  });

  it('returns "shared" for 3 decks', () => {
    expect(getAllocationStatus(3)).toBe('shared');
  });
});

// ---------------------------------------------------------------------------
// AllocationTile component tests
// ---------------------------------------------------------------------------

describe('AllocationTile', () => {
  const onTileClick = vi.fn();

  beforeEach(() => {
    onTileClick.mockClear();
  });

  it('renders with green badge for "available" status (0 decks)', () => {
    render(
      <AllocationTile allocation={makeAllocation(0)} onTileClick={onTileClick} />,
    );
    const badge = screen.getByRole('button').querySelector('span[aria-hidden="true"]');
    expect(badge?.className).toContain('bg-green-500');
  });

  it('renders with orange badge for "assigned" status (1 deck)', () => {
    render(
      <AllocationTile allocation={makeAllocation(1)} onTileClick={onTileClick} />,
    );
    const badge = screen.getByRole('button').querySelector('span[aria-hidden="true"]');
    expect(badge?.className).toContain('bg-orange-500');
  });

  it('renders with red badge for "shared" status (2+ decks)', () => {
    render(
      <AllocationTile allocation={makeAllocation(2)} onTileClick={onTileClick} />,
    );
    const badge = screen.getByRole('button').querySelector('span[aria-hidden="true"]');
    expect(badge?.className).toContain('bg-red-500');
  });

  it('calls onTileClick with the allocation object when clicked', async () => {
    const allocation = makeAllocation(1);
    render(<AllocationTile allocation={allocation} onTileClick={onTileClick} />);

    await userEvent.click(screen.getByRole('button'));

    expect(onTileClick).toHaveBeenCalledOnce();
    expect(onTileClick).toHaveBeenCalledWith(allocation);
  });
});
