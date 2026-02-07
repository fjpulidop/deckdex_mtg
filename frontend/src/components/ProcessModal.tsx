import React from 'react';
import { useWebSocket } from '../hooks/useApi';
import { api } from '../api/client';

interface ProcessModalProps {
  jobId: string | null;
  startedAt?: Date;
  onClose: () => void;
  onComplete?: (jobId: string) => void;
}

export function ProcessModal({ jobId, startedAt, onClose, onComplete }: ProcessModalProps) {
  const { status, progress, errors, complete, summary } = useWebSocket(jobId);
  const hasNotifiedComplete = React.useRef(false);
  const [isCancelling, setIsCancelling] = React.useState(false);
  const [elapsed, setElapsed] = React.useState('');
  const finishedAtRef = React.useRef<Date | null>(null);

  const isCancelled = summary?.status === 'cancelled';
  const isFinished = complete;

  // Notify parent when job completes
  React.useEffect(() => {
    if (complete && jobId && onComplete && !hasNotifiedComplete.current) {
      hasNotifiedComplete.current = true;
      onComplete(jobId);
    }
  }, [complete, jobId, onComplete]);

  // Capture the moment the job finishes so the timer stops
  React.useEffect(() => {
    if (isFinished && !finishedAtRef.current) {
      finishedAtRef.current = new Date();
    }
  }, [isFinished]);

  // Reset refs when jobId changes
  React.useEffect(() => {
    hasNotifiedComplete.current = false;
    setIsCancelling(false);
    finishedAtRef.current = null;
  }, [jobId]);

  // Live elapsed time counter
  React.useEffect(() => {
    if (!startedAt) { setElapsed(''); return; }

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
      const end = finishedAtRef.current || new Date();
      setElapsed(formatElapsed(end.getTime() - startedAt.getTime()));
    };
    tick();

    // Stop ticking once finished
    if (isFinished) return;

    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [startedAt, isFinished]);

  const handleCancel = async () => {
    if (!jobId || isCancelling) return;
    setIsCancelling(true);
    try {
      await api.cancelJob(jobId);
      // The WebSocket will receive a 'complete' event with status 'cancelled'
    } catch (e: any) {
      console.error('Failed to cancel job:', e);
      setIsCancelling(false);
    }
  };

  if (!jobId) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {isCancelled ? 'Process Cancelled' :
                 isFinished ? 'Process Complete' : 'Processing...'}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Job ID: {jobId.substring(0, 8)}...
              </p>
            </div>
            {elapsed && (
              <div className="flex items-center gap-1.5 text-sm text-gray-500 bg-gray-100 px-3 py-1.5 rounded-lg">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-mono tabular-nums">{elapsed}</span>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {/* Connection Status */}
          <div className="mb-4">
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              isCancelled ? 'bg-orange-100 text-orange-800' :
              status === 'connected' ? 'bg-green-100 text-green-800' :
              status === 'connecting' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {isCancelled ? '⊘ Cancelled' :
               status === 'connected' ? '✓ Connected' :
               status === 'connecting' ? '⏳ Connecting...' :
               isFinished ? '✓ Done' : '✗ Disconnected'}
            </span>
          </div>

          {/* Progress Bar */}
          {!isFinished && (
            <div className="mb-6">
              <div className="flex justify-between text-sm text-gray-700 mb-2">
                <span>Progress</span>
                <span>{progress.percentage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-4 transition-all duration-300 rounded-full ${
                    isCancelling ? 'bg-orange-400' : 'bg-blue-600'
                  }`}
                  style={{ width: `${progress.percentage}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {isCancelling
                  ? 'Stopping...'
                  : progress.total > 0
                    ? `Processing ${progress.current} / ${progress.total} cards`
                    : 'Initializing...'}
              </p>
            </div>
          )}

          {/* Completion Message */}
          {isFinished && (
            <div className={`mb-6 p-4 rounded-lg border ${
              isCancelled
                ? 'bg-orange-50 border-orange-200'
                : summary?.status === 'error'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-green-50 border-green-200'
            }`}>
              {isCancelled ? (
                <>
                  <p className="text-orange-800 font-medium">⊘ Process cancelled</p>
                  <p className="text-sm text-orange-700 mt-1">
                    The job was stopped by user.
                    {progress.total > 0 && ` Progress was at ${progress.current}/${progress.total} cards (${progress.percentage.toFixed(0)}%).`}
                  </p>
                </>
              ) : summary?.status === 'error' ? (
                <>
                  <p className="text-red-800 font-medium">✗ Process failed</p>
                  <p className="text-sm text-red-700 mt-1">
                    {summary?.error || 'An unknown error occurred'}
                  </p>
                </>
              ) : (
                <>
                  <p className="text-green-800 font-medium">✓ Process completed!</p>
                  <p className="text-sm text-green-700 mt-1">
                    {progress.total > 0 && `${progress.total} cards processed`}
                    {errors.length > 0 && ` (${errors.length} errors)`}
                  </p>
                </>
              )}
            </div>
          )}

          {/* Errors */}
          {errors.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">
                Errors ({errors.length})
              </h3>
              <div className="max-h-40 overflow-y-auto bg-red-50 border border-red-200 rounded p-3">
                {errors.slice(0, 20).map((error, index) => (
                  <div key={index} className="text-sm text-red-800 mb-1">
                    • {error.card_name}: {error.message}
                  </div>
                ))}
                {errors.length > 20 && (
                  <p className="text-sm text-red-600 mt-2">
                    ... and {errors.length - 20} more errors
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          {isFinished ? (
            <button
              onClick={onClose}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              Done
            </button>
          ) : (
            <>
              <button
                onClick={handleCancel}
                disabled={isCancelling}
                className={`px-6 py-2 rounded-lg transition font-medium ${
                  isCancelling
                    ? 'bg-orange-200 text-orange-500 cursor-not-allowed'
                    : 'bg-red-600 text-white hover:bg-red-700'
                }`}
              >
                {isCancelling ? 'Stopping...' : 'Stop'}
              </button>
              <button
                onClick={onClose}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
              >
                Minimize
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
