// API client configuration and utilities
const API_BASE = '/api';
const FETCH_OPTS: RequestInit = { credentials: 'include' };

/** Wraps fetch and turns network errors into a clearer message. */
async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg === 'Failed to fetch' || msg.includes('NetworkError') || msg.includes('Load failed')) {
      throw new Error('Cannot reach the backend. Check that it is running (e.g. on port 8000) and that the frontend can connect to it.');
    }
    throw e;
  }
}

export interface Card {
  id?: number;
  name?: string;
  english_name?: string;
  type?: string;
  description?: string;
  keywords?: string;
  mana_cost?: string;
  cmc?: number;
  color_identity?: string;
  colors?: string;
  power?: string;
  toughness?: string;
  rarity?: string;
  price?: string;
  release_date?: string;
  set_id?: string;
  set_name?: string;
  number?: string;
  edhrec_rank?: string;
  game_strategy?: string;
  tier?: string;
  created_at?: string;  // ISO timestamp when card was added
  [key: string]: any;
}

export interface Stats {
  total_cards: number;
  total_value: number;
  average_price: number;
  last_updated: string;
}

export interface JobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  progress: {
    current?: number;
    total?: number;
    percentage?: number;
    errors?: Array<{card_name: string; message: string}>;
    summary?: Record<string, unknown>;
  };
  start_time: string;
  job_type: string;
}

export interface DeckListItem {
  id: number;
  name: string;
  created_at?: string;
  updated_at?: string;
  card_count?: number;
  commander_card_id?: number | null;
}

export interface DeckCard extends Card {
  quantity?: number;
  is_commander?: boolean;
}

export interface DeckWithCards extends DeckListItem {
  cards: DeckCard[];
}

