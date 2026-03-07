import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from '../Dashboard';

// ---------------------------------------------------------------------------
// Mock heavy child components — keep focus on Dashboard toggle behavior
// ---------------------------------------------------------------------------
vi.mock('../../components/CardTable', () => ({
  CardTable: () => <div data-testid="card-table" />,
}));

vi.mock('../../components/CardGallery', () => ({
  CardGallery: () => <div data-testid="card-gallery" />,
}));

vi.mock('../../components/CollectionInsights', () => ({
  CollectionInsights: () => <div data-testid="collection-insights" />,
}));

vi.mock('../../components/Filters', () => ({
  Filters: () => <div data-testid="filters" />,
}));

// ---------------------------------------------------------------------------
// Mock hooks that make network requests
// ---------------------------------------------------------------------------
vi.mock('../../hooks/useApi', () => ({
  useCards: vi.fn(() => ({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  })),
  useFilterOptions: vi.fn(() => ({ data: null })),
  useTriggerPriceUpdate: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

vi.mock('../../contexts/ActiveJobsContext', () => ({
  useActiveJobs: vi.fn(() => ({ addJob: vi.fn() })),
}));

vi.mock('../../api/client', () => ({
  api: {
    getCard: vi.fn(),
  },
}));

// ---------------------------------------------------------------------------
// localStorage spy helpers
// ---------------------------------------------------------------------------
let localStorageStore: Record<string, string> = {};

const mockLocalStorage = {
  getItem: (key: string) => localStorageStore[key] ?? null,
  setItem: (key: string, value: string) => { localStorageStore[key] = value; },
  removeItem: (key: string) => { delete localStorageStore[key]; },
  clear: () => { localStorageStore = {}; },
};

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------
function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Dashboard view toggle', () => {
  beforeEach(() => {
    localStorageStore = {};
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
    localStorageStore = {};
  });

  it('renders table view by default (no localStorage value)', () => {
    renderDashboard();
    expect(screen.getByTestId('card-table')).toBeInTheDocument();
    expect(screen.queryByTestId('card-gallery')).not.toBeInTheDocument();
  });

  it('renders gallery view after clicking the gallery toggle button', async () => {
    const user = userEvent.setup();
    renderDashboard();

    const galleryBtn = screen.getByRole('button', { name: /gallery view/i });
    await user.click(galleryBtn);

    expect(screen.getByTestId('card-gallery')).toBeInTheDocument();
    expect(screen.queryByTestId('card-table')).not.toBeInTheDocument();
  });

  it('persists view choice to localStorage after toggle', async () => {
    const user = userEvent.setup();
    renderDashboard();

    const galleryBtn = screen.getByRole('button', { name: /gallery view/i });
    await user.click(galleryBtn);

    expect(localStorageStore['collectionView']).toBe('gallery');
  });

  it('restores gallery view from localStorage on mount', () => {
    localStorageStore['collectionView'] = 'gallery';
    renderDashboard();
    expect(screen.getByTestId('card-gallery')).toBeInTheDocument();
    expect(screen.queryByTestId('card-table')).not.toBeInTheDocument();
  });

  it('uses limit=24 in gallery mode and limit=50 in table mode', async () => {
    const { useCards } = await import('../../hooks/useApi');
    const mockUseCards = useCards as ReturnType<typeof vi.fn>;

    const user = userEvent.setup();
    renderDashboard();

    // Default table mode — should have been called with limit=50
    const firstCall = mockUseCards.mock.calls[0]?.[0];
    expect(firstCall?.limit).toBe(50);

    // Switch to gallery
    const galleryBtn = screen.getByRole('button', { name: /gallery view/i });
    await user.click(galleryBtn);

    await waitFor(() => {
      const lastCall = mockUseCards.mock.calls[mockUseCards.mock.calls.length - 1]?.[0];
      expect(lastCall?.limit).toBe(24);
    });
  });
});
