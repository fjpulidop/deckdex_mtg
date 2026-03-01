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
        const active = list.filter(
          (job) => job.status === 'running' || job.status === 'pending'
        );
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

  const fireJobFinished = useCallback((jobId: string) => {
    const cb = finishedCallbacksRef.current.get(jobId);
    if (cb) {
      finishedCallbacksRef.current.delete(jobId);
      cb();
    }
  }, []);

  const value: ActiveJobsContextValue = { jobs, addJob, removeJob };

  return (
    <ActiveJobsContext.Provider value={value}>
      {children}
    </ActiveJobsContext.Provider>
  );
}