// API functions
export const api = {
  // Cards (same filter params as stats so list and totals match)
  getCards: async (params?: {
    limit?: number;
    offset?: number;
    search?: string;
    rarity?: string;
    type?: string;
    color_identity?: string;
    set_name?: string;
    price_min?: string;
    price_max?: string;
  }): Promise<Card[]> => {
    const cleanParams: Record<string, string> = {};
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== '') {
          cleanParams[key] = String(value);
        }
      }
    }
    const query = new URLSearchParams(cleanParams).toString();
    const response = await apiFetch(`${API_BASE}/cards/${query ? `?${query}` : ''}`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch cards');
    return response.json();
  },

  getCard: async (name: string): Promise<Card> => {
    const response = await apiFetch(`${API_BASE}/cards/${encodeURIComponent(name)}`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch card');
    return response.json();
  },

  /** Card name suggestions from Scryfall autocomplete for Add card name field. */
  getCardSuggest: async (query: string): Promise<string[]> => {
    const q = (query || '').trim();
    if (q.length < 2) return [];
    const response = await apiFetch(`${API_BASE}/cards/suggest?q=${encodeURIComponent(q)}`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch suggestions');
    return response.json();
  },

  /** Resolve full card data by name (Scryfall or collection) for use in POST create. */
  resolveCardByName: async (name: string): Promise<Card> => {
    const n = (name || '').trim();
    if (!n) throw new Error('Card name is required');
    const response = await apiFetch(`${API_BASE}/cards/resolve?name=${encodeURIComponent(n)}`, FETCH_OPTS);
    if (!response.ok) {
      if (response.status === 404) throw new Error('Card not found');
      throw new Error('Failed to resolve card');
    }
    return response.json();
  },

  /** URL for card image by id (use as img src). Backend fetches from Scryfall on first request and caches. */
  getCardImageUrl: (id: number): string => `${API_BASE}/cards/${id}/image`,

  // Stats (optional filter params: same as dashboard filters)
  getStats: async (params?: {
    search?: string;
    rarity?: string;
    type?: string;
    set_name?: string;
    price_min?: string;
    price_max?: string;
  }): Promise<Stats> => {
    const cleanParams: Record<string, string> = {};
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== '') {
          cleanParams[key] = String(value);
        }
      }
    }
    const query = new URLSearchParams(cleanParams).toString();
    const url = `${API_BASE}/stats/${query ? `?${query}` : ''}`;
    const response = await apiFetch(url, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  },

  // Process (scope: 'all' = all cards, 'new_only' = only cards with just the name / no type_line)
  triggerProcess: async (opts?: { limit?: number; scope?: 'all' | 'new_only' }): Promise<JobResponse> => {
    const body = opts ? { limit: opts.limit, scope: opts.scope ?? 'all' } : {};
    const response = await apiFetch(`${API_BASE}/process`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to trigger process');
    }
    return response.json();
  },

  triggerPriceUpdate: async (): Promise<JobResponse> => {
    const response = await apiFetch(`${API_BASE}/prices/update`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to trigger price update');
    }
    return response.json();
  },

  triggerSingleCardPriceUpdate: async (cardId: number): Promise<JobResponse> => {
    const response = await apiFetch(`${API_BASE}/prices/update/${cardId}`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to trigger single-card price update');
    }
    return response.json();
  },

  getJobs: async (): Promise<JobStatus[]> => {
    const response = await apiFetch(`${API_BASE}/jobs`);
    if (!response.ok) throw new Error('Failed to fetch jobs');
    return response.json();
  },

  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await apiFetch(`${API_BASE}/jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch job status');
    return response.json();
  },

  cancelJob: async (jobId: string): Promise<{job_id: string; status: string; message: string}> => {
    const response = await apiFetch(`${API_BASE}/jobs/${jobId}/cancel`, {
      method: 'POST',
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to cancel job');
    }
    return response.json();
  },

  // Settings: Scryfall credentials (stored as JSON internally by the backend)
  getScryfallCredentials: async (): Promise<{ configured: boolean }> => {
    const response = await apiFetch(`${API_BASE}/settings/scryfall-credentials`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch Scryfall credentials status');
    return response.json();
  },
  setScryfallCredentials: async (credentials: object | null): Promise<{ configured: boolean }> => {
    const response = await apiFetch(`${API_BASE}/settings/scryfall-credentials`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credentials }),
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || 'Failed to save Scryfall credentials');
    }
    return response.json();
  },

  // Analytics aggregations
  getAnalyticsRarity: async (params?: Record<string, string>): Promise<{ rarity: string; count: number }[]> => {
    const query = params ? new URLSearchParams(params).toString() : '';
    const response = await apiFetch(`${API_BASE}/analytics/rarity${query ? `?${query}` : ''}`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch analytics rarity');
    return response.json();
  },
  getAnalyticsColorIdentity: async (params?: Record<string, string>): Promise<{ color_identity: string; count: number }[]> => {
    const query = params ? new URLSearchParams(params).toString() : '';
    const response = await apiFetch(`${API_BASE}/analytics/color-identity${query ? `?${query}` : ''}`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch analytics color identity');
    return response.json();
  },
  getAnalyticsCmc: async (params?: Record<string, string>): Promise<{ cmc: string; count: number }[]> => {
    const query = params ? new URLSearchParams(params).toString() : '';
    const response = await apiFetch(`${API_BASE}/analytics/cmc${query ? `?${query}` : ''}`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch analytics CMC');
    return response.json();
  },
  getAnalyticsSets: async (params?: Record<string, string>): Promise<{ set_name: string; count: number }[]> => {
    const query = params ? new URLSearchParams(params).toString() : '';
    const response = await apiFetch(`${API_BASE}/analytics/sets${query ? `?${query}` : ''}`, FETCH_OPTS);
    if (!response.ok) throw new Error('Failed to fetch analytics sets');
    return response.json();
  },

  // Import from file (CSV/JSON)
  importFromFile: async (file: File): Promise<{ imported: number }> => {
    const form = new FormData();
    form.append('file', file);
    const response = await apiFetch(`${API_BASE}/import/file`, {
      method: 'POST',
      body: form,
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || 'Import failed');
    }
    return response.json();
  },

  // Card CRUD (Postgres)
  createCard: async (card: Partial<Card>): Promise<Card> => {
    const response = await apiFetch(`${API_BASE}/cards/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(card),
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || 'Create failed');
    }
    return response.json();
  },
  updateCard: async (id: number, card: Partial<Card>): Promise<Card> => {
    const response = await apiFetch(`${API_BASE}/cards/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(card),
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || 'Update failed');
    }
    return response.json();
  },
  deleteCard: async (id: number): Promise<void> => {
    const response = await apiFetch(`${API_BASE}/cards/${id}`, {
      method: 'DELETE',
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || 'Delete failed');
    }
  },

  // Decks (require Postgres; 501 if unavailable)
  getDecks: async (): Promise<DeckListItem[]> => {
    const response = await apiFetch(`${API_BASE}/decks/`, FETCH_OPTS);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
      throw new Error((err as { detail?: string }).detail || 'Failed to fetch decks');
    }
    return response.json();
  },
  getDeck: async (id: number): Promise<DeckWithCards> => {
    const response = await apiFetch(`${API_BASE}/decks/${id}`, FETCH_OPTS);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
      if (response.status === 404) throw new Error('Deck not found');
      throw new Error((err as { detail?: string }).detail || 'Failed to fetch deck');
    }
    return response.json();
  },
  createDeck: async (name: string): Promise<DeckListItem> => {
    const response = await apiFetch(`${API_BASE}/decks/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name || 'Unnamed Deck' }),
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
      throw new Error((err as { detail?: string }).detail || 'Failed to create deck');
    }
    return response.json();
  },
  updateDeck: async (id: number, payload: { name: string }): Promise<DeckListItem> => {
    const response = await apiFetch(`${API_BASE}/decks/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 404) throw new Error('Deck not found');
      throw new Error((err as { detail?: string }).detail || 'Failed to update deck');
    }
    return response.json();
  },
  deleteDeck: async (id: number): Promise<void> => {
    const response = await apiFetch(`${API_BASE}/decks/${id}`, {
      method: 'DELETE',
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
      if (response.status === 404) throw new Error('Deck not found');
      throw new Error((err as { detail?: string }).detail || 'Delete failed');
    }
  },
  addCardToDeck: async (
    deckId: number,
    cardId: number,
    opts?: { quantity?: number; is_commander?: boolean }
  ): Promise<DeckWithCards> => {
    const response = await apiFetch(`${API_BASE}/decks/${deckId}/cards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        card_id: cardId,
        quantity: opts?.quantity ?? 1,
        is_commander: opts?.is_commander ?? false,
      }),
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
      if (response.status === 404) throw new Error((err as { detail?: string }).detail || 'Deck or card not found');
      throw new Error((err as { detail?: string }).detail || 'Failed to add card');
    }
    return response.json();
  },
  removeCardFromDeck: async (deckId: number, cardId: number): Promise<void> => {
    const response = await apiFetch(`${API_BASE}/decks/${deckId}/cards/${cardId}`, {
      method: 'DELETE',
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 404) throw new Error('Deck or card not found');
      throw new Error((err as { detail?: string }).detail || 'Failed to remove card');
    }
  },
  setDeckCardCommander: async (deckId: number, cardId: number): Promise<DeckWithCards> => {
    const response = await apiFetch(`${API_BASE}/decks/${deckId}/cards/${cardId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_commander: true }),
      ...FETCH_OPTS,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 404) throw new Error('Deck or card not found');
      throw new Error((err as { detail?: string }).detail || 'Failed to set commander');
    }
    return response.json();
  },
};
