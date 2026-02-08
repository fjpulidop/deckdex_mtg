# Proposal: Analytics Dashboard (beta)

## Why

Users need to understand their card library beyond the list and total value: distribution by rarity, colors, sets, CMC, price evolution, or strategy. An analytics dashboard provides immediate visibility and actionable insights (what’s gaining value, where the collection is concentrated, imbalances by color or type). It is a product opportunity that differentiates the app and leverages data we already have in the model (Card, PriceHistory, etc.).

## What Changes

- Add a main navigation link **"Analytics (beta)"** next to Settings that leads to a new page.
- New route `/analytics` and **Analytics** page with a dashboard of metrics and charts about the library.
- **Interactive** dashboard: when the user clicks an element in a chart (e.g. a rarity bar, a color segment), the other charts and KPIs recalculate for that subset (drill-down). The filter context is clear and can be cleared (e.g. "View all").
- Backend: new **aggregation** endpoints that return data ready for charts (counts by rarity, color, set, CMC, etc.) accepting the same filters as the drill-down (search, rarity, type, set, price range, and when applicable the "slice" chosen in another chart).
- Polished visual design: readable dashboard, prominent metrics, and consistent charts (palette, typography, responsive layout). It should feel like a product dashboard, not a raw report.

## Capabilities

### New Capabilities

- **analytics-dashboard**: Library analytics dashboard. Defines the main metrics to show (e.g. total value and card count in context, distribution by rarity, color identity, CMC, set, type; price evolution when history exists), the visualizations (which chart for each metric), interactive behavior (click → update context → recalculate the rest), and the experience (beta, navigation, empty/loading states). The spec does not mandate a specific chart library but does require usability and consistency with the rest of the dashboard.

### Modified Capabilities

- **web-dashboard-ui**: Add "Analytics (beta)" link in navigation (visible next to Settings), route `/analytics`, and a dedicated page that implements the analytics dashboard per the `analytics-dashboard` spec. Responsive; light/dark theme aligned with the rest of the app.
- **web-api-backend**: Expose aggregation endpoints for the dashboard (e.g. by rarity, color/color identity, set, CMC, type; and when applicable, temporal summaries for prices). Endpoints accept filter parameters (search, rarity, type, set_name, price_min, price_max, and when applicable drill-down–derived filters) and return aggregated data ready for charts (counts, sums, buckets). Reuse existing filter logic where possible; efficient queries over PostgreSQL.

## Impact

- **Frontend:** New `Analytics` page, chart components (and possibly a library such as Recharts, Chart.js, Nivo), local state or URL for drill-down context, calls to the new endpoints. Routes and link in `App.tsx` and in the bar/navigation where Settings lives.
- **Backend:** New routers or routes under `/api/analytics/` (or under `/api/` with a clear prefix), aggregation services or functions, grouped SQL queries. Optional cache per filter set to avoid overloading the DB under heavy use.
- **Data:** Read-only over the current model (Card, PriceHistory if present). No storage schema changes for the dashboard MVP.
- **Dependencies:** Possible new frontend dependency for charts; no other critical version changes.
