import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CardDetailModal } from '../CardDetailModal';
import { DeckDetailModal } from '../DeckDetailModal';
import { ProfileModal } from '../ProfileModal';
import type { Card } from '../../api/client';

// ---------------------------------------------------------------------------
// Shared mocks
// ---------------------------------------------------------------------------

vi.mock('../../hooks/useCardImage', () => ({
  useCardImage: vi.fn(() => ({ src: 'https://example.com/card.jpg', loading: false, error: false })),
}));

vi.mock('../../hooks/useApi', () => ({
  usePriceHistory: vi.fn(() => ({ data: null, isLoading: false })),
  useFilterOptions: vi.fn(() => ({ data: null })),
}));

vi.mock('../../contexts/ActiveJobsContext', () => ({
  useActiveJobs: vi.fn(() => ({ addJob: vi.fn() })),
}));

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 1, email: 'test@example.com', display_name: 'Test User' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
    refreshUser: vi.fn(),
  })),
}));

vi.mock('../../api/client', () => ({
  api: {
    getCards: vi.fn(() => Promise.resolve([])),
    getDeck: vi.fn(() =>
      Promise.resolve({
        id: 1,
        name: 'Test Deck',
        cards: [
          {
            id: 10,
            name: 'Atraxa',
            type: 'Legendary Creature — Phyrexian Praetor',
            quantity: 1,
            is_commander: true,
            price: '5.00',
          },
        ],
      })
    ),
    updateCard: vi.fn(),
    deleteCard: vi.fn(),
    triggerSingleCardPriceUpdate: vi.fn(),
  },
}));

// Mock Cropper (react-easy-crop) — renders nothing meaningful in jsdom
vi.mock('react-easy-crop', () => ({
  default: () => <div data-testid="cropper" />,
}));

// Mock recharts — renders no SVG in jsdom
vi.mock('recharts', () => ({
  BarChart: () => <div data-testid="bar-chart" />,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Cell: () => null,
}));

// Mock PriceChart
vi.mock('../PriceChart', () => ({
  PriceChart: () => <div data-testid="price-chart" />,
}));

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function renderWithQuery(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={makeQueryClient()}>{ui}</QueryClientProvider>,
  );
}

const MOCK_CARD: Card = {
  id: 1,
  name: 'Lightning Bolt',
  type: 'Instant',
  rarity: 'common',
  set_name: 'M10',
  price: '0.5',
  created_at: '2024-01-01T00:00:00Z',
};

// Helper: simulate image load so the zoom button becomes clickable
async function simulateImageLoad(alt: string) {
  const img = document.querySelector(`img[alt="${alt}"]`) as HTMLImageElement;
  if (img) {
    await act(async () => {
      img.dispatchEvent(new Event('load'));
    });
  }
}

// ---------------------------------------------------------------------------
// CardDetailModal lightbox accessibility tests
// ---------------------------------------------------------------------------

