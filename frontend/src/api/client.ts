// API client configuration and utilities

const API_BASE = '/api';

export interface Card {
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
    // Filter out undefined values to avoid sending "undefined" as string
    const cleanParams: Record<string, string> = {};
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
          cleanParams[key] = String(value);
        }
      }
    }
    const query = new URLSearchParams(cleanParams).toString();
    const response = await fetch(`${API_BASE}/cards/${query ? `?${query}` : ''}`);
    if (!response.ok) throw new Error('Failed to fetch cards');
    return response.json();
  },

  getCard: async (name: string): Promise<Card> => {
    const response = await fetch(`${API_BASE}/cards/${encodeURIComponent(name)}/`);
    if (!response.ok) throw new Error('Failed to fetch card');
    return response.json();
  },

  // Stats
  getStats: async (): Promise<Stats> => {
    const response = await fetch(`${API_BASE}/stats/`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  },

  // Process
  triggerProcess: async (limit?: number): Promise<JobResponse> => {
    const response = await fetch(`${API_BASE}/process/`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({limit}),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to trigger process');
    }
    return response.json();
  },

  triggerPriceUpdate: async (): Promise<JobResponse> => {
    const response = await fetch(`${API_BASE}/prices/update/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to trigger price update');
    }
    return response.json();
  },

  getJobs: async (): Promise<JobStatus[]> => {
    const response = await fetch(`${API_BASE}/jobs/`);
    if (!response.ok) throw new Error('Failed to fetch jobs');
    return response.json();
  },

  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/`);
    if (!response.ok) throw new Error('Failed to fetch job status');
    return response.json();
  },

  cancelJob: async (jobId: string): Promise<{job_id: string; status: string; message: string}> => {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/cancel/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to cancel job');
    }
    return response.json();
  },
};
