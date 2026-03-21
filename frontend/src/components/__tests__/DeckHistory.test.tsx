import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeckHistoryTimeline } from '../DeckHistoryTimeline';
import { DeckHistoryModal } from '../DeckHistoryModal';
import { RevertButton } from '../RevertButton';
import type { DeckSnapshot } from '../../api/client';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../../api/client', () => ({
  api: {
    revertDeck: vi.fn(),
    getDeckHistory: vi.fn(),
  },
}));

// AccessibleModal renders children inline in tests
vi.mock('../AccessibleModal', () => ({
  AccessibleModal: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function renderWithQuery(ui: React.ReactElement) {
  return render(<QueryClientProvider client={makeQueryClient()}>{ui}</QueryClientProvider>);
}

function makeSnapshot(id: number, changeSummary: string, diff?: Partial<DeckSnapshot['diff']>): DeckSnapshot {
  return {
    id,
    created_at: new Date().toISOString(),
    created_by: 1,
    change_summary: changeSummary,
    diff: {
      added: [],
      removed: [],
      quantity_changed: [],
      commander_changed: null,
      ...diff,
    },
  };
}

// ---------------------------------------------------------------------------
// DeckHistoryTimeline tests
// ---------------------------------------------------------------------------

describe('DeckHistoryTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when snapshots is empty', () => {
    renderWithQuery(<DeckHistoryTimeline deckId={1} snapshots={[]} onReverted={() => {}} />);
    expect(screen.getByText(/deckHistory\.empty|No history yet/i)).toBeTruthy();
  });

  it('renders snapshot change_summary text', () => {
    const snapshots = [makeSnapshot(1, 'Added 2x Lightning Bolt')];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    expect(screen.getByText('Added 2x Lightning Bolt')).toBeTruthy();
  });

  it('first snapshot (index 0) has disabled RevertButton', () => {
    const snapshots = [
      makeSnapshot(1, 'Added 2x Lightning Bolt'),
      makeSnapshot(2, 'Added 1x Sol Ring'),
    ];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    const buttons = screen.getAllByRole('button');
    const disabledButtons = buttons.filter((btn) => btn.hasAttribute('disabled'));
    expect(disabledButtons.length).toBeGreaterThanOrEqual(1);
  });

  it('subsequent snapshots (index > 0) have active RevertButton', () => {
    const snapshots = [
      makeSnapshot(1, 'Added 2x Lightning Bolt'),
      makeSnapshot(2, 'Added 1x Sol Ring'),
    ];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    const buttons = screen.getAllByRole('button');
    const enabledButtons = buttons.filter((btn) => !btn.hasAttribute('disabled'));
    expect(enabledButtons.length).toBeGreaterThanOrEqual(1);
  });

  it('shows diff added count in DiffSummary when cards were added', () => {
    const snapshots = [
      makeSnapshot(1, 'Batch add', {
        added: [
          { card_id: 10, name: 'Lightning Bolt', quantity: 3 },
          { card_id: 11, name: 'Counterspell', quantity: 2 },
        ],
      }),
    ];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    // 3+2=5 cards added — rendered as "+5 cards" or i18n key
    const text = document.body.textContent ?? '';
    expect(text).toMatch(/\+5|diffAdded/);
  });

  it('shows diff removed count in DiffSummary when cards were removed', () => {
    const snapshots = [
      makeSnapshot(1, 'Remove cards', {
        removed: [{ card_id: 10, name: 'Lightning Bolt', quantity: 4 }],
      }),
    ];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    const text = document.body.textContent ?? '';
    expect(text).toMatch(/-4|diffRemoved/);
  });

  it('shows noChanges label in DiffSummary when diff is completely empty', () => {
    const snapshots = [makeSnapshot(1, 'No-op')];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    expect(screen.getByText(/deckHistory\.noChanges|Initial state/i)).toBeTruthy();
  });

  it('marks index-0 snapshot with currentVersion label', () => {
    const snapshots = [makeSnapshot(1, 'Latest change'), makeSnapshot(2, 'Older change')];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    const text = document.body.textContent ?? '';
    expect(text).toMatch(/currentVersion|Current version/i);
  });

  it('renders all snapshots as list items', () => {
    const snapshots = [
      makeSnapshot(1, 'First'),
      makeSnapshot(2, 'Second'),
      makeSnapshot(3, 'Third'),
    ];
    renderWithQuery(
      <DeckHistoryTimeline deckId={1} snapshots={snapshots} onReverted={() => {}} />,
    );
    const items = screen.getAllByRole('listitem');
    expect(items.length).toBe(3);
  });
});

// ---------------------------------------------------------------------------
// RevertButton tests
// ---------------------------------------------------------------------------

describe('RevertButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls api.revertDeck and invokes onReverted on success', async () => {
    const { api } = await import('../../api/client');
    const mockRevertDeck = vi.mocked(api.revertDeck);
    mockRevertDeck.mockResolvedValueOnce({
      id: 1,
      name: 'Test Deck',
      created_at: '2026-01-01T00:00:00',
      updated_at: '2026-01-01T00:00:00',
      cards: [],
    });

    const onReverted = vi.fn();
    renderWithQuery(<RevertButton deckId={1} snapshotId={42} onReverted={onReverted} />);

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(mockRevertDeck).toHaveBeenCalledWith(1, 42);
      expect(onReverted).toHaveBeenCalled();
    });
  });

  it('is disabled when disabled prop is true', () => {
    renderWithQuery(<RevertButton deckId={1} snapshotId={42} onReverted={() => {}} disabled />);
    const button = screen.getByRole('button');
    expect(button).toHaveProperty('disabled', true);
  });

  it('shows error message on revert failure', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.revertDeck).mockRejectedValueOnce(new Error('Network error'));

    renderWithQuery(<RevertButton deckId={1} snapshotId={42} onReverted={() => {}} />);

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      const alert = screen.getByRole('alert');
      expect(alert).toBeTruthy();
      expect(alert.textContent).toMatch(/Network error/);
    });
  });

  it('shows revertCardMissing error when detail mentions "no longer exists"', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.revertDeck).mockRejectedValueOnce(
      new Error("Card 'Sol Ring' no longer exists in collection"),
    );

    renderWithQuery(<RevertButton deckId={1} snapshotId={42} onReverted={() => {}} />);

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      const alert = screen.getByRole('alert');
      // RevertButton maps this to revertCardMissing i18n key or keeps the original message
      expect(alert.textContent).toMatch(
        /revertCardMissing|no longer exists|Cannot revert/i,
      );
    });
  });

  it('does not call onReverted when revert fails', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.revertDeck).mockRejectedValueOnce(new Error('Server error'));

    const onReverted = vi.fn();
    renderWithQuery(<RevertButton deckId={1} snapshotId={42} onReverted={onReverted} />);

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => screen.getByRole('alert'));
    expect(onReverted).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// DeckHistoryModal tests
