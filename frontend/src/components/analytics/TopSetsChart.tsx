import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import {
  CHART_COLORS, buildChartTheme,
  tooltipContentStyle, tooltipItemStyle, tooltipLabelStyle,
} from './constants';

export interface SetEntry {
  set_name: string;
  count: number;
}

interface TopSetsChartProps {
  data: SetEntry[];
  activeFilter?: string;
  onBarClick?: (entry: SetEntry) => void;
  isDark: boolean;
}

export function TopSetsChart({ data, activeFilter, onBarClick, isDark }: TopSetsChartProps) {
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
          dataKey="set_name"
          type="category"
          width={140}
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
              fill={CHART_COLORS[idx % CHART_COLORS.length]}
              opacity={activeFilter && activeFilter !== entry.set_name ? 0.3 : 1}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
