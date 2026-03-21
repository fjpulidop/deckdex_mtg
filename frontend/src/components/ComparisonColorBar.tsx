import { BarChart, Bar, Cell, ResponsiveContainer } from 'recharts';
import { MTG_COLOR_MAP } from './analytics/constants';
import type { DeckColorCount } from '../api/client';

interface ComparisonColorBarProps {
  data: DeckColorCount[];
  isDark: boolean;
}

const COLOR_ORDER = ['W', 'U', 'B', 'R', 'G', 'C'];

export function ComparisonColorBar({ data }: ComparisonColorBarProps) {
  const totalCount = data.reduce((sum, d) => sum + d.count, 0);

  // Build a single data point for the stacked horizontal bar
  const dataPoint: Record<string, number> = {};
  if (totalCount === 0) {
    // Placeholder: show equal segments so the bar is visible
    COLOR_ORDER.forEach(c => { dataPoint[c] = 1; });
  } else {
    COLOR_ORDER.forEach(c => {
      const entry = data.find(d => d.color === c);
      dataPoint[c] = entry ? (entry.count / totalCount) * 100 : 0;
    });
  }

  return (
    <div>
      <ResponsiveContainer width="100%" height={28}>
        <BarChart
          data={[dataPoint]}
          layout="vertical"
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          barCategoryGap={0}
        >
          {COLOR_ORDER.map(color => (
            <Bar
              key={color}
              dataKey={color}
              stackId="colors"
              fill={totalCount === 0 ? '#9ca3af' : (MTG_COLOR_MAP[color]?.hex ?? '#9ca3af')}
            >
              <Cell fill={totalCount === 0 ? '#9ca3af' : (MTG_COLOR_MAP[color]?.hex ?? '#9ca3af')} />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-2 mt-1 flex-wrap">
        {COLOR_ORDER.map(color => (
          <span key={color} className="flex items-center gap-0.5 text-xs text-gray-600 dark:text-gray-400">
            <span
              className="inline-block w-2 h-2 rounded-sm"
              style={{ backgroundColor: MTG_COLOR_MAP[color]?.hex ?? '#9ca3af' }}
            />
            {color}
          </span>
        ))}
      </div>
    </div>
  );
}
