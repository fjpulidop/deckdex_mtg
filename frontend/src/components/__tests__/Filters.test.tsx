import { render, screen, act } from '@testing-library/react';
import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, afterEach } from 'vitest';
import { Filters } from '../Filters';

const defaultProps = {
  search: '',
  onSearchChange: vi.fn(),
  rarity: 'all',
  onRarityChange: vi.fn(),
  type: 'all',
  onTypeChange: vi.fn(),
  typeOptions: ['Instant', 'Creature'],
  set: 'all',
  onSetChange: vi.fn(),
  setOptions: ['M10', 'LEA'],
  priceMin: '',
  priceMax: '',
  onPriceRangeChange: vi.fn(),
  colors: [],
  onColorsChange: vi.fn(),
  activeChips: [],
  resultCount: 0,
  onClearFilters: vi.fn(),
};

describe('Filters', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input and rarity select', () => {
    render(<Filters {...defaultProps} />);
    expect(screen.getByPlaceholderText('Search cards by name...')).toBeInTheDocument();
    expect(screen.getByDisplayValue('All Rarities')).toBeInTheDocument();
  });

  it('calls onSearchChange after debounce when typing in search', async () => {
    vi.useFakeTimers();
    const onSearchChange = vi.fn();
    render(<Filters {...defaultProps} onSearchChange={onSearchChange} />);

    const input = screen.getByPlaceholderText('Search cards by name...');
    fireEvent.change(input, { target: { value: 'bolt' } });

    // Advance past the 300ms debounce
    await act(async () => {
      vi.advanceTimersByTime(350);
    });

    expect(onSearchChange).toHaveBeenCalledWith('bolt');
    vi.useRealTimers();
  });

  it('calls onRarityChange when rarity select changes', () => {
    const onRarityChange = vi.fn();
    render(<Filters {...defaultProps} onRarityChange={onRarityChange} />);

    fireEvent.change(screen.getByDisplayValue('All Rarities'), { target: { value: 'common' } });

    expect(onRarityChange).toHaveBeenCalledWith('common');
  });

  it('calls onClearFilters when Clear Filters button is clicked', async () => {
    const user = userEvent.setup();
    const onClearFilters = vi.fn();
    render(<Filters {...defaultProps} onClearFilters={onClearFilters} />);

    await user.click(screen.getByText('Clear Filters'));

    expect(onClearFilters).toHaveBeenCalledOnce();
  });
});
