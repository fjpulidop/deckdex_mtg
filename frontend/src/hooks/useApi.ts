import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Card, Stats, JobResponse } from '../api/client';

// Hook for fetching cards
export function useCards(params?: {limit?: number; offset?: number; search?: string}) {
  return useQuery({
    queryKey: ['cards', params],
    queryFn: () => api.getCards(params),
    staleTime: 30000, // 30 seconds
  });
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
      filters.priceMax)
      ? {
          search: filters.search || undefined,
          rarity: filters.rarity || undefined,
          type: filters.type || undefined,
          set_name: filters.set || undefined,
          price_min: filters.priceMin || undefined,
          price_max: filters.priceMax || undefined,
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

// Hook for WebSocket connection with progress tracking
export function useWebSocket(jobId: string | null) {
  const [status, setStatus] = React.useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [progress, setProgress] = React.useState<{current: number; total: number; percentage: number}>({
    current: 0,
    total: 0,
    percentage: 0,
  });
  const [errors, setErrors] = React.useState<Array<{card_name: string; message: string}>>([]);
  const [complete, setComplete] = React.useState(false);
  const [summary, setSummary] = React.useState<any>(null);

  React.useEffect(() => {
    if (!jobId) return;

    // Reset state for new job
    setErrors([]);
    setComplete(false);
    setSummary(null);
    setStatus('connecting');

    // Immediately fetch current state from REST API so we don't flash 0%
    // while the WebSocket is still connecting
    let cancelled = false;
    api.getJobStatus(jobId).then((jobStatus) => {
      if (cancelled) return;
      const p = jobStatus.progress || {};
      if (p.percentage > 0 || p.current > 0 || p.total > 0) {
        setProgress({
          current: p.current || 0,
          total: p.total || 0,
          percentage: p.percentage || 0,
        });
      } else {
        // Only reset to 0 if REST says progress is 0 (truly just started)
        setProgress({ current: 0, total: 0, percentage: 0 });
      }
      // If job already completed before we opened the modal
      if (jobStatus.status === 'complete' || jobStatus.status === 'error') {
        setComplete(true);
        setSummary(p.summary || jobStatus);
      }
    }).catch(() => {
      // REST fetch failed - start from zero, WebSocket will update
      if (!cancelled) {
        setProgress({ current: 0, total: 0, percentage: 0 });
      }
    });

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/progress/${jobId}`);

    ws.onopen = () => {
      setStatus('connected');
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
        // Ignore ping/pong/connected messages
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = () => {
      setStatus('disconnected');
    };

    ws.onclose = () => {
      setStatus('disconnected');
    };

    return () => {
      cancelled = true;
      ws.close();
    };
  }, [jobId]);

  return { status, progress, errors, complete, summary };
}
