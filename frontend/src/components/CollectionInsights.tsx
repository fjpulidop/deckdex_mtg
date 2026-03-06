import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, InsightCatalogEntry, InsightResponse as InsightResponseType } from '../api/client';
import { useInsightsCatalog, useInsightsSuggestions, useInsightExecute } from '../hooks/useApi';
import { InsightResponse } from './insights/InsightResponse';

const PINNED_STORAGE_KEY = 'deckdex:pinned_insights';

interface InsightResultEntry {
  /** Unique render key: `${insight_id}_${executedAt}` */
  id: string;
  response: InsightResponseType;
  pinned: boolean;
  executedAt: number;
}

function loadPinnedIds(): string[] {
  try {
    const raw = localStorage.getItem(PINNED_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
      return parsed;
    }
    return [];
  } catch {
    return [];
  }
}

function savePinnedIds(ids: string[]): void {
  try {
    localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(ids));
  } catch {
    // localStorage unavailable — silent failure
  }
}

function fuzzyMatch(query: string, entry: InsightCatalogEntry): boolean {
  if (!query.trim()) return false;
  const q = query.toLowerCase();
  if (entry.label.toLowerCase().includes(q)) return true;
  return entry.keywords.some(k => k.toLowerCase().includes(q));
}

// --- InsightResultCard ---

interface InsightResultCardProps {
  entry: InsightResultEntry;
  allResults: InsightResultEntry[];
  onTogglePin: (entryId: string, currentResults: InsightResultEntry[]) => void;
  onDismiss: (entryId: string) => void;
  onCardClick?: (card: Card) => void;
}

function InsightResultCard({ entry, allResults, onTogglePin, onDismiss, onCardClick }: InsightResultCardProps) {
  const { t } = useTranslation();

  return (
    <div
      className={[
        'mt-4 rounded-xl border',
        entry.pinned
          ? 'border-l-4 border-indigo-400 dark:border-indigo-500 bg-gray-50 dark:bg-gray-700/50'
          : 'border-gray-100 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50',
      ].join(' ')}
    >
      {/* Card header: question + actions */}
      <div className="flex items-start justify-between gap-2 px-4 pt-3 pb-1">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex-1">
          {entry.response.question}
        </h3>
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Pin toggle */}
          <button
            type="button"
            onClick={() => onTogglePin(entry.id, allResults)}
            aria-label={entry.pinned ? t('insights.unpin') : t('insights.pin')}
            title={entry.pinned ? t('insights.unpin') : t('insights.pin')}
            className={[
              'p-1 rounded transition-colors',
              entry.pinned
                ? 'text-indigo-500 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-200'
                : 'text-gray-400 hover:text-indigo-500 dark:text-gray-500 dark:hover:text-indigo-400',
            ].join(' ')}
          >
            {entry.pinned ? (
              // Filled pin icon
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                <path d="M16 9V4h1c.55 0 1-.45 1-1s-.45-1-1-1H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3v2h5.97v7l1 1 1-1v-7H19v-2c-1.66 0-3-1.34-3-3z"/>
              </svg>
            ) : (
              // Outline pin icon
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 9V4h1a1 1 0 000-2H7a1 1 0 000 2h1v5a3 3 0 01-3 3v2h5.97v7l1 1 1-1v-7H19v-2a3 3 0 01-3-3z"/>
              </svg>
            )}
          </button>

          {/* Dismiss */}
          <button
            type="button"
            onClick={() => onDismiss(entry.id)}
            aria-label={t('insights.dismiss')}
            title={t('insights.dismiss')}
            className="p-1 rounded text-gray-400 hover:text-gray-700 dark:text-gray-500 dark:hover:text-gray-200 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Renderer — pass question-less response since we render the question above */}
      <div className="px-4 pb-4">
        <InsightResponse
          response={entry.response}
          onCardClick={onCardClick}
          hideQuestion
        />
      </div>
    </div>
  );
}

// --- CollectionInsights ---

