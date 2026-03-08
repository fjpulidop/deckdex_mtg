/* eslint-disable react-refresh/only-export-components -- context files export both Provider and hook by convention */
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { api } from '../api/client';

export interface JobInfo {
  jobId: string;
  type: string;
  startedAt: Date;
}

export type JobFinishedCallback = () => void;

interface ActiveJobsContextValue {
  jobs: JobInfo[];
  addJob: (jobId: string, jobType: string, onFinished?: JobFinishedCallback) => void;
  removeJob: (jobId: string) => void;
}

const ActiveJobsContext = createContext<ActiveJobsContextValue | null>(null);

export function useActiveJobs(): ActiveJobsContextValue {
  const ctx = useContext(ActiveJobsContext);
  if (!ctx) throw new Error('useActiveJobs must be used within ActiveJobsProvider');
  return ctx;
}

export function ActiveJobsProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<JobInfo[]>([]);
  const finishedCallbacksRef = useRef<Map<string, JobFinishedCallback>>(new Map());

  useEffect(() => {
    const restoreJobs = async () => {
      try {
        const list = await api.getJobs();
        const active = list.filter((job) => job.status === 'running' || job.status === 'pending');
        if (active.length > 0) {
          setJobs(
            active.map((job) => ({
              jobId: job.job_id,
              type: job.job_type,
              startedAt: job.start_time ? new Date(job.start_time) : new Date(),
            }))
          );
        }
      } catch (err) {
        console.error('Failed to restore jobs:', err);
      }
    };
    restoreJobs();
  }, []);

  // Re-sync job list when the tab regains visibility (debounced 2s)
  const lastSyncRef = useRef(0);
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState !== 'visible') return;
      const now = Date.now();
      if (now - lastSyncRef.current < 2000) return; // debounce
      lastSyncRef.current = now;
      api.getJobs().then((list) => {
        const activeList = list.filter((j) => j.status === 'running' || j.status === 'pending');
        const activeIds = new Set(activeList.map((j) => j.job_id));
        setJobs((prev) => {
          // Keep locally-added jobs that the server still reports as active,
          // plus add any new active ones from the server.
          const existing = new Set(prev.map((j) => j.jobId));
          const kept = prev.filter((j) => activeIds.has(j.jobId));
          const added = activeList
            .filter((j) => !existing.has(j.job_id))
            .map((j) => ({
              jobId: j.job_id,
              type: j.job_type,
              startedAt: j.start_time ? new Date(j.start_time) : new Date(),
            }));
          return [...kept, ...added];
        });
      }).catch(() => { /* network error — keep current state */ });
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, []);

  const addJob = useCallback((jobId: string, jobType: string, onFinished?: JobFinishedCallback) => {
    setJobs((prev) => [
      ...prev,
      { jobId, type: jobType, startedAt: new Date() },
    ]);
    if (onFinished) {
      finishedCallbacksRef.current.set(jobId, onFinished);
    }
  }, []);

  const removeJob = useCallback((jobId: string) => {
    setJobs((prev) => prev.filter((j) => j.jobId !== jobId));
    finishedCallbacksRef.current.delete(jobId);
  }, []);

  const value: ActiveJobsContextValue = { jobs, addJob, removeJob };

  return (
    <ActiveJobsContext.Provider value={value}>
      {children}
    </ActiveJobsContext.Provider>
  );
}