// ---------------------------------------------------------------------------

describe('DeckHistoryModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state while history is being fetched', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.getDeckHistory).mockReturnValue(new Promise(() => {}));

    renderWithQuery(
      <DeckHistoryModal deckId={1} onClose={() => {}} onReverted={() => {}} />,
    );

    expect(screen.getByText(/deckHistory\.loading|Loading history/i)).toBeTruthy();
  });

  it('shows error alert when history fetch fails', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.getDeckHistory).mockRejectedValueOnce(new Error('Deck not found'));

    renderWithQuery(
      <DeckHistoryModal deckId={1} onClose={() => {}} onReverted={() => {}} />,
    );

    await waitFor(() => {
      const alert = screen.getByRole('alert');
      expect(alert.textContent).toMatch(/Deck not found/);
    });
  });

  it('renders timeline after successful history fetch', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.getDeckHistory).mockResolvedValueOnce({
      deck_id: 1,
      snapshots: [makeSnapshot(1, 'Added Sol Ring')],
    });

    renderWithQuery(
      <DeckHistoryModal deckId={1} onClose={() => {}} onReverted={() => {}} />,
    );

    await waitFor(() => {
      expect(screen.getByText('Added Sol Ring')).toBeTruthy();
    });
  });

  it('shows empty state when deck has no snapshots', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.getDeckHistory).mockResolvedValueOnce({
      deck_id: 1,
      snapshots: [],
    });

    renderWithQuery(
      <DeckHistoryModal deckId={1} onClose={() => {}} onReverted={() => {}} />,
    );

    await waitFor(() => {
      expect(screen.getByText(/deckHistory\.empty|No history yet/i)).toBeTruthy();
    });
  });

  it('calls onClose when close button is clicked', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.getDeckHistory).mockReturnValue(new Promise(() => {}));

    const onClose = vi.fn();
    renderWithQuery(
      <DeckHistoryModal deckId={1} onClose={onClose} onReverted={() => {}} />,
    );

    const closeButton = screen.getByRole('button', { name: /deckHistory\.close|Close/i });
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalled();
  });

  it('renders modal title', async () => {
    const { api } = await import('../../api/client');
    vi.mocked(api.getDeckHistory).mockReturnValue(new Promise(() => {}));

    renderWithQuery(
      <DeckHistoryModal deckId={1} onClose={() => {}} onReverted={() => {}} />,
    );

    expect(screen.getByText(/deckHistory\.title|Deck History/i)).toBeTruthy();
  });
});
