import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { CardTable } from '../CardTable';
import type { Card } from '../../api/client';

// jsdom doesn't implement scrollIntoView — mock it globally
beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

const MOCK_CARDS: Card[] = [
  { id: 1, name: 'Lightning Bolt', rarity: 'common', type: 'Instant', set_name: 'M10', price: '0.5', created_at: '2024-01-01T00:00:00Z' },
  { id: 2, name: 'Black Lotus', rarity: 'rare', type: 'Artifact', set_name: 'LEA', price: '25000', created_at: '2024-01-02T00:00:00Z' },
  { id: 3, name: 'Counterspell', rarity: 'uncommon', type: 'Instant', set_name: 'M10', price: '1.2', created_at: '2024-01-03T00:00:00Z' },
];

describe('CardTable', () => {
  it('renders an empty tbody when no cards are passed', () => {
    render(<CardTable cards={[]} />);
    const tbody = document.querySelector('tbody')!;
    expect(within(tbody).queryAllByRole('row')).toHaveLength(0);
  });

  it('renders one row per card', () => {
    render(<CardTable cards={MOCK_CARDS} />);
    const tbody = document.querySelector('tbody')!;
    expect(within(tbody).getAllByRole('row')).toHaveLength(3);
  });

  it('renders each card name in the table', () => {
    render(<CardTable cards={MOCK_CARDS} />);
    expect(screen.getByText('Lightning Bolt')).toBeInTheDocument();
    expect(screen.getByText('Black Lotus')).toBeInTheDocument();
    expect(screen.getByText('Counterspell')).toBeInTheDocument();
  });

  it('calls onSortChange with price asc on first Price header click', async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    render(<CardTable cards={MOCK_CARDS} sortBy="created_at" sortDir="desc" onSortChange={onSortChange} />);

    await user.click(screen.getByText(/^Price/));

    expect(onSortChange).toHaveBeenCalledWith('price', 'asc');
  });

  it('calls onSortChange with price desc when already sorting price asc', async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    render(<CardTable cards={MOCK_CARDS} sortBy="price" sortDir="asc" onSortChange={onSortChange} />);

    await user.click(screen.getByText(/^Price/));

    expect(onSortChange).toHaveBeenCalledWith('price', 'desc');
  });

  it('calls onRowClick with the card when a row is clicked', async () => {
    const user = userEvent.setup();
    const onRowClick = vi.fn();
    render(<CardTable cards={MOCK_CARDS} onRowClick={onRowClick} />);

    const rows = within(document.querySelector('tbody')!).getAllByRole('row');
    await user.click(rows[0]);

    expect(onRowClick).toHaveBeenCalledOnce();
  });
});
