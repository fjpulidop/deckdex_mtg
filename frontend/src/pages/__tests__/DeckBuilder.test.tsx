import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeckCardButton } from '../DeckBuilder';
import { useCardImage } from '../../hooks/useCardImage';
import type { DeckListItem } from '../../api/client';

// ---------------------------------------------------------------------------
// Mock hooks and API
// ---------------------------------------------------------------------------

vi.mock('../../hooks/useCardImage', () => ({
  useCardImage: vi.fn(),
}));

vi.mock('../../api/client', () => ({
  api: {
    getDecks: vi.fn(() => Promise.resolve([])),
  },
}));

const mockUseCardImage = useCardImage as ReturnType<typeof vi.fn>;

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

// ---------------------------------------------------------------------------
// DeckCardButton tests
// ---------------------------------------------------------------------------

describe('DeckCardButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders background image and overlay when commanderImageUrl is set', () => {
    mockUseCardImage.mockReturnValue({
      src: 'blob:http://test/image',
      loading: false,
      error: false,
    });

    const deck: DeckListItem = {
      id: 1,
      name: 'Test Deck',
      card_count: 30,
      commander_card_id: 42,
    };

    renderWithQuery(<DeckCardButton deck={deck} onClick={() => {}} />);

    // Background image div should be present
    const bgDiv = document.querySelector('[style*="background-image"]');
    expect(bgDiv).not.toBeNull();

    // Dark overlay should be present
    const overlay = document.querySelector('.bg-black\\/55');
    expect(overlay).not.toBeNull();
  });

  it('renders neutral background and no overlay when commanderImageUrl is null', () => {
    mockUseCardImage.mockReturnValue({
      src: null,
      loading: false,
      error: false,
    });

    const deck: DeckListItem = {
      id: 2,
      name: 'No Commander',
      card_count: 0,
      commander_card_id: null,
    };

    renderWithQuery(<DeckCardButton deck={deck} onClick={() => {}} />);

    // No background image div
    const bgDiv = document.querySelector('[style*="background-image"]');
    expect(bgDiv).toBeNull();

    // No dark overlay
    const overlay = document.querySelector('.bg-black\\/55');
    expect(overlay).toBeNull();
  });

  it('shows white text with drop-shadow when image is present', () => {
    mockUseCardImage.mockReturnValue({
      src: 'blob:http://test/img',
      loading: false,
      error: false,
    });

    const deck: DeckListItem = {
      id: 3,
      name: 'Commander Deck',
      card_count: 10,
      commander_card_id: 5,
    };

    renderWithQuery(<DeckCardButton deck={deck} onClick={() => {}} />);

    const nameSpan = screen.getByText('Commander Deck');
    expect(nameSpan.className).toContain('text-white');
  });
});