interface Props {
  onCardClick?: (card: Card) => void;
}

export function CollectionInsights({ onCardClick }: Props) {
  const { t } = useTranslation();
  const [searchValue, setSearchValue] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [results, setResults] = useState<InsightResultEntry[]>([]);
  const [pinnedIds, setPinnedIds] = useState<string[]>(loadPinnedIds);
  const [executingId, setExecutingId] = useState<string | null>(null);
  // Track whether we've already done the initial pinned-auto-execute
  const autoExecutedRef = useRef(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { data: catalog = [] } = useInsightsCatalog();
  const { data: suggestions = [] } = useInsightsSuggestions();
  const execute = useInsightExecute();

  // Auto-execute pinned insights on mount (sequentially)
  useEffect(() => {
    if (autoExecutedRef.current) return;
    const initialPinnedIds = loadPinnedIds();
    if (initialPinnedIds.length === 0) return;
    autoExecutedRef.current = true;

    (async () => {
      for (const insightId of initialPinnedIds) {
        try {
          const result = await execute.mutateAsync(insightId);
          const entry: InsightResultEntry = {
            id: `${insightId}_${Date.now()}`,
            response: result,
            pinned: true,
            executedAt: Date.now(),
          };
          setResults(prev => [...prev, entry]);
        } catch {
          // Silent failure for background auto-execution
        }
      }
    })();
    // execute is a stable mutate object; we intentionally run this once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      const alreadyPinned = pinnedIds.includes(insightId);
      const entry: InsightResultEntry = {
        id: `${insightId}_${Date.now()}`,
        response: result,
        pinned: alreadyPinned,
        executedAt: Date.now(),
      };
      // Prepend so most recent appears first
      setResults(prev => [entry, ...prev]);
    } finally {
      setExecutingId(null);
    }
  };

  const handleTogglePin = useCallback((entryId: string, currentResults: InsightResultEntry[]) => {
    const entry = currentResults.find(e => e.id === entryId);
    if (!entry) return;

    const nowPinned = !entry.pinned;
    const insightId = entry.response.insight_id;

    // Update the results array
    setResults(prev =>
      prev.map(e => e.id === entryId ? { ...e, pinned: nowPinned } : e)
    );

    // Sync pinnedIds state and localStorage
    const newPinnedIds = nowPinned
      ? pinnedIds.includes(insightId) ? pinnedIds : [...pinnedIds, insightId]
      : pinnedIds.filter(id => id !== insightId);

    setPinnedIds(newPinnedIds);
    savePinnedIds(newPinnedIds);
  }, [pinnedIds]);

  const handleDismiss = useCallback((entryId: string) => {
    setResults(prev => prev.filter(e => e.id !== entryId));
    // Note: we intentionally keep pinnedIds intact — pinning is a preference,
    // not a display state. Dismissed pinned insights re-appear on next page load.
  }, []);

  const getCategoryLabel = (cat: string) =>
    t(`insights.categories.${cat}`, { defaultValue: cat });

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
        {t('insights.title')}
      </h2>

      {/* Search input */}
      <div className="relative mb-4">
        <input
          ref={inputRef}
          type="text"
          placeholder={t('insights.placeholder')}
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
                  {getCategoryLabel(category)}
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
            {t('insights.noMatches')}
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

      {/* Loading state (for non-chip executions) */}
      {execute.isPending && executingId === null && (
        <div className="mt-4 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <span className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <span>{t('insights.running')}</span>
        </div>
      )}

      {/* Error state */}
      {execute.isError && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-400">
            {execute.error?.message ?? t('insights.failed')}
          </p>
        </div>
      )}

      {/* Result history */}
      {results.map(entry => (
        <InsightResultCard
          key={entry.id}
          entry={entry}
          allResults={results}
          onTogglePin={handleTogglePin}
          onDismiss={handleDismiss}
          onCardClick={onCardClick}
        />
      ))}
    </div>
  );
}
