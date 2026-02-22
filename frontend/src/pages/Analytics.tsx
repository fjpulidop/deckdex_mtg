import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { api } from '../api/client';
import { useStats } from '../hooks/useApi';
import { useTheme } from '../contexts/ThemeContext';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface DrillDown {
  rarity?: string;
  color_identity?: string;
  cmc?: string;
  set_name?: string;
}

// ---------------------------------------------------------------------------
// Color palettes
// ---------------------------------------------------------------------------
const RARITY_COLORS: Record<string, string> = {
  common: '#9ca3af',
  uncommon: '#6ee7b7',
  rare: '#facc15',
  mythic: '#f97316',
  'mythic rare': '#f97316',
  special: '#a78bfa',
  bonus: '#f472b6',
};

const MTG_COLOR_MAP: Record<string, { label: string; hex: string }> = {
  W: { label: 'White', hex: '#f5f0e1' },
  U: { label: 'Blue', hex: '#0e68ab' },
  B: { label: 'Black', hex: '#4b4b4b' },
  R: { label: 'Red', hex: '#d32029' },
  G: { label: 'Green', hex: '#00733e' },
  C: { label: 'Colorless', hex: '#9ca3af' },
};

const CHART_COLORS = ['#6366f1', '#06b6d4', '#f59e0b', '#ef4444', '#22c55e', '#a855f7', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6'];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function buildParams(drillDown: DrillDown): Record<string, string> {
  const params: Record<string, string> = {};
  if (drillDown.rarity) params.rarity = drillDown.rarity;
  if (drillDown.color_identity) {
    // The backend doesn't have a native color_identity filter in filter_collection,
    // but we pass it anyway; aggregation endpoints will return the full set and we
    // do client-side narrowing only for KPIs — KPIs use /api/stats which doesn't
    // understand color_identity directly.  So we skip it for stats params.
  }
  if (drillDown.set_name) params.set_name = drillDown.set_name;
  // cmc filter not supported natively by the cards filter either; skip for stats
  return params;
}

function statsParams(drillDown: DrillDown) {
  const p: Record<string, string | undefined> = {};
  if (drillDown.rarity) p.rarity = drillDown.rarity;
  if (drillDown.set_name) p.set_name = drillDown.set_name;
  return {
    rarity: p.rarity,
    set: p.set_name,
  };
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(value);
}

function colorIdentityLabel(ci: string): string {
  if (!ci || ci === 'C') return 'Colorless';
  // Backend now sends normalized WUBRG codes like "W", "WU", "WUBRG"
  const letters = ci.split('').filter(c => MTG_COLOR_MAP[c]);
  if (letters.length === 0) return ci; // fallback
  if (letters.length === 1) return MTG_COLOR_MAP[letters[0]].label;
  return letters.map(c => MTG_COLOR_MAP[c]?.label ?? c).join('/');
}

function colorIdentityHex(ci: string): string {
  if (!ci || ci === 'C') return MTG_COLOR_MAP['C'].hex;
  const letters = ci.split('').filter(c => MTG_COLOR_MAP[c]);
  if (letters.length === 0) return '#6366f1';
  // For mono: exact color; for multi: use the first color
  return MTG_COLOR_MAP[letters[0]]?.hex ?? '#6366f1';
}

