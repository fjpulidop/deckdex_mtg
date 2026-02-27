import { useState, useRef, useEffect } from 'react';
import { Card } from '../api/client';

interface CardTableProps {
  cards: Card[];
  isLoading?: boolean;
  onAdd?: () => void;
  onRowClick?: (card: Card) => void;
}

export function CardTable({ cards, isLoading, onAdd, onRowClick }: CardTableProps) {
  const hasIds = cards.some(c => c.id != null);
  const [sortKey, setSortKey] = useState<string>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50;

  // Scroll-to-top on page change
  const containerRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);
  // 'first' | 'last' | null — which row to focus after a keyboard-triggered page change
  const pendingFocus = useRef<'first' | 'last' | null>(null);

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  // Sort full list first so order is consistent across all pages
  const sortedCards = [...cards].sort((a, b) => {
    if (sortKey === 'price') {
      const parsePrice = (v: unknown): number => {
        if (v == null || v === '') return NaN;
        const s = String(v).replace(',', '.');
        const n = parseFloat(s);
        return Number.isFinite(n) ? n : NaN;
      };
      const aNum = parsePrice(a.price);
      const bNum = parsePrice(b.price);
      const aNaN = Number.isNaN(aNum);
      const bNaN = Number.isNaN(bNum);
      if (aNaN && bNaN) return 0;
      if (aNaN) return 1;
      if (bNaN) return -1;
      if (sortDirection === 'asc') return aNum < bNum ? -1 : aNum > bNum ? 1 : 0;
      return bNum < aNum ? -1 : bNum > aNum ? 1 : 0;
    }
    if (sortKey === 'created_at') {
      const aVal = (a.created_at ?? '') as string;
      const bVal = (b.created_at ?? '') as string;
      // ISO strings compare lexicographically for chronological order
      if (sortDirection === 'asc') return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
    }
    const aVal = (a[sortKey] ?? '') as string;
    const bVal = (b[sortKey] ?? '') as string;
    if (sortDirection === 'asc') return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
  });

  const totalPages = Math.ceil(sortedCards.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedCards = sortedCards.slice(startIndex, startIndex + itemsPerPage);

  // Scroll-to-top when page changes
  useEffect(() => {
    containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [currentPage]);

  // Resolve pending focus after a keyboard-triggered page change
  useEffect(() => {
    if (pendingFocus.current === 'first') {
      rowRefs.current[0]?.focus();
      setFocusedIndex(0);
    } else if (pendingFocus.current === 'last') {
      const last = paginatedCards.length - 1;
      rowRefs.current[last]?.focus();
      setFocusedIndex(last);
    }
    pendingFocus.current = null;
  // paginatedCards.length and currentPage are the right triggers; exhaustive-deps would add more
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

  const handleTbodyKeyDown = (e: React.KeyboardEvent<HTMLTableSectionElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (focusedIndex < paginatedCards.length - 1) {
        const next = focusedIndex + 1;
        rowRefs.current[next]?.focus();
        setFocusedIndex(next);
      } else if (currentPage < totalPages) {
        pendingFocus.current = 'first';
        setCurrentPage(p => p + 1);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (focusedIndex > 0) {
        const prev = focusedIndex - 1;
        rowRefs.current[prev]?.focus();
        setFocusedIndex(prev);
      } else if (currentPage > 1) {
        pendingFocus.current = 'last';
        setCurrentPage(p => p - 1);
      }
    } else if (e.key === 'Enter' && focusedIndex >= 0) {
      onRowClick?.(paginatedCards[focusedIndex]);
    }
  };

  return (
    <div ref={containerRef} className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      {onAdd && hasIds && (
        <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-600">
          <button
            type="button"
            onClick={onAdd}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm dark:bg-green-500 dark:hover:bg-green-600"
          >
            Add card
          </button>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
          <thead className="bg-gray-50 dark:bg-gray-700/50">
            <tr>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                onClick={() => handleSort('created_at')}
                title="Date added (newest first by default)"
              >
                Added {sortKey === 'created_at' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                onClick={() => handleSort('name')}
              >
                Name {sortKey === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                onClick={() => handleSort('type')}
              >
                Type {sortKey === 'type' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                onClick={() => handleSort('rarity')}
              >
                Rarity {sortKey === 'rarity' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                onClick={() => handleSort('price')}
              >
                Price {sortKey === 'price' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Set
              </th>
            </tr>
          </thead>
          <tbody
            className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600"
            onKeyDown={handleTbodyKeyDown}
          >
            {paginatedCards.map((card, index) => (
              <tr
                key={card.id ?? index}
                ref={el => { rowRefs.current[index] = el; }}
                tabIndex={0}
                onFocus={() => setFocusedIndex(index)}
                className={`hover:bg-gray-50 dark:hover:bg-gray-700/50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-400 ${onRowClick ? 'cursor-pointer' : ''}`}
                onClick={() => onRowClick?.(card)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {card.created_at
                    ? new Date(card.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
                    : '—'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                  {card.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {card.type || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  <span className={`px-2 py-1 rounded text-xs ${
                    card.rarity === 'mythic' ? 'bg-orange-100 dark:bg-orange-900/40 text-orange-800 dark:text-orange-200' :
                    card.rarity === 'rare' ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200' :
                    card.rarity === 'uncommon' ? 'bg-gray-100 dark:bg-gray-600 text-gray-800 dark:text-gray-200' :
                    'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200'
                  }`}>
                    {card.rarity || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {card.price !== 'N/A' ? `€${card.price}` : 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {card.set_name || 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-gray-50 dark:bg-gray-700/50 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-600">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, sortedCards.length)} of {sortedCards.length} cards
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-sm text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm text-gray-700 dark:text-gray-300">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-sm text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
