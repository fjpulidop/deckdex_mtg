import { useState, useRef, useEffect } from 'react';
import { useTriggerProcess, useTriggerPriceUpdate } from '../hooks/useApi';

interface ActionButtonsProps {
  onJobStarted: (jobId: string, jobType: string) => void;
}

export function ActionButtons({ onJobStarted }: ActionButtonsProps) {
  const triggerProcess = useTriggerProcess();
  const triggerPriceUpdate = useTriggerPriceUpdate();
  const [processScopeOpen, setProcessScopeOpen] = useState(false);
  const processDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!processScopeOpen) return;
    const onOutside = (e: MouseEvent) => {
      if (processDropdownRef.current && !processDropdownRef.current.contains(e.target as Node)) {
        setProcessScopeOpen(false);
      }
    };
    document.addEventListener('click', onOutside);
    return () => document.removeEventListener('click', onOutside);
  }, [processScopeOpen]);

  const handleProcess = async (scope: 'all' | 'new_only') => {
    setProcessScopeOpen(false);
    try {
      const result = await triggerProcess.mutateAsync({ scope });
      const label = scope === 'new_only' ? 'Process new cards only' : 'Process all cards';
      onJobStarted(result.job_id, label);
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
      <div className="flex flex-wrap gap-4 items-center">
        <div className="relative" ref={processDropdownRef}>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setProcessScopeOpen(!processScopeOpen); }}
            disabled={isProcessing}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
          >
            {triggerProcess.isPending ? 'Starting...' : 'Process Cards'}
          </button>
          {processScopeOpen && (
            <div className="absolute left-0 top-full mt-1 z-10 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[220px]">
              <button
                type="button"
                onClick={() => handleProcess('new_only')}
                className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100"
              >
                New added cards (with only the name)
              </button>
              <button
                type="button"
                onClick={() => handleProcess('all')}
                className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100"
              >
                All cards
              </button>
            </div>
          )}
        </div>
        
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
