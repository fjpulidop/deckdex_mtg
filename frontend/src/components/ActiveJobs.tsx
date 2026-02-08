import React from 'react';
import { api } from '../api/client';
import { useWebSocket } from '../hooks/useApi';
import { JobLogModal } from './JobLogModal';

interface JobInfo {
  jobId: string;
  type: string;
  startedAt: Date;
}

interface ActiveJobsProps {
  jobs: JobInfo[];
  onJobCompleted: (jobId: string) => void;
  onJobFinished?: (jobId: string) => void;
}

interface JobState {
  expanded: boolean;
  isCancelling: boolean;
  finishedAt: Date | null;
}

export function ActiveJobs({ jobs, onJobCompleted, onJobFinished }: ActiveJobsProps) {
  const [jobStates, setJobStates] = React.useState<Record<string, JobState>>({});
  const [logModalJob, setLogModalJob] = React.useState<JobInfo | null>(null);

  // Don't show if no jobs exist
  if (jobs.length === 0) return null;

  const toggleExpanded = (jobId: string) => {
    setJobStates(prev => ({
      ...prev,
      [jobId]: {
        ...prev[jobId],
        expanded: !prev[jobId]?.expanded,
      }
    }));
  };

  const handleCancel = async (jobId: string) => {
    setJobStates(prev => ({
      ...prev,
      [jobId]: { ...prev[jobId], isCancelling: true }
    }));
    try {
      await api.cancelJob(jobId);
    } catch (e) {
      console.error('Failed to cancel job:', e);
      setJobStates(prev => ({
        ...prev,
        [jobId]: { ...prev[jobId], isCancelling: false }
      }));
    }
  };

  return (
    <>
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-600 shadow-lg">
        <div className="container mx-auto px-4 py-3">
          <div className="flex flex-col gap-3">
            {jobs.map(job => (
              <JobEntry
                key={job.jobId}
                job={job}
                state={jobStates[job.jobId] || { expanded: false, isCancelling: false, finishedAt: null }}
                onToggleExpanded={() => toggleExpanded(job.jobId)}
                onCancel={() => handleCancel(job.jobId)}
                onComplete={() => onJobCompleted(job.jobId)}
                onJobFinished={onJobFinished}
                onViewLog={() => setLogModalJob(job)}
                onFinish={(date) => setJobStates(prev => ({
                  ...prev,
                  [job.jobId]: { ...prev[job.jobId], finishedAt: date }
                }))}
              />
            ))}
          </div>
        </div>
      </div>
      {logModalJob && (
        <JobLogModal
          jobId={logModalJob.jobId}
          jobType={logModalJob.type}
          startedAt={logModalJob.startedAt}
          onClose={() => setLogModalJob(null)}
        />
      )}
    </>
  );
}

interface JobEntryProps {
  job: JobInfo;
  state: JobState;
  onToggleExpanded: () => void;
  onCancel: () => void;
  onComplete: () => void;
  onJobFinished?: (jobId: string) => void;
  onViewLog: () => void;
  onFinish: (date: Date) => void;
}

