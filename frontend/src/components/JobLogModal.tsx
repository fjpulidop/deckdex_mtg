import React from 'react';
import { useTranslation } from 'react-i18next';
import { useWebSocket } from '../hooks/useApi';
import { AccessibleModal } from './AccessibleModal';

interface JobLogModalProps {
  jobId: string;
  jobType: string;
  startedAt: Date;
  onClose: () => void;
}

export function JobLogModal({ jobId, jobType, startedAt, onClose }: JobLogModalProps) {
  const { t } = useTranslation();
  const { status: wsStatus, progress, errors, complete, summary } = useWebSocket(jobId);
  const [elapsed, setElapsed] = React.useState('');

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
    const tick = () => setElapsed(formatElapsed(Date.now() - startedAt.getTime()));
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [startedAt]);

  const isCancelled = summary?.status === 'cancelled';
  const isError = summary?.status === 'error';
  const statusText =
    isCancelled ? t('jobLog.status.cancelled') :
    isError ? t('jobLog.status.failed') :
    complete ? t('jobLog.status.completed') :
    wsStatus === 'connected' ? t('jobLog.status.connected') :
    wsStatus === 'connecting' ? t('jobLog.status.connecting') :
    t('jobLog.status.disconnected');

  return (
    <AccessibleModal isOpen titleId="job-log-modal-title" onClose={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[85vh] flex flex-col"
      >
        <div className="p-4 border-b border-gray-200 dark:border-gray-600 flex justify-between items-center">
          <div>
            <h2 id="job-log-modal-title" className="text-lg font-semibold text-gray-900 dark:text-white">
              {jobType} — {t('jobLog.title')}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {statusText} · ⏱ {elapsed}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('common.close')}
            className="px-3 py-1 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            {t('jobLog.close')}
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex-1 space-y-4">
          <div>
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
              <span>{t('jobLog.progress')}</span>
              <span>{progress.percentage.toFixed(0)}% — {t('jobLog.progressCount', { current: progress.current, total: progress.total })}</span>
            </div>
            <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 dark:bg-blue-500 transition-all duration-300"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
          </div>

          {complete && (
            <div className="text-sm text-gray-700 dark:text-gray-300">
              {isCancelled && <p>{t('jobLog.stoppedAt', { current: progress.current, total: progress.total })}</p>}
              {isError && <p className="text-red-600 dark:text-red-400">{summary?.error || t('jobLog.errorOccurred')}</p>}
              {!isCancelled && !isError && <p>{t('jobLog.cardsProcessed', { total: progress.total })}</p>}
            </div>
          )}

          {errors.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                {t('jobLog.errors', { count: errors.length })}
              </h3>
              <div className="max-h-48 overflow-y-auto bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3 text-xs text-red-800 dark:text-red-200">
                {errors.map((err, i) => (
                  <div key={i} className="mb-1">
                    • {err.card_name}: {err.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AccessibleModal>
  );
}
