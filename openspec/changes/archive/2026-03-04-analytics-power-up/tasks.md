## 1. Foundation: shared constants and utilities

- [x] 1.1 Create `frontend/src/components/analytics/constants.ts` with shared palettes (RARITY_COLORS, MTG_COLOR_MAP, CHART_COLORS), theme helper types, and tooltip style factory
- [x] 1.2 Create `frontend/src/components/analytics/useCountUp.ts` hook — animate from 0 (or previous) to target value over ~800ms with ease-out using requestAnimationFrame
- [x] 1.3 Create `frontend/src/components/analytics/ChartCard.tsx` — reusable card wrapper with title, loading skeleton, error+retry states, and optional badge slot (for avg CMC)

## 2. Chart components

- [x] 2.1 Create `frontend/src/components/analytics/RarityChart.tsx` — bar chart with rarity gradient colors, click handler prop, active filter opacity dimming
- [x] 2.2 Create `frontend/src/components/analytics/ColorRadar.tsx` — WUBRG radar chart: transform API color_identity data into 5-axis radar values (distribute multi-color across axes), colorless count label, click handler per axis, minimum baseline for visibility
- [x] 2.3 Create `frontend/src/components/analytics/ManaCurve.tsx` — area chart with vertical gradient fill, average CMC badge (weighted mean excluding Unknown), click handler for drill-down
- [x] 2.4 Create `frontend/src/components/analytics/TopSetsChart.tsx` — horizontal bar chart, click handler, active filter opacity dimming

## 3. KPI component

- [x] 3.1 Create `frontend/src/components/analytics/KpiCards.tsx` — 4-card row: Total Cards, Total Value (EUR), Mythic Rares (derived from rarity data), Average Price. Each uses useCountUp for animated numbers. Accepts stats + rarityData props. Loading skeleton and error states.

## 4. Barrel export and integration

- [x] 4.1 Create `frontend/src/components/analytics/index.ts` barrel export for all public components
- [x] 4.2 Refactor `frontend/src/pages/Analytics.tsx` to import and use the new modular components, removing all inline chart code, palettes, and helpers. Preserve existing drill-down logic and filter chip UI.

## 5. i18n and polish

- [x] 5.1 Add any new translation keys to `frontend/src/locales/en.json` and `frontend/src/locales/es.json` (e.g., mythic KPI label, avg CMC label, colorless label)
- [x] 5.2 Verify dark/light theme rendering across all new components
