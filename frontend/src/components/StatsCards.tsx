import { useStats } from '../hooks/useApi';

export function StatsCards() {
  const { data: stats, isLoading } = useStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {[1, 2].map(i => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR'
    }).format(value);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {/* Total Cards */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-sm font-medium text-gray-600 mb-2">Total Cards</div>
        <div className="text-3xl font-bold text-gray-900">{stats.total_cards.toLocaleString()}</div>
      </div>

      {/* Total Value */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-sm font-medium text-gray-600 mb-2">Total Value</div>
        <div className="text-3xl font-bold text-green-600">{formatCurrency(stats.total_value)}</div>
        <div className="text-sm text-gray-500 mt-2">Avg: {formatCurrency(stats.average_price)}</div>
      </div>
    </div>
  );
}
