# Analytics & Prices Exploration (2026-03-07, updated)

## Current State Assessment

### Backend Endpoints (All Implemented)

| Endpoint | Description | Postgres Path | Sheets Path |
|----------|-------------|---------------|-------------|
| `GET /api/analytics/rarity` | Count per rarity | SQL GROUP BY | Python Counter |
| `GET /api/analytics/color-identity` | Count per color identity | SQL GROUP BY + Python normalize | Python Counter |
| `GET /api/analytics/cmc` | Count per CMC bucket (0-6, 7+, Unknown) | SQL CASE bucketing | Python Counter |
| `GET /api/analytics/sets` | Top N sets by count | SQL GROUP BY + LIMIT | Python Counter |
| `GET /api/analytics/type` | Count per primary type | SQL filter + Python `_extract_primary_type` | Python Counter |
| `GET /api/stats/` | Total cards, total value, avg price | SQL aggregation (single query) | Python aggregation |
| `GET /api/cards/{id}/price-history` | Per-card price time-series | SQL query on price_history table | N/A |

All analytics endpoints accept consistent filter params: `search`, `rarity`, `type`, `set_name`, `price_min`, `price_max`, `color_identity`, `cmc`.

All endpoints have a 30-second in-memory TTL cache keyed by `(endpoint, user_id, ...filter_params)`.

### Frontend Components (All Implemented)

| Component | Chart Type | Library | Location |
|-----------|-----------|---------|----------|
| `KpiCards` | 4 animated KPI cards (Total Cards, Total Value, Mythic Rares, Avg Price) | Custom `useCountUp` hook | `components/analytics/` |
| `RarityChart` | Vertical bar chart | Recharts `BarChart` | `components/analytics/` |
| `ColorRadar` | WUBRG radar/pentagon | Recharts `RadarChart` | `components/analytics/` |
| `ManaCurve` | Area chart with gradient + Avg CMC badge | Recharts `AreaChart` | `components/analytics/` |
| `TopSetsChart` | Horizontal bar chart | Recharts `BarChart` (vertical layout) | `components/analytics/` |
| `TypeDistributionChart` | Horizontal bar chart (full width) | Recharts `BarChart` (vertical layout) | `components/analytics/` |
| `ChartCard` | Wrapper: loading skeleton, error+retry, title+badge | N/A | `components/analytics/` |
| `PriceChart` | Per-card price history line chart | Recharts `LineChart` | `components/PriceChart.tsx` |

Supporting infrastructure:
- `constants.ts`: RARITY_COLORS, TYPE_COLORS, MTG_COLOR_MAP, WUBRG_ORDER, CHART_COLORS, buildChartTheme, formatCurrency, colorIdentityLabel/Hex/Short
- `useCountUp.ts`: Animated number hook (ease-out, ~800ms, from previous value to new)
- Barrel export `index.ts`: exports all components + types + constants
- Recharts `^3.7.0` in package.json

### Price History (Recently Implemented)

- Migration `014_price_history.sql` creates table: `id, card_id, recorded_at, source, currency, price NUMERIC(10,2)`
- Repository has `record_price()` and `get_price_history()` methods
- `magic_card_processor.py` inserts price_history row on each price update
- `GET /api/cards/{id}/price-history` endpoint exists
- `PriceChart.tsx` is real implementation (not placeholder anymore) -- LineChart with proper dark mode, loading skeleton, empty state
- Rendered inside `CardDetailModal.tsx`

### Drill-Down System (Fully Working)

5 drill-down dimensions: `rarity`, `color_identity`, `cmc`, `set_name`, `type_line`
- Click any chart segment to toggle drill-down for that dimension
- All charts + KPIs refetch with new filter params
- Active filters shown as removable chips with "View All" clear button
- Clicking same segment twice clears that filter
- Reset Charts button clears all filters

### Tests

- `tests/test_api_extended.py`: 7 analytics-related tests
  - `TestAnalyticsRarity`: 3 tests (empty, returns list, aggregates correctly)
  - `TestAnalyticsSets`: 3 tests (returns 200, contains set_name, aggregates correctly)
  - `TestCardsColorIdentityFilter`: 1 test (filter excludes colorless)
