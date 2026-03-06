import { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useStats } from '../hooks/useApi';
import { useTheme } from '../contexts/ThemeContext';
import {
  ChartCard, KpiCards, RarityChart, ColorRadar, ManaCurve, TopSetsChart, TypeDistributionChart,
  colorIdentityLabel,
} from '../components/analytics';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface DrillDown {
  rarity?: string;
  color_identity?: string;
  cmc?: string;
  set_name?: string;
  type_line?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function buildParams(drillDown: DrillDown): Record<string, string> {
  const params: Record<string, string> = {};
  if (drillDown.rarity) params.rarity = drillDown.rarity;
  if (drillDown.color_identity) params.color_identity = drillDown.color_identity;
  if (drillDown.cmc) params.cmc = drillDown.cmc;
  if (drillDown.set_name) params.set_name = drillDown.set_name;
  if (drillDown.type_line) params.type = drillDown.type_line;
  return params;
}

function statsParams(drillDown: DrillDown) {
  return {
    rarity: drillDown.rarity,
    set: drillDown.set_name,
    colorIdentity: drillDown.color_identity,
    cmc: drillDown.cmc,
    type: drillDown.type_line,
  };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function Analytics() {
  const { t } = useTranslation();
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
  const { data: typeData, isLoading: typeLoading, error: typeError, refetch: refetchType } = useQuery({
    queryKey: ['analytics', 'type', analyticsParams],
    queryFn: () => api.getAnalyticsType(analyticsParams),
    staleTime: 30000,
  });

  // Drill-down handlers
  const handleRarityClick = useCallback((entry: { rarity: string }) => {
    setDrillDown(prev => ({
      ...prev,
      rarity: prev.rarity === entry.rarity ? undefined : entry.rarity,
    }));
  }, []);

  const handleColorClick = useCallback((color: string) => {
    setDrillDown(prev => ({
      ...prev,
      color_identity: prev.color_identity === color ? undefined : color,
    }));
  }, []);

  const handleCmcClick = useCallback((cmc: string) => {
    setDrillDown(prev => ({
      ...prev,
      cmc: prev.cmc === cmc ? undefined : cmc,
    }));
  }, []);

  const handleSetClick = useCallback((entry: { set_name: string }) => {
    setDrillDown(prev => ({
      ...prev,
      set_name: prev.set_name === entry.set_name ? undefined : entry.set_name,
    }));
  }, []);

  const handleTypeClick = useCallback((entry: { type_line: string }) => {
    setDrillDown(prev => ({
      ...prev,
      type_line: prev.type_line === entry.type_line ? undefined : entry.type_line,
    }));
  }, []);

  const clearFilters = useCallback(() => setDrillDown({}), []);

  // Active filter chips
  const activeChips: { key: string; label: string }[] = [];
  if (drillDown.rarity) activeChips.push({ key: 'rarity', label: t('analytics.filterRarity', { value: drillDown.rarity }) });
  if (drillDown.color_identity) activeChips.push({ key: 'color_identity', label: t('analytics.filterColor', { value: colorIdentityLabel(drillDown.color_identity) }) });
  if (drillDown.cmc) activeChips.push({ key: 'cmc', label: t('analytics.filterCmc', { value: drillDown.cmc }) });
  if (drillDown.set_name) activeChips.push({ key: 'set_name', label: t('analytics.filterSet', { value: drillDown.set_name }) });
  if (drillDown.type_line) activeChips.push({ key: 'type_line', label: t('analytics.filterType', { value: drillDown.type_line }) });

  const removeChip = useCallback((key: string) => {
    setDrillDown(prev => ({ ...prev, [key]: undefined }));
  }, []);

  // Check if collection is empty (no cards at all)
  const isEmpty = !statsLoading && stats && stats.total_cards === 0 && !hasFilters;

  return (
    <div className="relative min-h-screen transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            {t('analytics.title')}
            <span className="ml-3 text-sm font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 px-2.5 py-0.5 rounded-full align-middle">
              {t('analytics.beta')}
            </span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {t('analytics.subtitle')}
          </p>
        </div>

        {/* Reset charts button */}
        <div className="mb-6">
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-600 transition-colors"
            title={t('analytics.resetChartsTitle')}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            {t('analytics.resetCharts')}
          </button>
        </div>

        {/* Active drill-down chips */}
        {hasFilters && (
          <div className="mb-6 flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400 mr-1">{t('analytics.filteredBy')}</span>
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
              {t('analytics.viewAll')}
            </button>
          </div>
        )}

        {/* Empty state */}
        {isEmpty && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">{t('analytics.emptyTitle')}</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-6">{t('analytics.emptyDesc')}</p>
            <Link to="/" className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">{t('analytics.goToDashboard')}</Link>
          </div>
        )}

        {!isEmpty && (
          <>
            {/* KPI Cards */}
            <KpiCards
              stats={stats}
              rarityData={rarityData}
              isLoading={statsLoading}
              error={statsError}
            />

            {/* Charts grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Rarity Distribution */}
              <ChartCard title={t('analytics.charts.byRarity')} isLoading={rarityLoading} error={rarityError} onRetry={refetchRarity}>
                {rarityData && rarityData.length > 0 && (
                  <RarityChart
                    data={rarityData}
                    activeFilter={drillDown.rarity}
                    onBarClick={handleRarityClick}
                    isDark={isDark}
                  />
                )}
              </ChartCard>

              {/* Color Identity — WUBRG Radar */}
              <ChartCard title={t('analytics.charts.byColor')} isLoading={colorLoading} error={colorError} onRetry={refetchColor}>
                {colorData && colorData.length > 0 && (
                  <ColorRadar
                    data={colorData}
                    activeFilter={drillDown.color_identity}
                    onSliceClick={handleColorClick}
                    isDark={isDark}
                  />
                )}
              </ChartCard>

              {/* CMC Curve — Area chart */}
              <ChartCard title={t('analytics.charts.manaCurve')} isLoading={cmcLoading} error={cmcError} onRetry={refetchCmc}>
                {cmcData && cmcData.length > 0 && (
                  <ManaCurve
                    data={cmcData}
                    activeFilter={drillDown.cmc}
                    onBarClick={handleCmcClick}
                    isDark={isDark}
                  />
                )}
              </ChartCard>

              {/* Top Sets */}
              <ChartCard title={t('analytics.charts.topSets')} isLoading={setsLoading} error={setsError} onRetry={refetchSets}>
                {setsData && setsData.length > 0 && (
                  <TopSetsChart
                    data={setsData}
                    activeFilter={drillDown.set_name}
                    onBarClick={handleSetClick}
                    isDark={isDark}
                  />
                )}
              </ChartCard>

              {/* Type Distribution */}
              <div className="lg:col-span-2">
                <ChartCard title={t('analytics.charts.byType')} isLoading={typeLoading} error={typeError} onRetry={refetchType}>
                  {typeData && typeData.length > 0 && (
                    <TypeDistributionChart
                      data={typeData}
                      activeFilter={drillDown.type_line}
                      onBarClick={handleTypeClick}
                      isDark={isDark}
                    />
                  )}
                </ChartCard>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
