import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AllocationDropZone } from '../AllocationDropZone';
import type { DeckListItem } from '../../api/client';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// react-i18next stub — returns the key (with {{}} interpolation) as translation
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

// Stub DeckDropTarget so its internals (useDroppable, etc.) are not exercised.
// We still verify it receives the correct deck prop.
vi.mock('../DeckDropTarget', () => ({
  DeckDropTarget: vi.fn(({ deck }: { deck: DeckListItem }) => (
    <div data-testid="deck-drop-target" data-deck-id={deck.id}>
      {deck.name}
    </div>
  )),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeDecks(count: number): DeckListItem[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Deck ${i + 1}`,
  }));
}

function renderZone(decks: DeckListItem[], isLoading: boolean) {
  return render(<AllocationDropZone decks={decks} isLoading={isLoading} />);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AllocationDropZone', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // Loading state
  // -------------------------------------------------------------------------

  it('renders skeleton placeholders when isLoading=true', () => {
    renderZone(makeDecks(5), true);
    // Three animate-pulse skeleton divs shown during loading
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBe(3);
  });

  it('does not render DeckDropTarget components while loading', () => {
    renderZone(makeDecks(5), true);
    expect(screen.queryAllByTestId('deck-drop-target')).toHaveLength(0);
  });

  it('does not show "no decks" message when loading', () => {
    renderZone([], true);
    // The empty-state message key should not appear
    expect(screen.queryByText('allocations.noDecks')).not.toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Empty state
  // -------------------------------------------------------------------------

  it('shows "no decks" message when not loading and decks is empty', () => {
    renderZone([], false);
    expect(screen.getByText('allocations.noDecks')).toBeInTheDocument();
  });

  it('does not render DeckDropTarget components when decks is empty', () => {
    renderZone([], false);
    expect(screen.queryAllByTestId('deck-drop-target')).toHaveLength(0);
  });

  // -------------------------------------------------------------------------
  // Populated state
  // -------------------------------------------------------------------------

  it('renders one DeckDropTarget per deck', () => {
    renderZone(makeDecks(3), false);
    const targets = screen.getAllByTestId('deck-drop-target');
    expect(targets).toHaveLength(3);
  });

  it('passes the correct deck to each DeckDropTarget', () => {
    renderZone(makeDecks(2), false);
    const targets = screen.getAllByTestId('deck-drop-target');
    expect(targets[0]).toHaveAttribute('data-deck-id', '1');
    expect(targets[1]).toHaveAttribute('data-deck-id', '2');
    expect(targets[0]).toHaveTextContent('Deck 1');
    expect(targets[1]).toHaveTextContent('Deck 2');
  });

  it('does not show "no decks" message when decks are present', () => {
    renderZone(makeDecks(2), false);
    expect(screen.queryByText('allocations.noDecks')).not.toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Accessibility and region labelling
  // -------------------------------------------------------------------------

  it('renders a region with the correct aria-label', () => {
    renderZone(makeDecks(1), false);
    expect(
      screen.getByRole('region', { name: 'allocations.dropZoneLabel' }),
    ).toBeInTheDocument();
  });

  it('shows the drag instruction text', () => {
    renderZone(makeDecks(1), false);
    expect(screen.getByText('allocations.dragToAdd')).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Edge cases
  // -------------------------------------------------------------------------

  it('renders correctly with a single deck', () => {
    renderZone(makeDecks(1), false);
    const targets = screen.getAllByTestId('deck-drop-target');
    expect(targets).toHaveLength(1);
    expect(targets[0]).toHaveTextContent('Deck 1');
  });

  it('renders a large number of decks without error', () => {
    renderZone(makeDecks(20), false);
    expect(screen.getAllByTestId('deck-drop-target')).toHaveLength(20);
  });

  it('transitions from loading to loaded without crashing', () => {
    const { rerender } = renderZone(makeDecks(2), true);
    // While loading: skeletons
    expect(document.querySelectorAll('.animate-pulse').length).toBe(3);

    rerender(<AllocationDropZone decks={makeDecks(2)} isLoading={false} />);
    // After load: actual targets
    expect(screen.getAllByTestId('deck-drop-target')).toHaveLength(2);
    expect(document.querySelectorAll('.animate-pulse').length).toBe(0);
  });
});