function JobEntry({ job, state, onToggleExpanded, onCancel, onComplete, onJobFinished, onViewLog, onFinish }: JobEntryProps) {
  const { status: wsStatus, progress, errors, complete, summary } = useWebSocket(job.jobId);
  const hasNotifiedComplete = React.useRef(false);
  const [elapsed, setElapsed] = React.useState('');

  const isCancelled = summary?.status === 'cancelled';
  const isError = summary?.status === 'error';
  const isFinished = complete;
  const isRunning = !isFinished;

  // Notify parent when job completes
  React.useEffect(() => {
    if (complete && !hasNotifiedComplete.current) {
      hasNotifiedComplete.current = true;
      onJobFinished?.(job.jobId);
      onFinish(new Date());
      // Remove after 5 seconds
      setTimeout(() => onComplete(), 5000);
    }
  }, [complete, job.jobId, onComplete, onFinish, onJobFinished]);

  // Reset on job change
  React.useEffect(() => {
    hasNotifiedComplete.current = false;
  }, [job.jobId]);

  // Live elapsed time counter
  React.useEffect(() => {
    const formatElapsed = (ms: number) => {
      const totalSecs = Math.floor(ms / 1000);
      if (totalSecs < 60) return `${totalSecs}s`;
      const mins = Math.floor(totalSecs / 60);
      const secs = totalSecs % 60;
      if (mins < 60) return `${mins}m ${secs}s`;
      const hrs = Math.floor(mins / 60);
      const remainMins = mins % 60;
      return `${hrs}h ${remainMins}m ${secs}s`;
    };

    const tick = () => {
      const end = state.finishedAt || new Date();
      setElapsed(formatElapsed(end.getTime() - job.startedAt.getTime()));
    };
    tick();

    if (isFinished) return;

    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [job.startedAt, isFinished, state.finishedAt]);

  const borderColor = 
    isCancelled ? 'border-orange-600' :
    isError ? 'border-red-600' :
    isFinished ? 'border-green-600' :
    'border-blue-600';

  const statusIcon = 
    isCancelled ? '⊗' :
    isError ? '✗' :
    isFinished ? '✓' :
    '🔄';

  const statusText =
    isCancelled ? 'Cancelled' :
    isError ? 'Failed' :
    isFinished ? 'Completed' :
    wsStatus === 'connected' ? 'Connected' :
    wsStatus === 'connecting' ? 'Connecting...' :
    'Disconnected';

  const statusColor =
    isCancelled ? 'text-orange-600 dark:text-orange-400' :
    isError ? 'text-red-600 dark:text-red-400' :
    isFinished ? 'text-green-600 dark:text-green-400' :
    wsStatus === 'connected' ? 'text-green-600 dark:text-green-400' :
    'text-yellow-600 dark:text-yellow-400';

  return (
    <div className={`border-l-4 ${borderColor} bg-white dark:bg-gray-700 rounded shadow-sm`}>
      {/* Main row */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Status icon */}
        <div className="flex-shrink-0 text-xl">
          {isRunning && statusIcon === '🔄' ? (
            <div className="w-5 h-5 border-2 border-gray-300 dark:border-gray-500 border-t-blue-600 dark:border-t-blue-400 rounded-full animate-spin" />
          ) : (
            <span className={statusColor}>{statusIcon}</span>
          )}
        </div>

        {/* Job info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-900 dark:text-white">{job.type}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              wsStatus === 'connected' ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300' :
              wsStatus === 'connecting' ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300' :
              'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
            }`}>
              {statusText}
            </span>
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {isFinished ? (
              <span>
                {isCancelled ? `Stopped at ${progress.current}/${progress.total} cards` :
                 isError ? summary?.error || 'An error occurred' :
                 `${progress.total} cards processed`}
                {errors.length > 0 && ` • ${errors.length} errors`}
              </span>
            ) : (
              <span>
                {progress.percentage.toFixed(0)}% — {progress.current}/{progress.total} cards
                {state.isCancelling && ' • Stopping...'}
              </span>
            )}
          </div>
        </div>

        {/* Progress bar (only when running) */}
        {isRunning && (
          <div className="flex-shrink-0 w-32">
            <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-300 ${
                  state.isCancelling ? 'bg-orange-400' : 'bg-blue-600'
                }`}
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Timer */}
        <div className="flex-shrink-0 text-xs text-gray-500 dark:text-gray-400 font-mono tabular-nums min-w-[60px] text-right">
          ⏱ {elapsed}
        </div>

        {/* Actions */}
        <div className="flex-shrink-0 flex items-center gap-2">
          {isRunning && (
            <button
              onClick={onCancel}
              disabled={state.isCancelling}
              className={`px-3 py-1 text-xs rounded transition ${
                state.isCancelling
                  ? 'bg-orange-100 dark:bg-orange-900/40 text-orange-500 dark:text-orange-300 cursor-not-allowed'
                  : 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600'
              }`}
            >
              {state.isCancelling ? 'Stopping...' : 'Stop'}
            </button>
          )}
          <button
            onClick={onViewLog}
            className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-500 transition"
          >
            View log
          </button>
          {errors.length > 0 && (
            <button
              onClick={onToggleExpanded}
              className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-500 transition"
            >
              {state.expanded ? 'Hide' : 'Show'} errors
            </button>
          )}
        </div>
      </div>

      {/* Expanded errors section */}
      {state.expanded && errors.length > 0 && (
        <div className="px-4 pb-3 border-t border-gray-100 dark:border-gray-600">
          <div className="mt-3 max-h-40 overflow-y-auto bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded p-3">
            <h4 className="text-xs font-medium text-red-800 dark:text-red-200 mb-2">
              Errors ({errors.length})
            </h4>
            {errors.slice(0, 20).map((error, index) => (
              <div key={index} className="text-xs text-red-700 dark:text-red-300 mb-1">
                • {error.card_name}: {error.message}
              </div>
            ))}
            {errors.length > 20 && (
              <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                ... and {errors.length - 20} more errors
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
