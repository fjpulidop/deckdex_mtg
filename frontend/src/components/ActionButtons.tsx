import { useTriggerProcess, useTriggerPriceUpdate } from '../hooks/useApi';

interface ActionButtonsProps {
  onJobStarted: (jobId: string, jobType: string) => void;
}

export function ActionButtons({ onJobStarted }: ActionButtonsProps) {
  const triggerProcess = useTriggerProcess();
  const triggerPriceUpdate = useTriggerPriceUpdate();

  const handleProcess = async () => {
    try {
      const result = await triggerProcess.mutateAsync();
      onJobStarted(result.job_id, 'Process Cards');
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    }
  };

  const handlePriceUpdate = async () => {
    try {
      const result = await triggerPriceUpdate.mutateAsync();
      onJobStarted(result.job_id, 'Update Prices');
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    }
  };

  const isProcessing = triggerProcess.isPending || triggerPriceUpdate.isPending;

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Actions</h2>
      <div className="flex flex-wrap gap-4">
        <button
          onClick={handleProcess}
          disabled={isProcessing}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
        >
          {triggerProcess.isPending ? 'Starting...' : 'Process Cards'}
        </button>
        
        <button
          onClick={handlePriceUpdate}
          disabled={isProcessing}
          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
        >
          {triggerPriceUpdate.isPending ? 'Starting...' : 'Update Prices'}
        </button>
      </div>
    </div>
  );
}
