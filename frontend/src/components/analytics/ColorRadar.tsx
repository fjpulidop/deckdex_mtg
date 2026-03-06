import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from 'recharts';
import { MTG_COLOR_MAP, WUBRG_ORDER, buildChartTheme, tooltipContentStyle } from './constants';

export interface ColorIdentityEntry {
  color_identity: string;
  count: number;
}

interface ColorRadarProps {
  data: ColorIdentityEntry[];
  activeFilter?: string;
  onSliceClick?: (color: string) => void;
  isDark: boolean;
}

interface RadarPoint {
  color: string;
  label: string;
  value: number;
  fullMark: number;
}

/**
 * Distribute multi-color entries across their constituent WUBRG axes.
 * e.g., "WU" count:10 → W+10, U+10
 * Returns 5-axis data + colorless count.
 */
function transformToRadar(data: ColorIdentityEntry[]): { radarData: RadarPoint[]; colorlessCount: number } {
  const totals: Record<string, number> = { W: 0, U: 0, B: 0, R: 0, G: 0 };
  let colorlessCount = 0;

  for (const entry of data) {
    const ci = entry.color_identity;
    if (!ci || ci === 'C') {
      colorlessCount += entry.count;
      continue;
    }
    const letters = ci.split('').filter(c => c in totals);
    if (letters.length === 0) {
      colorlessCount += entry.count;
      continue;
    }
    for (const letter of letters) {
      totals[letter] += entry.count;
    }
  }

  const maxVal = Math.max(...Object.values(totals), 1);
  // Minimum baseline: at least 5% of max so shape is always visible
  const baseline = maxVal * 0.05;

  const radarData: RadarPoint[] = WUBRG_ORDER.map(color => ({
    color,
    label: MTG_COLOR_MAP[color].label,
    value: Math.max(totals[color], baseline),
    fullMark: maxVal,
  }));

  return { radarData, colorlessCount };
}

export function ColorRadar({ data, activeFilter, onSliceClick, isDark }: ColorRadarProps) {
  const { t } = useTranslation();
  const theme = buildChartTheme(isDark);

  const { radarData, colorlessCount } = useMemo(() => transformToRadar(data), [data]);

  if (data.length === 0) return null;

  const fillColor = isDark ? '#818cf8' : '#6366f1';
  const strokeColor = isDark ? '#a5b4fc' : '#4f46e5';

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke={theme.gridColor} />
          <PolarAngleAxis
            dataKey="label"
            tick={({ x, y, payload }: { x: string | number; y: string | number; payload: { value: string } }) => {
              const color = WUBRG_ORDER.find(c => MTG_COLOR_MAP[c].label === payload.value);
              const hex = color ? MTG_COLOR_MAP[color].hex : theme.axisColor;
              const isActive = !activeFilter || (color && activeFilter === color);
              return (
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={hex}
                  fontSize={13}
                  fontWeight={600}
                  opacity={isActive ? 1 : 0.35}
                  cursor="pointer"
                  onClick={() => {
                    if (color && onSliceClick) onSliceClick(color);
                  }}
                >
                  {payload.value}
                </text>
              );
            }}
          />
          <PolarRadiusAxis tick={false} axisLine={false} />
          <Radar
            dataKey="value"
            stroke={strokeColor}
            fill={fillColor}
            fillOpacity={0.35}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={tooltipContentStyle(theme)}
            formatter={(value, _name, props) => {
              const point = (props as { payload: RadarPoint }).payload;
              const numValue = Number(value ?? 0);
              const total = radarData.reduce((s, d) => s + d.value, 0);
              const pct = total > 0 ? ((point.value) / total * 100).toFixed(1) : '0';
              return [`${Math.round(numValue)} (${pct}%)`, point.label];
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
      {colorlessCount > 0 && (
        <div className="absolute bottom-2 right-4 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
          {t('analytics.colorless', { count: colorlessCount })}
        </div>
      )}
    </div>
  );
}
