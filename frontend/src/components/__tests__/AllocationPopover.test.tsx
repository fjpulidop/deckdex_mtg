import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AllocationPopover } from '../AllocationPopover';
import type { CardAllocation } from '../../api/client';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeAllocation(deckCount: number): CardAllocation {
  return {
    card_id: 42,
    card_name: 'Sol Ring',
    image_url: null,
    type_line: 'Artifact',
    mana_cost: '{1}',
    quantity: 1,
    decks: Array.from({ length: deckCount }, (_, i) => ({
      deck_id: i + 10,
      deck_name: `Deck ${String.fromCharCode(65 + i)}`, // Deck A, Deck B, ...
    })),
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AllocationPopover', () => {
  const onRemoveFromDeck = vi.fn();
  const onClose = vi.fn();

  beforeEach(() => {
    onRemoveFromDeck.mockClear();
    onClose.mockClear();
  });

  it('renders "Available — not in any deck" when decks array is empty', () => {
    render(
      <AllocationPopover
        allocation={makeAllocation(0)}
        onRemoveFromDeck={onRemoveFromDeck}
        onClose={onClose}
      />,
    );

    expect(screen.getByText('Available — not in any deck')).toBeInTheDocument();
  });

  it('renders deck name(s) when allocation has entries', () => {
    render(
      <AllocationPopover
        allocation={makeAllocation(2)}
        onRemoveFromDeck={onRemoveFromDeck}
        onClose={onClose}
      />,
    );

    expect(screen.getByText('Deck A')).toBeInTheDocument();
    expect(screen.getByText('Deck B')).toBeInTheDocument();
  });

  it('calls onRemoveFromDeck with correct (deckId, cardId) when Remove is clicked', async () => {
    const allocation = makeAllocation(1);
    render(
      <AllocationPopover
        allocation={allocation}
        onRemoveFromDeck={onRemoveFromDeck}
        onClose={onClose}
      />,
    );

    await userEvent.click(screen.getByRole('button', { name: /remove from deck a/i }));

    expect(onRemoveFromDeck).toHaveBeenCalledOnce();
    expect(onRemoveFromDeck).toHaveBeenCalledWith(10, 42); // deck_id=10, card_id=42
  });

  it('calls onClose when the close button is clicked', async () => {
    render(
      <AllocationPopover
        allocation={makeAllocation(0)}
        onRemoveFromDeck={onRemoveFromDeck}
        onClose={onClose}
      />,
    );

    await userEvent.click(screen.getByRole('button', { name: /close/i }));

    expect(onClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when Escape key is pressed', async () => {
    render(
      <AllocationPopover
        allocation={makeAllocation(0)}
        onRemoveFromDeck={onRemoveFromDeck}
        onClose={onClose}
      />,
    );

    await userEvent.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledOnce();
  });

  it('has role="dialog" on the root element', () => {
    render(
      <AllocationPopover
        allocation={makeAllocation(1)}
        onRemoveFromDeck={onRemoveFromDeck}
        onClose={onClose}
      />,
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
