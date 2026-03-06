## Context

The Analytics page (`frontend/src/pages/Analytics.tsx`) is a ~520-line monolith with all chart logic, color palettes, helpers, and layout inline. Charts use basic Recharts defaults (bar + pie) with no MTG personality. KPIs are plain number boxes.

The user wants these components to be reusable in a future deck stats view, so extraction into a modular component library is the primary architectural goal.

## Goals / Non-Goals

**Goals:**
- Extract analytics charts into reusable components under `frontend/src/components/analytics/`
- Replace color identity donut with WUBRG radar chart (Recharts `RadarChart`)
- Replace mana curve bar chart with area chart + gradient + average CMC badge
- Enhance KPI cards with count-up animation, mythic count, and top valuable card
- All components accept data via props — no hardcoded API calls inside

**Non-Goals:**
- No new backend endpoints or API changes
- No new npm dependencies (Recharts already has RadarChart, AreaChart built-in)
- No deck stats page (just make components reusable for it)
- No framer-motion or heavy animation library — CSS + requestAnimationFrame only

## Decisions

### 1. Component architecture: props-driven, no internal fetching

Each chart component receives data + config via props. The parent page (Analytics, future DeckStats) owns the data fetching and drill-down state.

```
frontend/src/components/analytics/
  ├── index.ts                    → barrel export
  ├── KpiCards.tsx                 → KPI row (total, value, mythics, top card)
  ├── ColorRadar.tsx              → WUBRG radar/pentagon chart
  ├── ManaCurve.tsx               → Area chart with gradient + avg CMC badge
  ├── RarityChart.tsx             → Bar chart (improved with gradients)
  ├── TopSetsChart.tsx            → Horizontal bar chart
  ├── ChartCard.tsx               → Reusable card wrapper (loading/error/retry)
  ├── useCountUp.ts               → Hook for animated number counting
  └── constants.ts                → Shared palettes (RARITY_COLORS, MTG_COLOR_MAP, etc.)
```

**Why**: Props-driven means a DeckStats page can pass deck-scoped data to the same components. No coupling to collection-level API calls.

**Alternative considered**: Context provider for analytics data. Rejected — too much ceremony for what amounts to passing ~4 data arrays.

### 2. WUBRG Radar chart for color identity

Use Recharts `RadarChart` with 5 axes (W, U, B, R, G). Data transformation: collapse multi-color entries by distributing count across constituent colors (e.g., a "WU" card contributes +1 to both W and U axes). Colorless shown as center label or separate stat.

```
Props:
  data: { color_identity: string; count: number }[]   → from API
  activeFilter?: string                                → for drill-down highlight
  onSliceClick?: (color: string) => void               → drill-down handler
  isDark: boolean                                      → theme
```

**Why radar over donut**: The pentagon IS Magic's color wheel. Every player recognizes it instantly. It also shows your "shape" — heavy in two colors = Golgari, balanced = 5-color.

**Trade-off**: Multi-color combos (WU, BRG, etc.) get distributed across axes rather than shown as distinct slices. The donut was better at showing "I have 50 Azorius cards." Mitigated by showing the raw color identity breakdown in a tooltip or secondary view if needed later.

### 3. Mana curve as area chart with gradient

Use Recharts `AreaChart` with a linear gradient fill (indigo → transparent downward). Show average CMC as a badge in the top-right corner of the chart card.

```
Props:
  data: { cmc: string; count: number }[]
  activeFilter?: string
  onBarClick?: (cmc: string) => void
  isDark: boolean
```

**Why area over bars**: Mana curves are traditionally shown as smooth distributions. The area fill with gradient gives a more organic, fluid feel. The shape is instantly readable (aggro = left-heavy, control = right-heavy).

### 4. Count-up animation via custom hook

`useCountUp(target, duration?)` — uses `requestAnimationFrame` to animate from 0 to target over ~800ms with ease-out. Returns the current display value.

**Why not a library**: It's ~20 lines of code. Adding `react-countup` or similar for this is unnecessary.

### 5. Enhanced KPIs: derive mythic count and top card from existing data

- **Mythic count**: Extract from the rarity distribution data already fetched (`rarityData.find(r => r.rarity === 'mythic')?.count ?? 0`). Zero additional API calls.
- **Top valuable card**: This requires knowing the single most expensive card. The current stats endpoint returns `average_price` but not the top card. **Decision**: For now, replace "Average Price" KPI with "Mythic Rares" count (derived from rarity data). Top valuable card deferred — would need a new endpoint.

### 6. Theme integration

All components accept `isDark: boolean` and derive their own colors. Shared constants in `constants.ts` provide base palettes. This matches the existing `useTheme()` pattern.

## Risks / Trade-offs

- **Radar chart readability**: With very unbalanced collections (99% one color), the radar looks like a spike. → Mitigation: Use a minimum baseline so the shape is always visible; add % labels on each axis.
- **Breaking familiarity**: Users of the current donut chart might miss seeing multi-color combos as distinct slices. → Mitigation: Keep the raw distribution data accessible via tooltips on the radar points.
- **Component API surface**: Making components too configurable creates complexity. → Mitigation: Start with minimal props (data + handlers + theme). Add config props only when the deck stats view needs them.
