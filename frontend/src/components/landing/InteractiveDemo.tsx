import { useState, useMemo } from 'react';
import { Search } from 'lucide-react';

interface DemoCard {
  id: number;
  name: string;
  set: string;
  rarity: 'Common' | 'Uncommon' | 'Rare' | 'Mythic';
  price: number;
}

const DEMO_CARDS: DemoCard[] = [
  { id: 1, name: 'Lightning Bolt', set: 'M11', rarity: 'Common', price: 0.50 },
  { id: 2, name: 'Black Lotus', set: 'Alpha', rarity: 'Mythic', price: 50000.00 },
  { id: 3, name: 'Serra Angel', set: 'M10', rarity: 'Rare', price: 45.00 },
  { id: 4, name: 'Counterspell', set: '4ED', rarity: 'Common', price: 15.00 },
  { id: 5, name: 'Mox Jet', set: 'Alpha', rarity: 'Mythic', price: 45000.00 },
  { id: 6, name: 'Giant Growth', set: 'Alpha', rarity: 'Common', price: 2.00 },
  { id: 7, name: 'Time Walk', set: 'Alpha', rarity: 'Mythic', price: 35000.00 },
  { id: 8, name: 'Ancestral Recall', set: 'Alpha', rarity: 'Mythic', price: 40000.00 },
  { id: 9, name: 'Fireball', set: 'M21', rarity: 'Uncommon', price: 0.75 },
  { id: 10, name: 'Shock', set: 'ZEN', rarity: 'Common', price: 0.50 },
  { id: 11, name: 'Path to Exile', set: 'CON', rarity: 'Uncommon', price: 8.00 },
  { id: 12, name: 'Snapcaster Mage', set: 'ISD', rarity: 'Mythic', price: 120.00 },
  { id: 13, name: 'Thoughtseize', set: 'TSB', rarity: 'Rare', price: 90.00 },
  { id: 14, name: 'Dark Ritual', set: '5ED', rarity: 'Common', price: 5.00 },
  { id: 15, name: 'Lotus Petal', set: 'ALS', rarity: 'Common', price: 25.00 },
];

type RarityFilter = 'All' | 'Common' | 'Uncommon' | 'Rare' | 'Mythic';

export const InteractiveDemo = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRarity, setSelectedRarity] = useState<RarityFilter>('All');

  const filteredCards = useMemo(() => {
    return DEMO_CARDS.filter((card) => {
      const matchesSearch =
        card.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        card.set.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesRarity = selectedRarity === 'All' || card.rarity === selectedRarity;
      return matchesSearch && matchesRarity;
    });
  }, [searchQuery, selectedRarity]);

  const rarities: RarityFilter[] = ['All', 'Common', 'Uncommon', 'Rare', 'Mythic'];

  return (
    <section id="demo" className="py-20 md:py-32 bg-gradient-to-b from-slate-950 to-slate-900 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-12 md:mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-purple-300 to-pink-400 bg-clip-text text-transparent">
              Try DeckDex Right Now
            </span>
          </h2>
          <p className="text-slate-400 text-lg">
            Explore our interactive demo — no signup required
          </p>
        </div>

        {/* Demo Container */}
        <div className="rounded-lg border border-slate-700/50 overflow-hidden bg-slate-900/50 backdrop-blur-sm">
          {/* Search and Filter Bar */}
          <div className="p-6 md:p-8 border-b border-slate-700/50 space-y-6">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-5 w-5 text-slate-500" />
              <input
                type="text"
                placeholder="Search cards by name or set..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors"
              />
            </div>

            {/* Rarity Filters */}
            <div className="flex flex-wrap gap-2">
              {rarities.map((rarity) => (
                <button
                  key={rarity}
                  onClick={() => setSelectedRarity(rarity)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    selectedRarity === rarity
                      ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg shadow-primary-500/50'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                  }`}
                >
                  {rarity}
                </button>
              ))}
            </div>
          </div>

          {/* Cards Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/50 bg-slate-800/50">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                    Card Name
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                    Set
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                    Rarity
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-slate-300">
                    Price
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredCards.length > 0 ? (
                  filteredCards.map((card) => (
                    <tr
                      key={card.id}
                      className="border-b border-slate-700/30 hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="px-6 py-4 text-white">{card.name}</td>
                      <td className="px-6 py-4 text-slate-400">{card.set}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            card.rarity === 'Mythic'
                              ? 'bg-orange-500/20 text-orange-300'
                              : card.rarity === 'Rare'
                                ? 'bg-yellow-500/20 text-yellow-300'
                                : card.rarity === 'Uncommon'
                                  ? 'bg-slate-500/20 text-slate-300'
                                  : 'bg-slate-600/20 text-slate-400'
                          }`}
                        >
                          {card.rarity}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-white font-semibold">
                        ${card.price.toFixed(2)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-400">
                      No cards found matching your search.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Results Footer */}
          <div className="px-6 md:px-8 py-4 border-t border-slate-700/50 bg-slate-900/30 flex items-center justify-between">
            <p className="text-sm text-slate-400">
              Results: <span className="text-white font-semibold">{filteredCards.length}</span>{' '}
              {filteredCards.length === 1 ? 'card' : 'cards'}
            </p>
            <p className="text-xs text-slate-500">Demo data — actual prices vary</p>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <a
            href="/login"
            className="inline-flex items-center justify-center px-8 py-3 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:shadow-lg hover:shadow-primary-500/50 transition-all duration-300 hover:scale-105"
          >
            Create Your Free Account
          </a>
        </div>
      </div>
    </section>
  );
};
