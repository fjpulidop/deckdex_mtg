import React from 'react';
import { api } from '../api/client';

interface JobInfo {
  jobId: string;
  type: string;
  startedAt: Date;
}

interface ActiveJobsProps {
  jobs: JobInfo[];
  activeJobId: string | null;
  onSelectJob: (jobId: string) => void;
  onJobCompleted: (jobId: string) => void;
}

interface JobProgress {
  status: string;
  percentage: number;
  current: number;
  total: number;
}

export function ActiveJobs({ jobs, activeJobId, onSelectJob, onJobCompleted }: ActiveJobsProps) {
  const [jobProgress, setJobProgress] = React.useState<Record<string, JobProgress>>({});

  // Poll job status for all background jobs
  React.useEffect(() => {
    if (jobs.length === 0) return;

    const pollJobs = async () => {
      for (const job of jobs) {
        try {
          const status = await api.getJobStatus(job.jobId);
          setJobProgress(prev => ({
            ...prev,
            [job.jobId]: {
              status: status.status,
              percentage: status.progress?.percentage || 0,
              current: status.progress?.current || 0,
              total: status.progress?.total || 0,
            }
          }));

          // Remove finished jobs after a delay
          if (status.status === 'complete' || status.status === 'error' || status.status === 'cancelled') {
            setTimeout(() => onJobCompleted(job.jobId), 5000);
          }
        } catch {
          // Job might have been cleaned up
        }
      }
    };

    pollJobs();
    const interval = setInterval(pollJobs, 2000);
    return () => clearInterval(interval);
  }, [jobs, onJobCompleted]);

  // Don't show if no background jobs (or all are being viewed in modal)
  const backgroundJobs = jobs.filter(j => j.jobId !== activeJobId);
  if (backgroundJobs.length === 0) return null;

  const formatElapsed = (startedAt: Date) => {
    const seconds = Math.floor((Date.now() - startedAt.getTime()) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  return (
    <div className="fixed bottom-4 right-4 z-40 flex flex-col gap-2">
      {backgroundJobs.map(job => {
        const progress = jobProgress[job.jobId];
        const isComplete = progress?.status === 'complete';
        const isError = progress?.status === 'error';
        const isCancelled = progress?.status === 'cancelled';
        const isRunning = progress?.status === 'running';
        const pct = progress?.percentage || 0;

        return (
          <button
            key={job.jobId}
            onClick={() => onSelectJob(job.jobId)}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-left transition-all hover:scale-105 cursor-pointer min-w-[280px] ${
              isComplete ? 'bg-green-600 text-white' :
              isCancelled ? 'bg-orange-600 text-white' :
              isError ? 'bg-red-600 text-white' :
              'bg-gray-800 text-white'
            }`}
          >
            {/* Spinner / Status icon */}
            <div className="flex-shrink-0">
              {isComplete ? (
                <span className="text-lg">&#10003;</span>
              ) : isCancelled ? (
                <span className="text-lg">&#8856;</span>
              ) : isError ? (
                <span className="text-lg">&#10007;</span>
              ) : (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{job.type}</div>
              <div className="text-xs opacity-80">
                {isComplete ? 'Completed' :
                 isCancelled ? 'Cancelled' :
                 isError ? 'Failed' :
                 isRunning ? `${pct.toFixed(0)}% — ${progress.current}/${progress.total}` :
                 'Starting...'}
                {' · '}{formatElapsed(job.startedAt)}
              </div>
            </div>

            {/* Progress ring */}
            {isRunning && (
              <div className="flex-shrink-0 w-10 h-10 relative">
                <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="3" />
                  <circle
                    cx="18" cy="18" r="15" fill="none" stroke="white" strokeWidth="3"
                    strokeDasharray={`${pct * 0.942} 94.2`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold">
                  {pct.toFixed(0)}%
                </span>
              </div>
            )}

            {/* Click hint */}
            <div className="flex-shrink-0 text-xs opacity-60">
              Click to view
            </div>
          </button>
        );
      })}
    </div>
  );
}
