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
  };
  start_time: string;
  job_type: string;
}

// API functions
export const api = {
  // Cards
  getCards: async (params?: {limit?: number; offset?: number; search?: string}): Promise<Card[]> => {
    const cleanParams: Record<string, string> = {};
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
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

  // Stats
  getStats: async (): Promise<Stats> => {
    const response = await apiFetch(`${API_BASE}/stats/`);
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
};
