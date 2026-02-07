import { useState } from 'react';

interface FiltersProps {
  onSearchChange: (search: string) => void;
  onRarityChange: (rarity: string) => void;
  onClearFilters: () => void;
}

export function Filters({ onSearchChange, onRarityChange, onClearFilters }: FiltersProps) {
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('all');

  const handleSearchChange = (value: string) => {
    setSearch(value);
    // Debounce search
    setTimeout(() => onSearchChange(value), 300);
  };

  const handleRarityChange = (value: string) => {
    setRarity(value);
    onRarityChange(value);
  };

  const handleClear = () => {
    setSearch('');
    setRarity('all');
    onClearFilters();
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex flex-wrap gap-4 items-center">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search cards by name..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Rarity Filter */}
        <div className="min-w-[150px]">
          <select
            value={rarity}
            onChange={(e) => handleRarityChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Rarities</option>
            <option value="common">Common</option>
            <option value="uncommon">Uncommon</option>
            <option value="rare">Rare</option>
            <option value="mythic">Mythic</option>
          </select>
        </div>

        {/* Clear Filters */}
        <button
          onClick={handleClear}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
        >
          Clear Filters
        </button>
      </div>
    </div>
  );
}