- ZERO tests for: `/api/analytics/cmc`, `/api/analytics/color-identity`, `/api/analytics/type`, price history endpoint
- All tests mock `get_collection_repo` returning None (only test Sheets path, never Postgres SQL path)

### Collection Insights Overlap

The Insights system (17 questions on Dashboard) overlaps significantly with Analytics:
- Insights `by_color` = Analytics `/color-identity` (same data, different UI)
- Insights `by_rarity` = Analytics `/rarity`
- Insights `by_set` = Analytics `/sets`
- Insights `value_by_color` and `value_by_set` are unique to Insights (value-weighted)
- Both use separate Python-loop computation paths (duplicated logic)
- Insights live on Dashboard; Analytics is a separate page
- No cross-linking between them

## Gaps & Issues

### Bugs / Code Quality

1. **Type endpoint accesses private `_build_filter_clauses` and `_get_engine`**: The `/api/analytics/type` Postgres path reaches into repository internals (`_repo._build_filter_clauses`, `_repo._get_engine`) and executes raw SQL from the route layer. This violates the convention "all DB ops through repository.py" and couples the route to Postgres internals.

2. **Type endpoint imports inside function body**: `from sqlalchemy import text` and `from ..dependencies import get_collection_repo as _get_repo` are inside the function, plus redundant `_get_repo()` call alongside the already-obtained `repo`.

3. **Duplicated color identity normalization**: `_normalize_color_identity` exists in both `analytics.py` (imported from `utils.color`) and `filters.py` (local function). The analytics one uses the utility module, but insights_service.py has yet another copy.

4. **No value-weighted analytics endpoint**: The spec and Insights both have "value by color" and "value by set" but there's no analytics chart for value distribution. The KPIs show total value but no chart breaks it down.

5. **Test coverage gap**: 3 of 5 analytics endpoints have zero tests. All tests only exercise the Sheets (in-memory) path, never the Postgres SQL path.

6. **`_analytics_cache` is a module-level global dict**: Grows unbounded -- no max-size or LRU eviction. With many filter combinations and users, memory grows indefinitely.

### Missing Features (Spec vs Reality)

1. **No collection-level value snapshots**: The price_history table tracks per-card prices, but there's no daily aggregate "total collection value" snapshot. Can't show "my collection was worth X last month".

2. **No price trend charts on Analytics page**: Analytics page has zero price-related charts. All price data is per-card in CardDetailModal only. No "total value over time" or "price distribution histogram" on Analytics.

3. **No deck-level analytics**: Decks exist (deck_cards table) but no analytics endpoints or charts for deck composition (e.g., mana curve of a deck, color distribution of a deck).

4. **No format legality breakdown**: `catalog_cards.legalities` JSONB exists but no chart shows "how many of my cards are Standard-legal vs Modern-legal vs Commander-legal".

5. **No set completion tracking**: Could show "you have 47/280 cards from Innistrad: Midnight Hunt" -- data exists in catalog_cards.

6. **No export/share for analytics views**: Cannot export a chart as image or share a drill-down URL.

7. **No comparison view**: Cannot compare two drill-down states side by side (e.g., "my Red cards vs my Blue cards").

## Improvement Ideas

### Tier 1: Quick Wins (Low Effort, High Impact)

| Idea | Value | Complexity | Notes |
|------|-------|-----------|-------|
| **Fix type endpoint to use repository method** | Medium | Low | Add `type_line` dimension to `get_cards_analytics()` or add dedicated repo method. Removes route-layer SQL. ~1hr |
| **Add tests for cmc, color-identity, type endpoints** | Medium | Low | Follow existing TestAnalyticsRarity pattern. ~2hrs |
| **Add test for Postgres SQL path** | High | Medium | Need test Postgres or mock engine. Currently 0 SQL coverage. |
| **Consolidate `_normalize_color_identity`** | Low | Low | Single utility function, import everywhere. ~30min |
| **Cap analytics cache size** | Medium | Low | Add `maxlen` or use `functools.lru_cache`. ~30min |

