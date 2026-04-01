import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { DraggableTile } from '../DraggableTile';
import type { CardAllocation } from '../../api/client';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock @dnd-kit/core so tests don't need a real DndContext.
// useDraggable returns stable stubs; transform=null means no inline style applied.
vi.mock('@dnd-kit/core', () => ({
  useDraggable: vi.fn(() => ({
    attributes: { role: 'button', tabIndex: 0 },
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    isDragging: false,
  })),
}));

vi.mock('@dnd-kit/utilities', () => ({
  CSS: {
    Translate: {
      toString: vi.fn((t) => `translate3d(${t.x}px, ${t.y}px, 0)`),
    },
  },
}));

// Stub AllocationTile so we can assert through its aria-label without
// needing IntersectionObserver or real image loading.
vi.mock('../AllocationTile', () => ({
  AllocationTile: vi.fn(({ allocation, onTileClick, isDragging }) => (
    <button
      data-testid="allocation-tile"
      data-card-id={allocation.card_id}
      data-is-dragging={String(isDragging)}
      onClick={() => onTileClick(allocation)}
    >
      {allocation.card_name}
    </button>
  )),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeAllocation(overrides: Partial<CardAllocation> = {}): CardAllocation {
  return {
    card_id: 1,
    card_name: 'Lightning Bolt',
    image_url: null,
    type_line: 'Instant',
    mana_cost: '{R}',
    quantity: 2,
    decks: [],
    ...overrides,
  };
}

function renderTile(
  allocation: CardAllocation = makeAllocation(),
  onTileClick: (a: CardAllocation) => void = vi.fn(),
) {
  return render(<DraggableTile allocation={allocation} onTileClick={onTileClick} />);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DraggableTile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the inner AllocationTile', () => {
    renderTile();
    expect(screen.getByTestId('allocation-tile')).toBeInTheDocument();
  });

  it('passes allocation to AllocationTile', () => {
    const allocation = makeAllocation({ card_id: 42, card_name: 'Sol Ring' });
    renderTile(allocation);
    const tile = screen.getByTestId('allocation-tile');
    expect(tile).toHaveAttribute('data-card-id', '42');
    expect(tile).toHaveTextContent('Sol Ring');
  });

  it('calls onTileClick when the inner tile is clicked', async () => {
    const onTileClick = vi.fn();
    const allocation = makeAllocation();
    renderTile(allocation, onTileClick);

    await userEvent.click(screen.getByTestId('allocation-tile'));

    expect(onTileClick).toHaveBeenCalledOnce();
    expect(onTileClick).toHaveBeenCalledWith(allocation);
  });

  it('passes isDragging=false to AllocationTile when not dragging', () => {
    renderTile();
    const tile = screen.getByTestId('allocation-tile');
    expect(tile).toHaveAttribute('data-is-dragging', 'false');
  });

  it('passes isDragging=true to AllocationTile when dragging', async () => {
    // Re-configure useDraggable mock to report isDragging=true for this test
    const { useDraggable } = await import('@dnd-kit/core');
    vi.mocked(useDraggable).mockReturnValueOnce({
      attributes: { role: 'button', tabIndex: 0 },
      listeners: {},
      setNodeRef: vi.fn(),
      transform: null,
      isDragging: true,
    } as unknown as ReturnType<typeof useDraggable>);

    renderTile();
    const tile = screen.getByTestId('allocation-tile');
    expect(tile).toHaveAttribute('data-is-dragging', 'true');
  });

  it('applies transform style when useDraggable returns a transform', async () => {
    const { useDraggable } = await import('@dnd-kit/core');
    vi.mocked(useDraggable).mockReturnValueOnce({
      attributes: { role: 'button', tabIndex: 0 },
      listeners: {},
      setNodeRef: vi.fn(),
      transform: { x: 10, y: 20, scaleX: 1, scaleY: 1 },
      isDragging: true,
    } as unknown as ReturnType<typeof useDraggable>);

    const { container } = renderTile();
    // The wrapper div should have an inline style when transform is non-null
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.style.transform).not.toBe('');
  });

  it('does not apply a transform style when transform is null', () => {
    const { container } = renderTile();
    const wrapper = container.firstChild as HTMLElement;
    // style.transform should be empty string (no inline style set)
    expect(wrapper.style.transform).toBe('');
  });

  it('calls useDraggable with the card_id as the draggable id', async () => {
    const { useDraggable } = await import('@dnd-kit/core');
    const allocation = makeAllocation({ card_id: 77 });
    renderTile(allocation);

    const lastCall = vi.mocked(useDraggable).mock.calls.at(-1)!;
    expect(lastCall[0].id).toBe(77);
  });

  it('passes data.type="card" and data.allocation to useDraggable', async () => {
    const { useDraggable } = await import('@dnd-kit/core');
    const allocation = makeAllocation({ card_id: 55 });
    renderTile(allocation);

    const lastCall = vi.mocked(useDraggable).mock.calls.at(-1)!;
    expect(lastCall[0].data).toMatchObject({ type: 'card', allocation });
  });
});
