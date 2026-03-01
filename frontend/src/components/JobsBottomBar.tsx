/**
 * JobsBottomBar — permanent fixed bottom-right bar.
 *
 * Collapsed: discrete pill button (always visible).
 * Expanded: panel with Active and History tabs.
 * Auto-expands when a new active job is detected.
 */
import React, { useState, useEffect, useRef } from 'react';
import { api, JobHistoryItem } from '../api/client';
import { useActiveJobs } from '../contexts/ActiveJobsContext';
import { useWebSocket } from '../hooks/useApi';
import { JobLogModal } from './JobLogModal';

// ---------------------------------------------------------------------------
// Job entry (active)
// ---------------------------------------------------------------------------
interface ActiveJobEntryProps {
  jobId: string;
  type: string;
  startedAt: Date;
  onComplete: (jobId: string) => void;
  onFinished?: (jobId: string) => void;
}

function ActiveJobEntry({ jobId, type, startedAt, onComplete, onFinished }: ActiveJobEntryProps) {
  const { status: wsStatus, progress, complete, summary } = useWebSocket(jobId);
  const hasNotified = useRef(false);
  const [elapsed, setElapsed] = useState('');
  const [cancelling, setCancelling] = useState(false);

  const isCancelled = summary?.status === 'cancelled';
  const isError = summary?.status === 'error';
  const isFinished = complete;

  useEffect(() => {
    if (complete && !hasNotified.current) {
      hasNotified.current = true;
      onFinished?.(jobId);
      setTimeout(() => onComplete(jobId), 5000);
    }
  }, [complete, jobId, onComplete, onFinished]);

  useEffect(() => {
    const fmt = (ms: number) => {
      const s = Math.floor(ms / 1000);
      if (s < 60) return `${s}s`;
      const m = Math.floor(s / 60), rs = s % 60;
      return `${m}m ${rs}s`;
    };
    const tick = () => setElapsed(fmt(Date.now() - startedAt.getTime()));
    tick();
    if (isFinished) return;
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt, isFinished]);

  const handleCancel = async () => {
    setCancelling(true);
    try { await api.cancelJob(jobId); } catch { setCancelling(false); }
  };

  const borderColor = isCancelled ? 'border-orange-500' : isError ? 'border-red-500' : isFinished ? 'border-green-500' : 'border-blue-500';
  const statusText = isCancelled ? 'Cancelado' : isError ? 'Error' : isFinished ? 'Completado' : `${Math.round(progress.percentage)}% — ${progress.current}/${progress.total}`;

  return (
    <div className={`border-l-4 ${borderColor} bg-white dark:bg-gray-700 rounded px-3 py-2 flex items-center gap-3`}>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-900 dark:text-white truncate">{type}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{statusText}</div>
      </div>
      {!isFinished && (
        <div className="w-20 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
          <div className="h-full bg-blue-500 transition-all" style={{ width: `${progress.percentage}%` }} />
        </div>
      )}
      <span className="text-xs font-mono text-gray-400">{elapsed}</span>
      {!isFinished && !cancelling && (
        <button
          onClick={handleCancel}
          className="text-xs text-red-500 hover:text-red-700 dark:text-red-400"
        >Stop</button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// History item row
// ---------------------------------------------------------------------------
function HistoryRow({ item, onViewLog }: { item: JobHistoryItem; onViewLog: (item: JobHistoryItem) => void }) {
  const statusIcon = item.status === 'complete' ? '✓' : item.status === 'error' ? '✗' : item.status === 'cancelled' ? '⊗' : '○';
  const statusColor = item.status === 'complete' ? 'text-green-600 dark:text-green-400' : item.status === 'error' ? 'text-red-500' : 'text-gray-400';
  const date = item.created_at ? new Date(item.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <div className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded">
      <span className={`font-mono text-sm ${statusColor}`}>{statusIcon}</span>
      <div className="flex-1 min-w-0">
        <span className="text-sm text-gray-900 dark:text-white">{item.type}</span>
        <span className="ml-2 text-xs text-gray-400">{date}</span>
      </div>
      <button
        onClick={() => onViewLog(item)}
        className="text-xs text-blue-500 hover:text-blue-700 dark:text-blue-400 shrink-0"
      >
        Ver log
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function JobsBottomBar() {
  const { jobs, removeJob } = useActiveJobs();
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState<'active' | 'history'>('active');
  const [history, setHistory] = useState<JobHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [logItem, setLogItem] = useState<{ jobId: string; type: string; startedAt: Date } | null>(null);
  const prevJobCount = useRef(jobs.length);

  // Auto-expand when a new job starts
  useEffect(() => {
    if (jobs.length > prevJobCount.current) {
      setExpanded(true);
      setTab('active');
    }
    prevJobCount.current = jobs.length;
  }, [jobs.length]);

  // Load history when History tab opens
  useEffect(() => {
    if (tab === 'history' && expanded) {
      setLoadingHistory(true);
      api.getJobHistory().then(setHistory).catch(() => setHistory([])).finally(() => setLoadingHistory(false));
    }
  }, [tab, expanded]);

  const handleViewHistoryLog = (item: JobHistoryItem) => {
    setLogItem({ jobId: item.job_id, type: item.type, startedAt: item.created_at ? new Date(item.created_at) : new Date() });
  };

  return (
    <>
      {/* Fixed container */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
        {/* Expanded panel */}
        {expanded && (
          <div className="w-96 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl shadow-2xl overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b border-gray-200 dark:border-gray-600">
              {(['active', 'history'] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`flex-1 py-2 text-sm font-medium capitalize transition ${tab === t ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}`}
                >
                  {t === 'active' ? `Active${jobs.length > 0 ? ` (${jobs.length})` : ''}` : 'History'}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="max-h-72 overflow-y-auto p-2 space-y-2">
              {tab === 'active' && (
                jobs.length === 0
                  ? <p className="text-center text-sm text-gray-400 py-6">No active jobs</p>
                  : jobs.map(job => (
                    <ActiveJobEntry
                      key={job.jobId}
                      jobId={job.jobId}
                      type={job.type}
                      startedAt={job.startedAt}
                      onComplete={removeJob}
                    />
                  ))
              )}
              {tab === 'history' && (
                loadingHistory
                  ? <p className="text-center text-sm text-gray-400 py-6">Loading…</p>
                  : history.length === 0
                    ? <p className="text-center text-sm text-gray-400 py-6">No job history yet</p>
                    : history.map(item => (
                      <HistoryRow key={item.job_id} item={item} onViewLog={handleViewHistoryLog} />
                    ))
              )}
            </div>
          </div>
        )}

        {/* Pill toggle button */}
        <button
          onClick={() => setExpanded(e => !e)}
          className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg text-sm font-medium transition ${jobs.length > 0 ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
        >
          {jobs.length > 0 && <span className="w-2 h-2 rounded-full bg-white animate-pulse" />}
          Jobs {jobs.length > 0 ? `(${jobs.length})` : ''} {expanded ? '▼' : '▲'}
        </button>
      </div>

      {/* Log modal */}
      {logItem && (
        <JobLogModal
          jobId={logItem.jobId}
          jobType={logItem.type}
          startedAt={logItem.startedAt}
          onClose={() => setLogItem(null)}
        />
      )}
    </>
  );
}
