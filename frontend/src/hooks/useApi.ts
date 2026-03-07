import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Card, CardPage, FilterOptions, InsightCatalogEntry, InsightSuggestion, InsightResponse } from '../api/client';
import { useDemoMode } from '../contexts/DemoContext';
import { DEMO_CARDS, DEMO_CATALOG, DEMO_SUGGESTIONS } from '../data/demoData';

// Params for cards list (same filter shape as dashboard; map to API snake_case in getCards)
export interface CardsParams {
  limit?: number;
  offset?: number;
  search?: string;
  rarity?: string;
  type?: string;
  set?: string;
  priceMin?: string;
  priceMax?: string;
  colorIdentity?: string;
  sortBy?: string;
  sortDir?: string;
}

// Hook for fetching cards; pass current dashboard filters so list and stats match.
// Returns CardPage: { items: Card[], total: number, limit: number, offset: number }
// In demo mode, returns a compatible CardPage shape built from DEMO_CARDS.
export function useCards(params?: CardsParams) {
  const { isDemoMode } = useDemoMode();
  const apiParams =
    !isDemoMode && params
      ? {
          limit: params.limit,
          offset: params.offset,
          search: params.search,
          rarity: params.rarity,
          type: params.type,
          set_name: params.set,
          price_min: params.priceMin,
          price_max: params.priceMax,
          color_identity: params.colorIdentity,
          sort_by: params.sortBy,
          sort_dir: params.sortDir,
        }
      : undefined;
  const query = useQuery<CardPage>({
    queryKey: ['cards', apiParams],
    queryFn: () => api.getCards(apiParams),
    staleTime: 30000, // 30 seconds
    enabled: !isDemoMode,
  });
  if (isDemoMode) {
    const search = (params?.search ?? '').toLowerCase();
    const rar = params?.rarity;
    const filtered = DEMO_CARDS.filter(c => {
      const matchesSearch = !search || (c.name ?? '').toLowerCase().includes(search) || (c.set_id ?? '').toLowerCase().includes(search);
      const matchesRarity = !rar || c.rarity === rar;
      return matchesSearch && matchesRarity;
    });
    const limit = params?.limit ?? 100;
    const offset = params?.offset ?? 0;
    const page: CardPage = {
      items: filtered.slice(offset, offset + limit) as Card[],
      total: filtered.length,
      limit,
      offset,
    };
    return { data: page, isLoading: false, error: null };
  }
  return query;
}

// Hook for fetching filter options (distinct types and sets) for dropdown menus.
// Uses a 60s stale time since these change infrequently.
export function useFilterOptions() {
  const { isDemoMode } = useDemoMode();
  const query = useQuery<FilterOptions>({
    queryKey: ['filter-options'],
    queryFn: () => api.getFilterOptions(),
    staleTime: 60000, // 60 seconds
    enabled: !isDemoMode,
  });
  if (isDemoMode) {
    // Build options from demo data
    const types = Array.from(new Set(DEMO_CARDS.map(c => c.type).filter(Boolean) as string[])).sort();
    const sets = Array.from(new Set(DEMO_CARDS.map(c => c.set_name).filter(Boolean) as string[])).sort();
    return { data: { types, sets } as FilterOptions, isLoading: false, error: null };
  }
  return query;
}

// Hook for fetching single card
export function useCard(name: string) {
  return useQuery({
    queryKey: ['card', name],
    queryFn: () => api.getCard(name),
    enabled: !!name,
  });
}

export interface StatsFilters {
  search?: string;
  rarity?: string;
  type?: string;
  set?: string;
  priceMin?: string;
  priceMax?: string;
  colorIdentity?: string;
  cmc?: string;
}

// Hook for fetching stats; pass current dashboard filters so stats reflect filtered set
export function useStats(filters?: StatsFilters) {
  const apiParams =
    filters &&
    (filters.search ||
      filters.rarity ||
      filters.type ||
      filters.set ||
      filters.priceMin ||
      filters.priceMax ||
      filters.colorIdentity ||
      filters.cmc)
      ? {
          search: filters.search || undefined,
          rarity: filters.rarity || undefined,
          type: filters.type || undefined,
          set_name: filters.set || undefined,
          price_min: filters.priceMin || undefined,
          price_max: filters.priceMax || undefined,
          color_identity: filters.colorIdentity || undefined,
          cmc: filters.cmc || undefined,
        }
      : undefined;

  return useQuery({
    queryKey: ['stats', apiParams],
    queryFn: () => api.getStats(apiParams),
    staleTime: 30000,
    refetchInterval: 30000,
  });
}

// Hook for triggering process (opts.scope: 'all' | 'new_only')
export function useTriggerProcess() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (opts?: { limit?: number; scope?: 'all' | 'new_only' }) => api.triggerProcess(opts),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['cards']});
      queryClient.invalidateQueries({queryKey: ['stats']});
    },
  });
}

