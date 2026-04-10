import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { VariantGroupCard } from '../VariantGroupCard';
import type { CardVariantGroup } from '../../api/client';

// ---------------------------------------------------------------------------
// Sample data helpers
// ---------------------------------------------------------------------------

function makeGroup(overrides: Partial<CardVariantGroup> = {}): CardVariantGroup {
  return {
    card_name: 'Lightning Bolt',
    total_known_variants: 3,
    owned_variant_count: 1,
    slots: [
      {
        variant_label: 'Regular',
        finish: 'nonfoil',
        owned: true,
        copies: [{ id: 1, finish: 'nonfoil', variant_label: 'Regular', quantity: 1 }],
      },
      {
        variant_label: 'Foil',
        finish: 'foil',
        owned: false,
        copies: [],
      },
      {
        variant_label: 'Showcase',
        finish: 'nonfoil',
        owned: false,
        copies: [],
      },
    ],
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// VariantGroupCard tests
// ---------------------------------------------------------------------------

describe('VariantGroupCard', () => {
  it('renders the card name', () => {
    render(<VariantGroupCard group={makeGroup()} />);
    expect(screen.getByText('Lightning Bolt')).toBeInTheDocument();
  });

  it('renders variants owned summary text', () => {
    render(<VariantGroupCard group={makeGroup({ owned_variant_count: 1, total_known_variants: 3 })} />);
    // Should contain "1 of 3 variants" or similar
    expect(screen.getByText(/1 of 3 variants/i)).toBeInTheDocument();
  });

  it('renders a progressbar element', () => {
    render(<VariantGroupCard group={makeGroup()} />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('sets progressbar aria-valuenow to owned_variant_count', () => {
    render(<VariantGroupCard group={makeGroup({ owned_variant_count: 2, total_known_variants: 5 })} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '2');
  });

  it('sets progressbar aria-valuemax to total_known_variants', () => {
    render(<VariantGroupCard group={makeGroup({ owned_variant_count: 2, total_known_variants: 5 })} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuemax', '5');
  });

  it('is collapsed by default (slots not visible)', () => {
    render(<VariantGroupCard group={makeGroup()} />);
    // The body div has max-h-0 class when collapsed
    const body = screen.getByRole('button').closest('article')?.querySelector('[id$="-body"]');
    expect(body?.className).toContain('max-h-0');
  });

  it('expands when header button is clicked', async () => {
    const user = userEvent.setup();
    render(<VariantGroupCard group={makeGroup()} />);
    const button = screen.getByRole('button');

    await user.click(button);

    const body = button.closest('article')?.querySelector('[id$="-body"]');
    expect(body?.className).toContain('max-h-[2000px]');
  });

  it('sets aria-expanded=false on header button when collapsed', () => {
    render(<VariantGroupCard group={makeGroup()} />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('sets aria-expanded=true after expanding', async () => {
    const user = userEvent.setup();
    render(<VariantGroupCard group={makeGroup()} />);
    const button = screen.getByRole('button');

    await user.click(button);

    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('collapses again when header button is clicked twice', async () => {
    const user = userEvent.setup();
    render(<VariantGroupCard group={makeGroup()} />);
    const button = screen.getByRole('button');

    await user.click(button);
    await user.click(button);

    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('renders expanded by default when defaultExpanded=true', () => {
    render(<VariantGroupCard group={makeGroup()} defaultExpanded />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('renders one list item per slot in expanded state', async () => {
    const user = userEvent.setup();
    const { container } = render(<VariantGroupCard group={makeGroup()} />);

    await user.click(screen.getByRole('button'));

    // Count <li> elements directly (VariantCopyRow also adds role="listitem" divs,
    // so getAllByRole would double-count)
    const liElements = container.querySelectorAll('ul > li');
    expect(liElements).toHaveLength(3);
  });

  it('shows 0% progress bar fill when nothing is owned', () => {
    const group = makeGroup({ owned_variant_count: 0, total_known_variants: 5 });
    const { container } = render(<VariantGroupCard group={group} />);
    const progressFill = container.querySelector('[style*="width"]') as HTMLElement;
    expect(progressFill?.style.width).toBe('0%');
  });

  it('shows 100% progress bar fill when everything is owned', () => {
    const group = makeGroup({ owned_variant_count: 3, total_known_variants: 3 });
    const { container } = render(<VariantGroupCard group={group} />);
    const progressFill = container.querySelector('[style*="width"]') as HTMLElement;
    expect(progressFill?.style.width).toBe('100%');
  });

  it('renders a toggle button accessible by role', () => {
    render(<VariantGroupCard group={makeGroup()} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('uses card name for the header id (slug format)', () => {
    const { container } = render(<VariantGroupCard group={makeGroup({ card_name: 'Black Lotus' })} />);
    const button = container.querySelector('button');
    expect(button?.id).toContain('black-lotus');
  });
});
