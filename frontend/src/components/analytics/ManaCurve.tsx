import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { buildChartTheme, tooltipContentStyle, tooltipItemStyle, tooltipLabelStyle } from './constants';

export interface CmcEntry {
  cmc: string;
  count: number;
}

interface ManaCurveProps {
  data: CmcEntry[];
  activeFilter?: string;
  onBarClick?: (cmc: string) => void;
  isDark: boolean;
}

function computeAvgCmc(data: CmcEntry[]): number | null {
  let totalWeighted = 0;
  let totalCount = 0;
  for (const entry of data) {
    if (entry.cmc === 'Unknown') continue;
    const numericCmc = entry.cmc === '7+' ? 7 : Number(entry.cmc);
    if (isNaN(numericCmc)) continue;
    totalWeighted += numericCmc * entry.count;
    totalCount += entry.count;
  }
  if (totalCount === 0) return null;
  return totalWeighted / totalCount;
}

// Custom dot to make area chart clickable per data point
function ClickableDot(props: {
  cx?: number;
  cy?: number;
  index?: number;
  data: CmcEntry[];
  activeFilter?: string;
  onBarClick?: (cmc: string) => void;
  isDark: boolean;
}) {
  const { cx, cy, index, data, activeFilter, onBarClick, isDark } = props;
  if (cx === undefined || cy === undefined || index === undefined) return null;

  const entry = data[index];
  const isActive = !activeFilter || activeFilter === entry?.cmc;
  const fillColor = isDark ? '#818cf8' : '#6366f1';

  return (
    <circle
      cx={cx}
      cy={cy}
      r={isActive ? 5 : 3}
      fill={fillColor}
      stroke={isDark ? '#1f2937' : '#ffffff'}
      strokeWidth={2}
      opacity={isActive ? 1 : 0.35}
      cursor="pointer"
      onClick={() => {
        if (entry && onBarClick) onBarClick(entry.cmc);
      }}
    />
  );
}

export function ManaCurve({ data, activeFilter, onBarClick, isDark }: ManaCurveProps) {
  const { t } = useTranslation();
  const theme = buildChartTheme(isDark);
  const avgCmc = useMemo(() => computeAvgCmc(data), [data]);

  if (data.length === 0) return null;

  const gradientId = 'manaCurveGradient';
  const strokeColor = isDark ? '#818cf8' : '#6366f1';

  return (
    <div className="relative">
      {avgCmc !== null && (
        <div className="absolute top-0 right-0 z-10 bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-xs font-semibold px-2.5 py-1 rounded-full">
          {t('analytics.avgCmc')}: {avgCmc.toFixed(1)}
        </div>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity={0.4} />
              <stop offset="95%" stopColor={strokeColor} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis
            dataKey="cmc"
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
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke={strokeColor}
            strokeWidth={2.5}
            fill={`url(#${gradientId})`}
            dot={<ClickableDot data={data} activeFilter={activeFilter} onBarClick={onBarClick} isDark={isDark} />}
            activeDot={{ r: 6, strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