### Tier 2: Moderate Effort, High Value

| Idea | Value | Complexity | Notes |
|------|-------|-----------|-------|
| **Value distribution chart (value by color/rarity)** | High | Medium | New endpoint `/api/analytics/value-by-color` aggregating SUM(price * qty). Reuse ColorRadar or new chart showing EUR per color. Unique differentiation -- Moxfield/EDHREC don't do this. |
| **Price histogram chart** | High | Medium | Distribution of card prices in buckets ($0-1, $1-5, $5-20, $20-50, $50+). Helps users understand their collection's price structure at a glance. |
| **Collection value over time chart** | High | Medium | Requires `collection_value_snapshots` table (daily cron aggregates price_history). LineChart on Analytics page. This is the #1 collector request. |
| **Cross-link Insights and Analytics** | Medium | Low | "See distribution chart" link from Insights `by_color` result navigates to Analytics with `color_identity` pre-filtered. |
| **Drill-down URL persistence** | Medium | Low | Store drill-down state in URL search params (like Dashboard already does for its filters). Enables sharing filtered analytics views. |

### Tier 3: Higher Effort, Strategic Value

| Idea | Value | Complexity | Notes |
|------|-------|-----------|-------|
| **Deck analytics page** | High | Large | Reuse modular chart components (ManaCurve, ColorRadar, TypeDistribution) for per-deck views. Spec already says components are designed for this. Big differentiator -- show mana curve, color pie, type split for each deck. |
| **Format legality breakdown** | High | Medium | Pie/bar chart showing how many cards are legal in each format. Uses `catalog_cards.legalities` JSONB. Unique -- no competitor does this for collections. |
| **Set completion tracker** | High | Large | Compare user's cards against catalog_cards to show completion % per set. Progress bars + visual set icons. Collector candy. |
| **"Compare" mode** | Medium | Large | Side-by-side comparison of two drill-down states or two decks. Complex UI but very powerful for deck builders. |
| **Analytics data export** | Medium | Medium | Export current view as CSV/PNG/PDF. Useful for tournament reports, trade planning. |

### Tier 4: Ambitious / Future

| Idea | Value | Complexity | Notes |
|------|-------|-----------|-------|
| **Metagame overlay** | Medium | Epic | Compare user's collection against top tournament decks to show "you can build 80% of this meta deck". Requires metagame data source. |
| **Price alert system** | High | Large | "Notify me when Sheoldred drops below X". Requires scheduled price checks + notification system. |
| **AI-powered collection analysis** | Medium | Large | "What Commander decks can I build with my collection?" -- uses OpenAI integration already in stack. |

## Priority Recommendation

**Immediate (this sprint):**
1. Fix type endpoint repository violation (~1hr)
2. Add missing analytics tests (~2hrs)
3. Cap analytics cache + consolidate normalize function (~1hr)

**Next sprint:**
4. Value distribution chart (value by color) -- highest differentiation, leverages existing infrastructure
5. Drill-down URL persistence -- small effort, makes analytics shareable
6. Collection value over time -- requires snapshot table, but highest user demand

**Medium term:**
7. Deck analytics (reuse modular components -- they were designed for this)
8. Format legality breakdown (unique competitive advantage)
9. Set completion tracker (collector engagement)

## Competitive Analysis Notes

- **Moxfield**: Has deck stats (mana curve, type distribution, color pie) but NO collection-level analytics. No price history charts.
- **EDHREC**: Recommendations engine, not analytics. No personal collection analysis.
- **Archidekt**: Deck stats similar to Moxfield. No collection analytics.
- **MTGGoldfish**: Price tracking exists but for individual cards, not personal collections. Metagame analysis is format-level, not collection-level.
- **TCGPlayer**: Price history per card exists. Collection value shown but no time-series.
- **Deckbox**: Basic collection stats. No interactive drill-down. No price history charts.

**DeckDex's unique positioning**: Collection-level interactive analytics with drill-down cross-filtering. No major platform offers this. The combination of WUBRG radar + type distribution + mana curve + interactive drill-down is genuinely novel. Adding value-over-time and deck analytics would widen the gap.
