import { useState, useCallback, useEffect } from 'react';
import { useCards } from '../hooks/useApi';
import { StatsCards } from '../components/StatsCards';
import { Filters } from '../components/Filters';
import { CardTable } from '../components/CardTable';
import { ActionButtons } from '../components/ActionButtons';
import { ActiveJobs } from '../components/ActiveJobs';
import { api } from '../api/client';

interface JobInfo {
  jobId: string;
  type: string;
  startedAt: Date;
}

export function Dashboard() {
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('all');
  const [backgroundJobs, setBackgroundJobs] = useState<JobInfo[]>([]);

  // Fetch cards with filters
  const { data: cards, isLoading, error } = useCards({
    search: search || undefined,
    limit: 1000,
  });

  // Restore active jobs from backend on mount
  useEffect(() => {
    const restoreJobs = async () => {
      try {
        const jobs = await api.getJobs();
        // Only restore jobs that are still running (not complete, error, or cancelled)
        const activeJobs = jobs.filter(job => 
          job.status === 'running' || job.status === 'pending'
        );
        const restoredJobs = activeJobs.map(job => ({
          jobId: job.job_id,
          type: job.job_type,
          startedAt: job.start_time ? new Date(job.start_time) : new Date(),
        }));
        if (restoredJobs.length > 0) {
          setBackgroundJobs(restoredJobs);
        }
      } catch (err) {
        // Log error but don't block dashboard load
        console.error('Failed to restore jobs:', err);
      }
    };
    
    restoreJobs();
  }, []);

  // Show error if backend is not accessible
  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-lg">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Backend Connection Error</h1>
          <p className="text-gray-700 mb-4">
            Cannot connect to the backend API. Please ensure the backend is running:
          </p>
          <pre className="bg-gray-100 p-4 rounded text-sm mb-4">
cd backend{'\n'}
uvicorn api.main:app --reload
          </pre>
          <p className="text-gray-600 text-sm">
            The backend should be running on http://localhost:8000
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Filter cards by rarity (client-side)
  const filteredCards = cards?.filter(card => {
    if (rarity === 'all') return true;
    return card.rarity?.toLowerCase() === rarity;
  }) || [];

  const handleSearchChange = (value: string) => {
    setSearch(value);
  };

  const handleRarityChange = (value: string) => {
    setRarity(value);
  };

  const handleClearFilters = () => {
    setSearch('');
    setRarity('all');
  };

  const handleJobStarted = useCallback((jobId: string, jobType: string) => {
    setBackgroundJobs(prev => [...prev, {
      jobId,
      type: jobType,
      startedAt: new Date(),
    }]);
  }, []);

  const handleJobCompleted = useCallback((jobId: string) => {
    setBackgroundJobs(prev => prev.filter(j => j.jobId !== jobId));
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            DeckDex MTG
          </h1>
          <p className="text-gray-600">
            Manage your Magic: The Gathering collection
          </p>
        </div>

        {/* Stats Cards */}
        <StatsCards />

        {/* Action Buttons */}
        <ActionButtons onJobStarted={handleJobStarted} />

        {/* Filters */}
        <Filters
          onSearchChange={handleSearchChange}
          onRarityChange={handleRarityChange}
          onClearFilters={handleClearFilters}
        />

        {/* Card Table */}
        <CardTable cards={filteredCards} isLoading={isLoading} />
      </div>

      {/* Active Jobs Bar */}
      <ActiveJobs
        jobs={backgroundJobs}
        onJobCompleted={handleJobCompleted}
      />
    </div>
  );
}
