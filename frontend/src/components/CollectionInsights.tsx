import { useState, useRef, useEffect } from 'react';
import { Card, InsightCatalogEntry, InsightResponse as InsightResponseType } from '../api/client';
import { useInsightsCatalog, useInsightsSuggestions, useInsightExecute } from '../hooks/useApi';
import { InsightResponse } from './insights/InsightResponse';

interface Props {
  onCardClick?: (card: Card) => void;
}

function fuzzyMatch(query: string, entry: InsightCatalogEntry): boolean {
  if (!query.trim()) return false;
  const q = query.toLowerCase();
  if (entry.label.toLowerCase().includes(q)) return true;
  return entry.keywords.some(k => k.toLowerCase().includes(q));
}

export function CollectionInsights({ onCardClick }: Props) {
  const [searchValue, setSearchValue] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [activeResult, setActiveResult] = useState<InsightResponseType | null>(null);
  const [executingId, setExecutingId] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { data: catalog = [] } = useInsightsCatalog();
  const { data: suggestions = [] } = useInsightsSuggestions();
  const execute = useInsightExecute();

  // Filter catalog by search input
  const filteredResults = searchValue.trim()
    ? catalog.filter(e => fuzzyMatch(searchValue, e))
    : [];

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current && !inputRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleInputChange = (value: string) => {
    setSearchValue(value);
    setDropdownOpen(value.trim().length > 0);
  };

  const runInsight = async (insightId: string) => {
    setDropdownOpen(false);
    setSearchValue('');
    setExecutingId(insightId);
    try {
      const result = await execute.mutateAsync(insightId);
      setActiveResult(result);
    } finally {
      setExecutingId(null);
    }
  };

  const CATEGORY_LABELS: Record<string, string> = {
    summary: 'Summary',
    distribution: 'Distribution',
    ranking: 'Ranking',
    patterns: 'Patterns',
    activity: 'Activity',
  };

  // Group dropdown results by category
  const grouped = filteredResults.reduce<Record<string, InsightCatalogEntry[]>>((acc, entry) => {
    const cat = entry.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(entry);
    return acc;
  }, {});

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
      <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
        Collection Insights
      </h2>

      {/* Search input */}
      <div className="relative mb-4">
        <input
          ref={inputRef}
          type="text"
          placeholder="Ask a question about your collection…"
          value={searchValue}
          onChange={e => handleInputChange(e.target.value)}
          onFocus={() => { if (searchValue.trim()) setDropdownOpen(true); }}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
        />

        {/* Autocomplete dropdown */}
        {dropdownOpen && filteredResults.length > 0 && (
          <div
            ref={dropdownRef}
            className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-xl z-50 max-h-72 overflow-y-auto"
          >
            {Object.entries(grouped).map(([category, entries]) => (
              <div key={category}>
                <div className="px-3 py-1.5 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider bg-gray-50 dark:bg-gray-700/50">
                  {CATEGORY_LABELS[category] ?? category}
                </div>
                {entries.map(entry => (
                  <button
                    key={entry.id}
                    type="button"
                    onClick={() => runInsight(entry.id)}
                    className="w-full text-left px-3 py-2 flex items-center gap-2 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-colors"
                  >
                    <span className="text-base">{entry.icon}</span>
                    <span className="text-sm text-gray-800 dark:text-gray-200">{entry.label}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}

        {dropdownOpen && searchValue.trim() && filteredResults.length === 0 && (
          <div
            ref={dropdownRef}
            className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-xl z-50 px-4 py-3 text-sm text-gray-500 dark:text-gray-400"
          >
            No matching questions found
          </div>
        )}
      </div>

      {/* Suggestion chips */}
      {suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map(suggestion => {
            const entry = catalog.find(e => e.id === suggestion.id);
            const isLoading = executingId === suggestion.id;
            return (
              <button
                key={suggestion.id}
                type="button"
                onClick={() => runInsight(suggestion.id)}
                disabled={isLoading || execute.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 transition-all duration-200 cursor-pointer
                  hover:shadow-lg hover:scale-[1.03] hover:border-indigo-400 dark:hover:border-indigo-500
                  disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none"
              >
                {entry && <span className="text-base">{entry.icon}</span>}
                <span>{suggestion.label}</span>
                {isLoading && (
                  <span className="w-3 h-3 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Loading state */}
      {execute.isPending && executingId === null && (
        <div className="mt-4 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <span className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <span>Running insight…</span>
        </div>
      )}

      {/* Error state */}
      {execute.isError && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-400">
            {execute.error?.message ?? 'Failed to run insight'}
          </p>
        </div>
      )}

      {/* Result */}
      {activeResult && (
        <InsightResponse
          response={activeResult}
          onCardClick={onCardClick}
        />
      )}
    </div>
  );
}
