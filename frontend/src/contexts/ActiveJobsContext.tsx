import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import { ActiveJobs } from '../components/ActiveJobs';

export interface JobInfo {
  jobId: string;
  type: string;
  startedAt: Date;
}

interface ActiveJobsContextValue {
  jobs: JobInfo[];
  addJob: (jobId: string, jobType: string) => void;
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

  const addJob = useCallback((jobId: string, jobType: string) => {
    setJobs((prev) => [
      ...prev,
      { jobId, type: jobType, startedAt: new Date() },
    ]);
  }, []);

  const removeJob = useCallback((jobId: string) => {
    setJobs((prev) => prev.filter((j) => j.jobId !== jobId));
  }, []);

  const value: ActiveJobsContextValue = { jobs, addJob, removeJob };
  const jobsBarHeight =
    jobs.length > 0 ? 24 + jobs.length * 72 : 0;

  return (
    <ActiveJobsContext.Provider value={value}>
      <div
        style={
          jobsBarHeight > 0 ? { paddingBottom: jobsBarHeight } : undefined
        }
      >
        {children}
      </div>
      <ActiveJobs jobs={jobs} onJobCompleted={removeJob} />
    </ActiveJobsContext.Provider>
  );
}
