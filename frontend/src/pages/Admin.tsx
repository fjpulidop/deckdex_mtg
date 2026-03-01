import { useState, useEffect, useCallback } from 'react';
import { api, CatalogSyncStatus } from '../api/client';

const STATUS_BADGE: Record<string, string> = {
  idle: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  syncing_data: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  syncing_images: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
};

function statusLabel(s: string): string {
  switch (s) {
    case 'syncing_data': return 'Syncing Data';
    case 'syncing_images': return 'Syncing Images';
    default: return s.charAt(0).toUpperCase() + s.slice(1);
  }
}

export function Admin() {
  const [syncStatus, setSyncStatus] = useState<CatalogSyncStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // WebSocket progress state
  const [wsPhase, setWsPhase] = useState<string | null>(null);
  const [wsCurrent, setWsCurrent] = useState(0);
  const [wsTotal, setWsTotal] = useState(0);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.adminGetCatalogSyncStatus();
      setSyncStatus(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load sync status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // WebSocket connection for real-time progress
  useEffect(() => {
    if (!jobId) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/progress/${jobId}`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'progress') {
          setWsPhase(data.phase ?? null);
          setWsCurrent(data.current ?? 0);
          setWsTotal(data.total ?? 0);
        } else if (data.type === 'complete') {
          setSyncing(false);
          setJobId(null);
          setWsPhase(null);
          setSuccessMsg('Catalog sync completed successfully.');
          fetchStatus();
        } else if (data.type === 'error') {
          setError(data.message || 'Sync encountered an error');
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      setSyncing(false);
    };

    ws.onclose = () => {
      // If still syncing when socket closes, refresh status
      if (syncing) {
        fetchStatus();
      }
    };

    return () => ws.close();
  }, [jobId, fetchStatus, syncing]);

  const handleStartSync = async () => {
    setError(null);
    setSuccessMsg(null);
    setSyncing(true);
    setWsPhase(null);
    setWsCurrent(0);
    setWsTotal(0);

    try {
      const result = await api.adminTriggerCatalogSync();
      setJobId(result.job_id);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to start sync';
      if (msg.includes('already in progress') || msg.includes('409')) {
        setError('Sync already in progress');
      } else {
        setError(msg);
      }
      setSyncing(false);
    }
  };

  const isSyncing = syncing || syncStatus?.status === 'syncing_data' || syncStatus?.status === 'syncing_images';
  const percentage = wsTotal > 0 ? Math.round((wsCurrent / wsTotal) * 100) : 0;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
        Admin Dashboard
      </h1>

      {/* Catalog Sync Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Catalog Sync
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-500"></div>
            Loading sync status...
          </div>
        ) : (
          <>
            {/* Status Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                <span className={`inline-block mt-1 text-sm font-medium px-2.5 py-0.5 rounded-full ${STATUS_BADGE[syncStatus?.status ?? 'idle'] ?? STATUS_BADGE.idle}`}>
                  {statusLabel(syncStatus?.status ?? 'idle')}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Last Sync</p>
                <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white">
                  {syncStatus?.last_bulk_sync
                    ? new Date(syncStatus.last_bulk_sync).toLocaleString()
                    : 'Never'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Cards</p>
                <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white">
                  {(syncStatus?.total_cards ?? 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Images Downloaded</p>
                <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white">
                  {(syncStatus?.total_images_downloaded ?? 0).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Error display */}
            {(error || syncStatus?.status === 'failed') && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
                {error || syncStatus?.error_message || 'Sync failed'}
              </div>
            )}

            {/* Success message */}
            {successMsg && (
              <div className="mb-4 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 text-sm">
                {successMsg}
              </div>
            )}

            {/* Progress bar */}
            {isSyncing && wsPhase && (
              <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  {wsPhase === 'data' ? 'Downloading card data...' : 'Downloading images...'}
                </p>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-indigo-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {wsCurrent.toLocaleString()} / {wsTotal.toLocaleString()} ({percentage}%)
                </p>
              </div>
            )}

            {/* Start Sync button */}
            <button
              onClick={handleStartSync}
              disabled={isSyncing}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                isSyncing
                  ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white'
              }`}
            >
              {isSyncing ? 'Sync in progress...' : 'Start Sync'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
