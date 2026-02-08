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
  activeChips: ActiveFilterChip[];
  resultCount: number;
  onClearFilters: () => void;
}

const inputClass =
  'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500';

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

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6 transition-opacity duration-150">
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
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
        >
          Clear Filters
        </button>
      </div>

      {/* Row 2: Active chips + result count */}
      <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-100">
        {activeChips.map((chip) => (
          <span
            key={chip.id}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-50 text-blue-800 text-sm"
          >
            {chip.label}
            <button
              type="button"
              onClick={chip.onRemove}
              className="ml-0.5 rounded hover:bg-blue-100 p-0.5 leading-none"
              aria-label={`Remove ${chip.label} filter`}
            >
              ×
            </button>
          </span>
        ))}
        <span className="ml-auto text-sm text-gray-500">
          Showing {resultCount} card{resultCount !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
