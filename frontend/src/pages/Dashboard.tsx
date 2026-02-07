import { useState, useCallback } from 'react';
import { useCards } from '../hooks/useApi';
import { StatsCards } from '../components/StatsCards';
import { Filters } from '../components/Filters';
import { CardTable } from '../components/CardTable';
import { ActionButtons } from '../components/ActionButtons';
import { ProcessModal } from '../components/ProcessModal';
import { ActiveJobs } from '../components/ActiveJobs';

interface JobInfo {
  jobId: string;
  type: string;
  startedAt: Date;
}

export function Dashboard() {
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('all');
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [backgroundJobs, setBackgroundJobs] = useState<JobInfo[]>([]);

  // Fetch cards with filters
  const { data: cards, isLoading, error } = useCards({
    search: search || undefined,
    limit: 1000,
  });

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
    setActiveJobId(jobId);
    setBackgroundJobs(prev => [...prev, {
      jobId,
      type: jobType,
      startedAt: new Date(),
    }]);
  }, []);

  const handleCloseModal = useCallback(() => {
    // Don't remove from backgroundJobs - it keeps tracking
    setActiveJobId(null);
  }, []);

  const handleSelectJob = useCallback((jobId: string) => {
    setActiveJobId(jobId);
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

        {/* Process Modal */}
        {activeJobId && (
          <ProcessModal
            jobId={activeJobId}
            startedAt={backgroundJobs.find(j => j.jobId === activeJobId)?.startedAt}
            onClose={handleCloseModal}
            onComplete={handleJobCompleted}
          />
        )}
      </div>

      {/* Floating Active Jobs bar */}
      <ActiveJobs
        jobs={backgroundJobs}
        activeJobId={activeJobId}
        onSelectJob={handleSelectJob}
        onJobCompleted={handleJobCompleted}
      />
    </div>
  );
}