function colorIdentityShort(ci: string): string {
  if (!ci || ci === 'C') return 'C';
  // For pie label: "W" → "White", "WU" → "W/U" (short), "WUBRG" → "5C"
  const letters = ci.split('').filter(c => MTG_COLOR_MAP[c]);
  if (letters.length === 0) return ci;
  if (letters.length === 1) return MTG_COLOR_MAP[letters[0]].label;
  if (letters.length >= 4) return `${letters.length}C`;
  return letters.join('/');
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function Analytics() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [drillDown, setDrillDown] = useState<DrillDown>({});

  const hasFilters = Object.values(drillDown).some(Boolean);

  // Build query params for analytics endpoints
  const analyticsParams = useMemo(() => buildParams(drillDown), [drillDown]);

  // Stats KPIs
  const statsFilters = useMemo(() => statsParams(drillDown), [drillDown]);
  const { data: stats, isLoading: statsLoading, error: statsError } = useStats(statsFilters);

  // Analytics queries
  const { data: rarityData, isLoading: rarityLoading, error: rarityError, refetch: refetchRarity } = useQuery({
    queryKey: ['analytics', 'rarity', analyticsParams],
    queryFn: () => api.getAnalyticsRarity(analyticsParams),
    staleTime: 30000,
  });
  const { data: colorData, isLoading: colorLoading, error: colorError, refetch: refetchColor } = useQuery({
    queryKey: ['analytics', 'color-identity', analyticsParams],
    queryFn: () => api.getAnalyticsColorIdentity(analyticsParams),
    staleTime: 30000,
  });
  const { data: cmcData, isLoading: cmcLoading, error: cmcError, refetch: refetchCmc } = useQuery({
    queryKey: ['analytics', 'cmc', analyticsParams],
    queryFn: () => api.getAnalyticsCmc(analyticsParams),
    staleTime: 30000,
  });
  const { data: setsData, isLoading: setsLoading, error: setsError, refetch: refetchSets } = useQuery({
    queryKey: ['analytics', 'sets', analyticsParams],
    queryFn: () => api.getAnalyticsSets(analyticsParams),
    staleTime: 30000,
  });

  // Drill-down handlers
  const handleRarityClick = useCallback((entry: { rarity: string }) => {
    setDrillDown(prev => ({
      ...prev,
      rarity: prev.rarity === entry.rarity ? undefined : entry.rarity,
    }));
  }, []);

  const handleColorClick = useCallback((entry: { color_identity: string }) => {
    setDrillDown(prev => ({
      ...prev,
      color_identity: prev.color_identity === entry.color_identity ? undefined : entry.color_identity,
    }));
  }, []);

  const handleCmcClick = useCallback((entry: { cmc: string }) => {
    setDrillDown(prev => ({
      ...prev,
      cmc: prev.cmc === entry.cmc ? undefined : entry.cmc,
    }));
  }, []);

  const handleSetClick = useCallback((entry: { set_name: string }) => {
    setDrillDown(prev => ({
      ...prev,
      set_name: prev.set_name === entry.set_name ? undefined : entry.set_name,
    }));
  }, []);

  const clearFilters = useCallback(() => setDrillDown({}), []);

  // Theme-aware chart styles
  const axisColor = isDark ? '#9ca3af' : '#6b7280';
  const gridColor = isDark ? '#374151' : '#e5e7eb';
  const tooltipBg = isDark ? '#1f2937' : '#ffffff';
  const tooltipBorder = isDark ? '#374151' : '#e5e7eb';
  const tooltipTextColor = isDark ? '#ffffff' : '#111827';
  const tooltipContentStyle = {
    backgroundColor: tooltipBg,
    border: `1px solid ${tooltipBorder}`,
    borderRadius: 8,
    color: tooltipTextColor,
  };
  const tooltipItemStyle = { color: tooltipTextColor };
  const tooltipLabelStyle = { color: tooltipTextColor };

  // Active filter chips
  const activeChips: { key: string; label: string }[] = [];
  if (drillDown.rarity) activeChips.push({ key: 'rarity', label: `Rarity: ${drillDown.rarity}` });
  if (drillDown.color_identity) activeChips.push({ key: 'color_identity', label: `Color: ${colorIdentityLabel(drillDown.color_identity)}` });
  if (drillDown.cmc) activeChips.push({ key: 'cmc', label: `CMC: ${drillDown.cmc}` });
  if (drillDown.set_name) activeChips.push({ key: 'set_name', label: `Set: ${drillDown.set_name}` });

  const removeChip = useCallback((key: string) => {
    setDrillDown(prev => ({ ...prev, [key]: undefined }));
  }, []);

  // Is everything loading?
  const allLoading = statsLoading && rarityLoading && colorLoading && cmcLoading && setsLoading;

  // Check if collection is empty (no cards at all)
  const isEmpty = !statsLoading && stats && stats.total_cards === 0 && !hasFilters;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Analytics
            <span className="ml-3 text-sm font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 px-2.5 py-0.5 rounded-full align-middle">
              beta
            </span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Insights about your Magic: The Gathering collection
          </p>
        </div>

        {/* Reset charts button */}
        <div className="mb-6">
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-600 transition-colors"
            title="Reset all chart filters and restore original view"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            Reset Charts
          </button>
        </div>

        {/* Active drill-down chips */}
        {hasFilters && (
          <div className="mb-6 flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400 mr-1">Filtered by:</span>
            {activeChips.map(chip => (
              <button
                key={chip.key}
                onClick={() => removeChip(chip.key)}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
              >
                {chip.label}
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            ))}
            <button
              onClick={clearFilters}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 underline ml-2"
            >
              View all
            </button>
          </div>
        )}

        {/* Empty state */}
        {isEmpty && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">No cards in your collection yet</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-6">Add some cards to see analytics about your library.</p>
            <Link to="/" className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">Go to Dashboard</Link>
          </div>
        )}

        {!isEmpty && (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
              {statsLoading ? (
                [1, 2, 3].map(i => (
                  <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 animate-pulse">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                    <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  </div>
                ))
              ) : statsError ? (
                <div className="col-span-3 bg-red-50 dark:bg-red-900/20 rounded-xl p-6 text-center">
                  <p className="text-red-600 dark:text-red-400 mb-2">Failed to load statistics</p>
                  <button onClick={() => window.location.reload()} className="text-sm text-red-500 hover:underline">Retry</button>
                </div>
              ) : stats && (
                <>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
                    <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Cards</div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white">{stats.total_cards.toLocaleString()}</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
                    <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Value</div>
                    <div className="text-3xl font-bold text-green-600 dark:text-green-400">{formatCurrency(stats.total_value)}</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
                    <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Average Price</div>
                    <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{formatCurrency(stats.average_price)}</div>
                  </div>
                </>
              )}
            </div>

            {/* Charts grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Rarity Distribution */}
              <ChartCard title="Distribution by Rarity" isLoading={rarityLoading} error={rarityError} onRetry={refetchRarity}>
                {rarityData && rarityData.length > 0 && (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={rarityData} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis dataKey="rarity" tick={{ fill: axisColor, fontSize: 12 }} tickLine={{ stroke: axisColor }} />
                      <YAxis tick={{ fill: axisColor, fontSize: 12 }} tickLine={{ stroke: axisColor }} />
                      <Tooltip
                        contentStyle={tooltipContentStyle}
                        itemStyle={tooltipItemStyle}
                        labelStyle={tooltipLabelStyle}
                        cursor={{ fill: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
                      />
                      <Bar
                        dataKey="count"
                        radius={[6, 6, 0, 0]}
                        cursor="pointer"
                        onClick={(_: unknown, idx: number) => {
                          if (rarityData[idx]) handleRarityClick(rarityData[idx]);
                        }}
                      >
                        {rarityData.map((entry, idx) => (
                          <Cell
                            key={idx}
                            fill={RARITY_COLORS[entry.rarity.toLowerCase()] ?? CHART_COLORS[idx % CHART_COLORS.length]}
                            opacity={drillDown.rarity && drillDown.rarity !== entry.rarity ? 0.3 : 1}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              {/* Color Identity */}
              <ChartCard title="Distribution by Color Identity" isLoading={colorLoading} error={colorError} onRetry={refetchColor}>
                {colorData && colorData.length > 0 && (() => {
                  // Limit to top 8 slices; group the rest as "Other"
                  const MAX_SLICES = 8;
                  let pieData: { color_identity: string; count: number }[];
                  if (colorData.length <= MAX_SLICES) {
                    pieData = colorData;
                  } else {
                    const top = colorData.slice(0, MAX_SLICES);
                    const otherCount = colorData.slice(MAX_SLICES).reduce((acc, d) => acc + d.count, 0);
                    pieData = [...top, { color_identity: 'Multi', count: otherCount }];
                  }
                  return (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={pieData}
                          dataKey="count"
                          nameKey="color_identity"
                          cx="50%"
                          cy="50%"
                          outerRadius={100}
                          innerRadius={50}
                          paddingAngle={2}
                          cursor="pointer"
                          onClick={(_: unknown, idx: number) => {
                            if (pieData[idx] && pieData[idx].color_identity !== 'Multi') handleColorClick(pieData[idx]);
                          }}
                          label={(props: any) => {
                            const ci = String(props.color_identity ?? '');
                            const pct = Number(props.percent ?? 0);
                            if (pct < 0.03) return ''; // hide tiny labels
                            return `${colorIdentityShort(ci)} ${(pct * 100).toFixed(0)}%`;
                          }}
                          labelLine={false}
                        >
                          {pieData.map((entry, idx) => (
                            <Cell
                              key={idx}
                              fill={entry.color_identity === 'Multi' ? '#a78bfa' : colorIdentityHex(entry.color_identity)}
                              opacity={drillDown.color_identity && drillDown.color_identity !== entry.color_identity ? 0.3 : 1}
                              stroke={isDark ? '#1f2937' : '#ffffff'}
                              strokeWidth={2}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={tooltipContentStyle}
                          itemStyle={tooltipItemStyle}
                          labelStyle={tooltipLabelStyle}
                          formatter={(value: unknown, name: unknown) => [Number(value ?? 0), colorIdentityLabel(String(name ?? ''))]}
                        />
                        <Legend
                          formatter={(value: string) => colorIdentityShort(value)}
                          wrapperStyle={{ fontSize: 12, color: axisColor }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  );
                })()}
              </ChartCard>

              {/* CMC Curve */}
              <ChartCard title="Mana Curve (CMC)" isLoading={cmcLoading} error={cmcError} onRetry={refetchCmc}>
                {cmcData && cmcData.length > 0 && (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={cmcData} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis dataKey="cmc" tick={{ fill: axisColor, fontSize: 12 }} tickLine={{ stroke: axisColor }} />
                      <YAxis tick={{ fill: axisColor, fontSize: 12 }} tickLine={{ stroke: axisColor }} />
                      <Tooltip
                        contentStyle={tooltipContentStyle}
                        itemStyle={tooltipItemStyle}
                        labelStyle={tooltipLabelStyle}
                        cursor={{ fill: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
                      />
                      <Bar
                        dataKey="count"
                        radius={[6, 6, 0, 0]}
                        cursor="pointer"
                        onClick={(_: unknown, idx: number) => {
                          if (cmcData[idx]) handleCmcClick(cmcData[idx]);
                        }}
                      >
                        {cmcData.map((entry, idx) => (
                          <Cell
                            key={idx}
                            fill={CHART_COLORS[idx % CHART_COLORS.length]}
                            opacity={drillDown.cmc && drillDown.cmc !== entry.cmc ? 0.3 : 1}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              {/* Top Sets */}
              <ChartCard title="Top Sets by Card Count" isLoading={setsLoading} error={setsError} onRetry={refetchSets}>
                {setsData && setsData.length > 0 && (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={setsData} layout="vertical" margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                      <XAxis type="number" tick={{ fill: axisColor, fontSize: 12 }} tickLine={{ stroke: axisColor }} />
                      <YAxis
                        dataKey="set_name"
                        type="category"
                        width={140}
                        tick={{ fill: axisColor, fontSize: 11 }}
                        tickLine={{ stroke: axisColor }}
                      />
                      <Tooltip
                        contentStyle={tooltipContentStyle}
                        itemStyle={tooltipItemStyle}
                        labelStyle={tooltipLabelStyle}
                        cursor={{ fill: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
                      />
                      <Bar
                        dataKey="count"
                        radius={[0, 6, 6, 0]}
                        cursor="pointer"
                        onClick={(_: unknown, idx: number) => {
                          if (setsData[idx]) handleSetClick(setsData[idx]);
                        }}
                      >
                        {setsData.map((entry, idx) => (
                          <Cell
                            key={idx}
                            fill={CHART_COLORS[idx % CHART_COLORS.length]}
                            opacity={drillDown.set_name && drillDown.set_name !== entry.set_name ? 0.3 : 1}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reusable chart card wrapper
// ---------------------------------------------------------------------------
function ChartCard({
  title,
  isLoading,
  error,
  onRetry,
  children,
}: {
  title: string;
  isLoading: boolean;
  error: unknown;
  onRetry?: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{title}</h3>
      {isLoading ? (
        <div className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse flex flex-col items-center gap-2">
            <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="w-24 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      ) : error ? (
        <div className="h-[300px] flex flex-col items-center justify-center text-center">
          <p className="text-red-500 dark:text-red-400 mb-2 text-sm">Failed to load data</p>
          {onRetry && (
            <button onClick={() => onRetry()} className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
              Retry
            </button>
          )}
        </div>
      ) : (
        children
      )}
    </div>
  );
}
