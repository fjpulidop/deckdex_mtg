import { useState, useEffect } from 'react';

export interface ActiveFilterChip {
  id: string;
  label: string;
  onRemove: () => void;
}

interface FiltersProps {
  search: string;
  onSearchChange: (search: string) => void;
  rarity: string;
  onRarityChange: (rarity: string) => void;
  type: string;
  onTypeChange: (type: string) => void;
  typeOptions: string[];
  set: string;
  onSetChange: (set: string) => void;
  setOptions: string[];
  priceMin: string;
  priceMax: string;
  onPriceRangeChange: (min: string, max: string) => void;
  colors: string[];
  onColorsChange: (colors: string[]) => void;
  activeChips: ActiveFilterChip[];
  resultCount: number;
  onClearFilters: () => void;
}

const inputClass =
  'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400';

const MTG_COLORS = [
  {
    symbol: 'W',
    label: 'White',
    activeClass: 'bg-yellow-100 text-yellow-800 border-yellow-400 dark:bg-yellow-900/40 dark:text-yellow-200 dark:border-yellow-600',
  },
  {
    symbol: 'U',
    label: 'Blue',
    activeClass: 'bg-blue-100 text-blue-800 border-blue-400 dark:bg-blue-900/40 dark:text-blue-200 dark:border-blue-600',
  },
  {
    symbol: 'B',
    label: 'Black',
    activeClass: 'bg-gray-800 text-gray-100 border-gray-500 dark:bg-gray-900 dark:text-gray-100 dark:border-gray-400',
  },
  {
    symbol: 'R',
    label: 'Red',
    activeClass: 'bg-red-100 text-red-800 border-red-400 dark:bg-red-900/40 dark:text-red-200 dark:border-red-600',
  },
  {
    symbol: 'G',
    label: 'Green',
    activeClass: 'bg-green-100 text-green-800 border-green-400 dark:bg-green-900/40 dark:text-green-200 dark:border-green-600',
  },
] as const;

export function Filters({
  search,
  onSearchChange,
  rarity,
  onRarityChange,
  type,
  onTypeChange,
  typeOptions,
  set,
  onSetChange,
  setOptions,
  priceMin,
  priceMax,
  onPriceRangeChange,
  colors,
  onColorsChange,
  activeChips,
  resultCount,
  onClearFilters,
}: FiltersProps) {
  const [debouncedSearch, setDebouncedSearch] = useState(search);

  useEffect(() => {
    setDebouncedSearch(search);
  }, [search]);

  useEffect(() => {
    const t = setTimeout(() => onSearchChange(debouncedSearch), 300);
    return () => clearTimeout(t);
  }, [debouncedSearch, onSearchChange]);

  const handlePriceMinChange = (value: string) => onPriceRangeChange(value, priceMax);
  const handlePriceMaxChange = (value: string) => onPriceRangeChange(priceMin, value);

  const toggleColor = (symbol: string) => {
    if (colors.includes(symbol)) {
      onColorsChange(colors.filter(c => c !== symbol));
    } else {
      onColorsChange([...colors, symbol]);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6 transition-opacity duration-150">
      {/* Row 1: Search + dropdowns + Clear */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search cards by name..."
            value={debouncedSearch}
            onChange={(e) => setDebouncedSearch(e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="min-w-[140px]">
          <select
            value={rarity}
            onChange={(e) => onRarityChange(e.target.value)}
            className={inputClass}
          >
            <option value="all">All Rarities</option>
            <option value="common">Common</option>
            <option value="uncommon">Uncommon</option>
            <option value="rare">Rare</option>
            <option value="mythic">Mythic</option>
          </select>
        </div>

        <div className="min-w-[140px]">
          <select value={type} onChange={(e) => onTypeChange(e.target.value)} className={inputClass}>
            <option value="all">All Types</option>
            {typeOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>

        <div className="min-w-[140px]">
          <select value={set} onChange={(e) => onSetChange(e.target.value)} className={inputClass}>
            <option value="all">All Sets</option>
            {setOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 min-w-[180px]">
          <input
            type="text"
            placeholder="Min €"
            value={priceMin}
            onChange={(e) => handlePriceMinChange(e.target.value)}
            className={`${inputClass} w-20`}
            inputMode="decimal"
          />
          <span className="text-gray-400">–</span>
          <input
            type="text"
            placeholder="Max €"
            value={priceMax}
            onChange={(e) => handlePriceMaxChange(e.target.value)}
            className={`${inputClass} w-20`}
            inputMode="decimal"
          />
        </div>

        <button
          onClick={onClearFilters}
          className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition"
        >
          Clear Filters
        </button>
      </div>

      {/* Row 2: Color toggle bar */}
      <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mr-1">
          Color
        </span>
        {MTG_COLORS.map(({ symbol, label, activeClass }) => {
          const isActive = colors.includes(symbol);
          return (
            <button
              key={symbol}
              type="button"
              onClick={() => toggleColor(symbol)}
              title={label}
              aria-pressed={isActive}
              className={`w-8 h-8 rounded-full border-2 transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-400 flex items-center justify-center ${
                isActive
                  ? activeClass
                  : 'bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <span className={`card-symbol card-symbol-${symbol}`} aria-hidden="true" />
            </button>
          );
        })}
      </div>

      {/* Row 3: Active chips + result count */}
      <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
        {activeChips.map((chip) => (
          <span
            key={chip.id}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-50 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 text-sm"
          >
            {chip.label}
            <button
              type="button"
              onClick={chip.onRemove}
              className="ml-0.5 rounded hover:bg-blue-100 dark:hover:bg-blue-800/50 p-0.5 leading-none"
              aria-label={`Remove ${chip.label} filter`}
            >
              ×
            </button>
          </span>
        ))}
        <span className="ml-auto text-sm text-gray-500 dark:text-gray-400">
          Showing {resultCount} card{resultCount !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
