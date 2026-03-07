import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { PriceHistoryPoint } from '../api/client';

interface PriceChartProps {
  points: PriceHistoryPoint[];
  currency?: string;
  isLoading?: boolean;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function PriceChart({ points, currency = 'eur', isLoading = false }: PriceChartProps) {
  if (isLoading) {
    return (
      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Price History</div>
        <div className="h-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Price History</div>
        <div className="h-20 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded border border-dashed border-gray-300 dark:border-gray-600">
          No price history yet — run a price update to start tracking.
        </div>
      </div>
    );
  }

  const currencySymbol = currency === 'eur' ? '\u20AC' : '$';
  const chartData = points.map(p => ({
    date: formatDate(p.recorded_at),
    price: p.price,
  }));

  return (
    <div className="mt-4">
      <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Price History</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: 'currentColor' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: 'currentColor' }}
            tickFormatter={(v: number) => `${currencySymbol}${v}`}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value: number) => [`${currencySymbol}${value.toFixed(2)}`, 'Price']}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
