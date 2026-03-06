import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import {
  TYPE_COLORS, buildChartTheme,
  tooltipContentStyle, tooltipItemStyle, tooltipLabelStyle,
} from './constants';

export interface TypeEntry {
  type_line: string;
  count: number;
}

interface TypeDistributionChartProps {
  data: TypeEntry[];
  activeFilter?: string;
  onBarClick?: (entry: TypeEntry) => void;
  isDark: boolean;
}

export function TypeDistributionChart({ data, activeFilter, onBarClick, isDark }: TypeDistributionChartProps) {
  const theme = buildChartTheme(isDark);

  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
        <XAxis
          type="number"
          tick={{ fill: theme.axisColor, fontSize: 12 }}
          tickLine={{ stroke: theme.axisColor }}
        />
        <YAxis
          dataKey="type_line"
          type="category"
          width={120}
          tick={{ fill: theme.axisColor, fontSize: 11 }}
          tickLine={{ stroke: theme.axisColor }}
        />
        <Tooltip
          contentStyle={tooltipContentStyle(theme)}
          itemStyle={tooltipItemStyle(theme)}
          labelStyle={tooltipLabelStyle(theme)}
          cursor={{ fill: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
        />
        <Bar
          dataKey="count"
          radius={[0, 6, 6, 0]}
          cursor="pointer"
          onClick={(_: unknown, idx: number) => {
            if (data[idx] && onBarClick) onBarClick(data[idx]);
          }}
        >
          {data.map((entry, idx) => (
            <Cell
              key={idx}
              fill={TYPE_COLORS[entry.type_line] ?? TYPE_COLORS['Other']}
              opacity={activeFilter && activeFilter !== entry.type_line ? 0.3 : 1}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