// Hook for triggering price update
export function useTriggerPriceUpdate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.triggerPriceUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['cards']});
      queryClient.invalidateQueries({queryKey: ['stats']});
    },
  });
}

// Hook for WebSocket connection with progress tracking and auto-reconnection
export function useWebSocket(jobId: string | null) {
  const [status, setStatus] = React.useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [progress, setProgress] = React.useState<{current: number; total: number; percentage: number}>({
    current: 0,
    total: 0,
    percentage: 0,
  });
  const [errors, setErrors] = React.useState<Array<{card_name: string; message: string}>>([]);
  const [complete, setComplete] = React.useState(false);
  const [summary, setSummary] = React.useState<Record<string, unknown> | null>(null);

  React.useEffect(() => {
    if (!jobId) return;

    // Reset state for new job
    setErrors([]);
    setComplete(false);
    setSummary(null);
    setStatus('connecting');

    let cancelled = false;
    let retryCount = 0;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let currentWs: WebSocket | null = null;
    const MAX_RETRIES = 5;
    const BASE_DELAY = 1000; // 1s, doubles each retry up to 16s

    // Fetch current job state via REST (used on initial connect and reconnects)
    const fetchRestState = () => {
      api.getJobStatus(jobId).then((jobStatus) => {
        if (cancelled) return;
        const p = jobStatus.progress || {};
        const perc = p.percentage ?? 0;
        const cur = p.current ?? 0;
        const tot = p.total ?? 0;
        if (perc > 0 || cur > 0 || tot > 0) {
          setProgress({ current: cur, total: tot, percentage: perc });
        } else {
          setProgress({ current: 0, total: 0, percentage: 0 });
        }
        // If job already completed, set final state without waiting for WS
        if (jobStatus.status === 'complete' || jobStatus.status === 'error' || jobStatus.status === 'cancelled') {
          setComplete(true);
          setSummary(p.summary ?? jobStatus);
          setStatus('disconnected');
        }
      }).catch(() => {
        if (!cancelled) {
          setProgress({ current: 0, total: 0, percentage: 0 });
        }
      });
    };

    const connect = () => {
      if (cancelled) return;
      setStatus('connecting');
      fetchRestState();

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.host;
      const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/progress/${jobId}`);
      currentWs = ws;

      ws.onopen = () => {
        if (cancelled) { ws.close(); return; }
        setStatus('connected');
        retryCount = 0; // reset on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'progress') {
            setProgress({
              current: data.current || 0,
              total: data.total || 0,
              percentage: data.percentage || 0,
            });
          } else if (data.type === 'error') {
            setErrors(prev => [...prev, {
              card_name: data.card_name || 'Unknown',
              message: data.message || 'Unknown error',
            }]);
          } else if (data.type === 'complete') {
            setComplete(true);
            setSummary(data.summary || data);
            setStatus('disconnected');
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = () => {
        // onerror is always followed by onclose, reconnect logic is in onclose
      };

      ws.onclose = (event) => {
        if (cancelled) return;
        setStatus('disconnected');
        // Only reconnect on unexpected close (not clean 1000)
        if (event.code !== 1000 && retryCount < MAX_RETRIES) {
          const delay = Math.min(BASE_DELAY * Math.pow(2, retryCount), 16000);
          retryCount++;
          retryTimer = setTimeout(connect, delay);
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (currentWs) currentWs.close();
    };
  }, [jobId]);

  return { status, progress, errors, complete, summary };
}

// Hook for fetching insights catalog
export function useInsightsCatalog() {
  const { isDemoMode } = useDemoMode();
  const query = useQuery<InsightCatalogEntry[]>({
    queryKey: ['insights', 'catalog'],
    queryFn: () => api.getInsightsCatalog(),
    staleTime: 5 * 60 * 1000, // 5 minutes — catalog rarely changes
    enabled: !isDemoMode,
  });
  if (isDemoMode) {
    return { data: DEMO_CATALOG as InsightCatalogEntry[], isLoading: false, error: null };
  }
  return query;
}

// Hook for fetching contextual insight suggestions
export function useInsightsSuggestions() {
  const { isDemoMode } = useDemoMode();
  const query = useQuery<InsightSuggestion[]>({
    queryKey: ['insights', 'suggestions'],
    queryFn: () => api.getInsightsSuggestions(),
    staleTime: 30000,
    enabled: !isDemoMode,
  });
  if (isDemoMode) {
    return { data: DEMO_SUGGESTIONS as InsightSuggestion[], isLoading: false, error: null };
  }
  return query;
}

// Hook for executing an insight
export function useInsightExecute() {
  return useMutation<InsightResponse, Error, string>({
    mutationFn: (insightId: string) => api.executeInsight(insightId),
  });
}
