import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { CardInspectorSidebar } from '../CardInspectorSidebar';
import type { CardAllocation, DeckListItem } from '../../api/client';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../../hooks/useImageCache', () => ({
  useImageCache: vi.fn(() => ({ src: null, loading: false, error: false })),
}));

// react-i18next mock — returns the key as the translation value
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeAllocation(deckCount: number): CardAllocation {
  return {
    card_id: 1,
    card_name: 'Sol Ring',
    image_url: null,
    type_line: 'Artifact',
    mana_cost: '{0}',
    quantity: 1,
    decks: Array.from({ length: deckCount }, (_, i) => ({
      deck_id: i + 1,
      deck_name: i === 0 ? 'Atraxa' : `Deck ${i + 1}`,
    })),
  };
}

function makeDecks(count: number): DeckListItem[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: i === 0 ? 'Atraxa' : `Deck ${i + 1}`,
  }));
}

const defaultProps = {
  onAddToDeck: vi.fn(),
  onRemoveFromDeck: vi.fn(),
  onRemoveFromAll: vi.fn(),
  onClose: vi.fn(),
  isPending: false,
};

function renderSidebar(
  allocation: CardAllocation,
  allDecks: DeckListItem[],
  overrides: Partial<typeof defaultProps> = {},
) {
  const props = { ...defaultProps, ...overrides };
  return render(
    <CardInspectorSidebar
      allocation={allocation}
      allDecks={allDecks}
      onAddToDeck={props.onAddToDeck}
      onRemoveFromDeck={props.onRemoveFromDeck}
      onRemoveFromAll={props.onRemoveFromAll}
      onClose={props.onClose}
      isPending={props.isPending}
    />,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CardInspectorSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders card name and type line', () => {
    renderSidebar(makeAllocation(0), makeDecks(0));
    expect(screen.getByText('Sol Ring')).toBeInTheDocument();
    expect(screen.getByText('Artifact')).toBeInTheDocument();
  });

  it('shows "In these decks" section when card has deck assignments', () => {
    renderSidebar(makeAllocation(1), makeDecks(2));
    // The heading key as returned by our mock t()
    expect(screen.getByText('allocations.inTheseDecks')).toBeInTheDocument();
    // Deck name should appear in the list
    expect(screen.getByText('Atraxa')).toBeInTheDocument();
  });

  it('shows "Add to deck" section for decks not containing the card', () => {
    const allocation = makeAllocation(1); // in deck 1 (Atraxa)
    const allDecks = makeDecks(2); // decks 1 and 2
    renderSidebar(allocation, allDecks);
    // Deck 2 should appear in "Add to deck" section
    expect(screen.getByText('Deck 2')).toBeInTheDocument();
    // "Add to deck" heading should be present (the h3 element)
    const headings = screen.getAllByText('allocations.addToDeck');
    expect(headings.length).toBeGreaterThanOrEqual(1);
  });

  it('"Remove from all" button is disabled when allocation.decks is empty', () => {
    renderSidebar(makeAllocation(0), makeDecks(2));
    const btn = screen.getByRole('button', { name: /removeFromAllLabel/i });
    expect(btn).toBeDisabled();
  });

  it('"Remove from all" button is enabled when card is in decks', () => {
    renderSidebar(makeAllocation(1), makeDecks(1));
    const btn = screen.getByRole('button', { name: /removeFromAllLabel/i });
    expect(btn).not.toBeDisabled();
  });

  it('calls onClose when Escape key is pressed', () => {
    const onClose = vi.fn();
    renderSidebar(makeAllocation(0), makeDecks(0), { onClose });
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('disables all action buttons when isPending is true', () => {
    const allocation = makeAllocation(1);
    const allDecks = makeDecks(2);
    renderSidebar(allocation, allDecks, { isPending: true });

    // All buttons (Remove, Add to deck buttons, Remove from all)
    const buttons = screen.getAllByRole('button');
    // The close button (X) should not be disabled — filter action buttons
    const actionButtons = buttons.filter(
      (btn) => btn.getAttribute('aria-label') !== 'allocations.close',
    );
    actionButtons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });
});