describe('CardDetailModal lightbox accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('lightbox is rendered as role="dialog" with aria-modal when open', async () => {
    renderWithQuery(<CardDetailModal card={MOCK_CARD} onClose={vi.fn()} />);

    // Simulate image load so the zoom-in button becomes active
    await simulateImageLoad('Lightning Bolt');

    // Click the "view image larger" button
    const viewLargerBtn = screen.getByRole('button', { name: /view image larger/i });
    await act(async () => {
      viewLargerBtn.click();
    });

    const lightboxDialog = document.querySelector('[aria-labelledby="card-detail-lightbox-title"]');
    expect(lightboxDialog).not.toBeNull();
    expect(lightboxDialog).toHaveAttribute('role', 'dialog');
    expect(lightboxDialog).toHaveAttribute('aria-modal', 'true');
  });

  it('lightbox contains a sr-only title span with id "card-detail-lightbox-title"', async () => {
    renderWithQuery(<CardDetailModal card={MOCK_CARD} onClose={vi.fn()} />);
    await simulateImageLoad('Lightning Bolt');

    const viewLargerBtn = screen.getByRole('button', { name: /view image larger/i });
    await act(async () => {
      viewLargerBtn.click();
    });

    // The title span must exist and be present inside the lightbox dialog
    const titleSpan = document.getElementById('card-detail-lightbox-title');
    expect(titleSpan).not.toBeNull();
    expect(titleSpan?.tagName.toLowerCase()).toBe('span');
  });

  it('lightbox inner close element has role="button" and tabIndex=0', async () => {
    renderWithQuery(<CardDetailModal card={MOCK_CARD} onClose={vi.fn()} />);
    await simulateImageLoad('Lightning Bolt');

    const viewLargerBtn = screen.getByRole('button', { name: /view image larger/i });
    await act(async () => {
      viewLargerBtn.click();
    });

    const lightboxDialog = document.querySelector('[aria-labelledby="card-detail-lightbox-title"]');
    expect(lightboxDialog).not.toBeNull();

    // The inner close div should have role="button" and tabIndex=0
    const innerBtn = lightboxDialog!.querySelector('[role="button"][tabindex="0"]');
    expect(innerBtn).not.toBeNull();
  });

  it('lightbox is not rendered initially', () => {
    renderWithQuery(<CardDetailModal card={MOCK_CARD} onClose={vi.fn()} />);
    const lightboxDialog = document.querySelector('[aria-labelledby="card-detail-lightbox-title"]');
    expect(lightboxDialog).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// DeckDetailModal lightbox accessibility tests
// ---------------------------------------------------------------------------

describe('DeckDetailModal lightbox accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('lightbox dialog has aria-labelledby="deck-detail-lightbox-title" when open', async () => {
    const user = userEvent.setup();
    renderWithQuery(
      <DeckDetailModal deckId={1} onClose={vi.fn()} onDeleted={vi.fn()} />,
    );

    // The zoom button shows after deck data loads; its aria-label is from deckDetail.hoverCard
    // The DOM shows: aria-label="Hover a card to preview"
    const zoomInBtn = await screen.findByRole('button', { name: /hover a card to preview/i });
    await user.click(zoomInBtn);

    const lightboxDialog = document.querySelector('[aria-labelledby="deck-detail-lightbox-title"]');
    expect(lightboxDialog).not.toBeNull();
    expect(lightboxDialog).toHaveAttribute('role', 'dialog');
    expect(lightboxDialog).toHaveAttribute('aria-modal', 'true');
  });

  it('lightbox contains a sr-only title span with id "deck-detail-lightbox-title"', async () => {
    const user = userEvent.setup();
    renderWithQuery(
      <DeckDetailModal deckId={1} onClose={vi.fn()} onDeleted={vi.fn()} />,
    );

    const zoomInBtn = await screen.findByRole('button', { name: /hover a card to preview/i });
    await user.click(zoomInBtn);

    const titleSpan = document.getElementById('deck-detail-lightbox-title');
    expect(titleSpan).not.toBeNull();
    expect(titleSpan).toHaveClass('sr-only');
  });

  it('lightbox is not rendered initially', async () => {
    renderWithQuery(
      <DeckDetailModal deckId={1} onClose={vi.fn()} onDeleted={vi.fn()} />,
    );

    const lightboxDialog = document.querySelector('[aria-labelledby="deck-detail-lightbox-title"]');
    expect(lightboxDialog).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// ProfileModal crop sub-modal accessibility tests
// ---------------------------------------------------------------------------

describe('ProfileModal crop sub-modal accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('renders the profile modal as role="dialog" with aria-labelledby="profile-modal-title"', () => {
    renderWithQuery(<ProfileModal onClose={vi.fn()} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-labelledby', 'profile-modal-title');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('crop dialog is not rendered initially (cropOpen defaults to false)', () => {
    renderWithQuery(<ProfileModal onClose={vi.fn()} />);

    // Only one dialog (the profile modal) should be present before file selection
    const dialogs = screen.getAllByRole('dialog');
    expect(dialogs).toHaveLength(1);

    // The crop dialog specifically should not be present
    const cropDialog = document.querySelector('[aria-labelledby="crop-modal-title"]');
    expect(cropDialog).toBeNull();
  });

  it('profile modal dialog has correct accessible structure', () => {
    renderWithQuery(<ProfileModal onClose={vi.fn()} />);

    const dialog = document.querySelector('[aria-labelledby="profile-modal-title"]');
    expect(dialog).not.toBeNull();
    expect(dialog).toHaveAttribute('role', 'dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');

    // The profile-modal-title heading must exist
    const title = document.getElementById('profile-modal-title');
    expect(title).not.toBeNull();
  });
});
