import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeckCardPickerModal } from '../DeckCardPickerModal';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../../api/client', () => ({
  api: {
    getCards: vi.fn(() => Promise.resolve([])),
  },
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DeckCardPickerModal mobile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('"Add to Deck" button has w-full class for full-width on mobile', () => {
    renderWithQuery(
      <DeckCardPickerModal
        deckId={1}
        onClose={() => {}}
        onAdded={() => {}}
      />,
    );

    const addBtn = screen.getByRole('button', { name: /add to deck/i });
    expect(addBtn.className).toContain('w-full');
  });
});
