import { BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { buildChartTheme, tooltipContentStyle } from './analytics/constants';
import type { DeckManaCurveBucket } from '../api/client';

interface ComparisonManaCurveProps {
  data: DeckManaCurveBucket[];
  isDark: boolean;
}

export function ComparisonManaCurve({ data, isDark }: ComparisonManaCurveProps) {
  const theme = buildChartTheme(isDark);

  return (
    <ResponsiveContainer width="100%" height={100}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 12, left: -20 }}>
        <XAxis
          dataKey="cmc"
          tick={{ fontSize: 9, fill: theme.axisColor }}
          tickLine={false}
        />
        <YAxis hide domain={[0, 'auto']} />
        <Tooltip contentStyle={tooltipContentStyle(theme)} />
        <Bar dataKey="count" radius={[2, 2, 0, 0]}>
          {data.map((_entry, idx) => (
            <Cell key={idx} fill="#6366f1" />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
