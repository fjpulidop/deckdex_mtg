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

const handleGoogleLogin = () => {
  window.location.href = 'http://localhost:8000/api/auth/google';
};

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
          <p className="text-slate-400 text-lg mb-2">
            Explore our interactive demo — no signup required
          </p>
          <p className="text-slate-500 text-sm">
            Built with TypeScript, React, and love for the MTG community 💜
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
          <button
            onClick={handleGoogleLogin}
            className="inline-flex items-center justify-center px-8 py-3 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:shadow-lg hover:shadow-primary-500/50 transition-all duration-300 hover:scale-105"
          >
            <svg
              className="w-5 h-5 mr-2"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="white" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="white" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="white" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="white" />
            </svg>
            Sign in with Google
          </button>
        </div>
      </div>
    </section>
  );
};
