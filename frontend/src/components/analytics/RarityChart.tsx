import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import {
  RARITY_COLORS, CHART_COLORS, buildChartTheme,
  tooltipContentStyle, tooltipItemStyle, tooltipLabelStyle,
} from './constants';

export interface RarityEntry {
  rarity: string;
  count: number;
}

interface RarityChartProps {
  data: RarityEntry[];
  activeFilter?: string;
  onBarClick?: (entry: RarityEntry) => void;
  isDark: boolean;
}

export function RarityChart({ data, activeFilter, onBarClick, isDark }: RarityChartProps) {
  const theme = buildChartTheme(isDark);

  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
        <XAxis
          dataKey="rarity"
          tick={{ fill: theme.axisColor, fontSize: 12 }}
          tickLine={{ stroke: theme.axisColor }}
        />
        <YAxis
          tick={{ fill: theme.axisColor, fontSize: 12 }}
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
          radius={[6, 6, 0, 0]}
          cursor="pointer"
          onClick={(_: unknown, idx: number) => {
            if (data[idx] && onBarClick) onBarClick(data[idx]);
          }}
        >
          {data.map((entry, idx) => (
            <Cell
              key={idx}
              fill={RARITY_COLORS[entry.rarity.toLowerCase()] ?? CHART_COLORS[idx % CHART_COLORS.length]}
              opacity={activeFilter && activeFilter !== entry.rarity ? 0.3 : 1}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
