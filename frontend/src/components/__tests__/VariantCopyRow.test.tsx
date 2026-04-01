import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { VariantCopyRow } from '../VariantCopyRow';
import type { VariantSlot } from '../../api/client';

// ---------------------------------------------------------------------------
// Sample data helpers
// ---------------------------------------------------------------------------

function makeSlot(overrides: Partial<VariantSlot> = {}): VariantSlot {
  return {
    variant_label: 'Regular',
    finish: 'nonfoil',
    owned: true,
    copies: [
      {
        id: 1,
        finish: 'nonfoil',
        variant_label: 'Regular',
        condition: 'NM',
        quantity: 2,
        price: '0.50',
      },
    ],
    scryfall_image_uri: undefined,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// VariantCopyRow tests
// ---------------------------------------------------------------------------

describe('VariantCopyRow', () => {
  it('renders the variant label pill', () => {
    render(<VariantCopyRow slot={makeSlot({ variant_label: 'Showcase' })} />);
    expect(screen.getByText('Showcase')).toBeInTheDocument();
  });

  it('renders the FinishBadge for foil finish', () => {
    // Use a distinct variant_label so "Foil" badge text is unique in DOM
    render(<VariantCopyRow slot={makeSlot({ finish: 'foil', variant_label: 'Showcase Foil' })} />);
    // The FinishBadge renders "Foil" from variants.finishFoil i18n key
    expect(screen.getByText('Showcase Foil')).toBeInTheDocument(); // label pill
    expect(screen.getByText('Foil')).toBeInTheDocument(); // badge
  });

  it('renders the FinishBadge for etched finish', () => {
    // variant_label "Etched Foil" is distinct from badge text "Etched"
    render(<VariantCopyRow slot={makeSlot({ finish: 'etched', variant_label: 'Etched Foil' })} />);
    expect(screen.getByText('Etched')).toBeInTheDocument();
  });

  it('renders the FinishBadge for nonfoil finish with a distinct label', () => {
    // Use "Borderless" as label so "Regular" badge text is unique in DOM
    render(<VariantCopyRow slot={makeSlot({ finish: 'nonfoil', variant_label: 'Borderless' })} />);
    expect(screen.getByText('Regular')).toBeInTheDocument(); // badge
    expect(screen.getByText('Borderless')).toBeInTheDocument(); // label
  });

  it('shows condition when copy has one', () => {
    const slot = makeSlot();
    render(<VariantCopyRow slot={slot} />);
    expect(screen.getByText('NM')).toBeInTheDocument();
  });

  it('shows quantity when positive', () => {
    const slot = makeSlot();
    render(<VariantCopyRow slot={slot} />);
    expect(screen.getByText('x2')).toBeInTheDocument();
  });

  it('shows price when available', () => {
    const slot = makeSlot();
    render(<VariantCopyRow slot={slot} />);
    expect(screen.getByText('0.50')).toBeInTheDocument();
  });

  it('shows "Not owned" text when slot is not owned', () => {
    const slot = makeSlot({ owned: false, copies: [] });
    render(<VariantCopyRow slot={slot} />);
    expect(screen.getByText('Not owned')).toBeInTheDocument();
  });

  it('applies reduced opacity class when not owned', () => {
    const slot = makeSlot({ owned: false, copies: [] });
    const { container } = render(<VariantCopyRow slot={slot} />);
    const listItem = container.querySelector('[role="listitem"]');
    expect(listItem?.className).toContain('opacity-40');
  });

  it('does NOT apply opacity-40 when owned', () => {
    const slot = makeSlot({ owned: true });
    const { container } = render(<VariantCopyRow slot={slot} />);
    const listItem = container.querySelector('[role="listitem"]');
    expect(listItem?.className).not.toContain('opacity-40');
  });

  it('shows scryfall image when scryfall_image_uri is provided and no firstCopyId', () => {
    const slot = makeSlot({ scryfall_image_uri: 'https://example.com/img.jpg', copies: [] });
    render(<VariantCopyRow slot={slot} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/img.jpg');
  });

  it('uses /api/cards/{id}/image when firstCopyId is provided', () => {
    const slot = makeSlot({ scryfall_image_uri: 'https://example.com/img.jpg' });
    render(<VariantCopyRow slot={slot} firstCopyId={42} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', '/api/cards/42/image');
  });

  it('renders placeholder div when no image source is available', () => {
    const slot = makeSlot({ scryfall_image_uri: undefined, copies: [] });
    const { container } = render(<VariantCopyRow slot={slot} />);
    // No img element should be present; a placeholder div should be rendered instead
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    // The placeholder div exists inside the image area
    const imageArea = container.querySelector('.w-20');
    expect(imageArea?.querySelector('div')).toBeInTheDocument();
  });

  it('sets aria-label when slot is not owned', () => {
    const slot = makeSlot({ owned: false, variant_label: 'Foil', copies: [] });
    const { container } = render(<VariantCopyRow slot={slot} />);
    const listItem = container.querySelector('[role="listitem"]');
    expect(listItem?.getAttribute('aria-label')).toContain('Foil');
  });

  it('does not set aria-label when slot is owned', () => {
    const slot = makeSlot({ owned: true });
    const { container } = render(<VariantCopyRow slot={slot} />);
    const listItem = container.querySelector('[role="listitem"]');
    expect(listItem?.getAttribute('aria-label')).toBeNull();
  });
});
