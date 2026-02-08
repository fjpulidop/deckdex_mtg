## 1. Backend – Analytics API

- [x] 1.1 Add analytics router in `backend/api/routes/` with prefix `/api/analytics` and register it in `main.py`
- [x] 1.2 Implement GET `/api/analytics/rarity`: accept search, rarity, type, set_name, price_min, price_max; return list of { rarity, count } from filtered collection (reuse filter_collection / or SQL when Postgres)
- [x] 1.3 Implement GET `/api/analytics/color-identity`: same filter params; return list of { color_identity, count }; normalize color_identity from card model for grouping
- [x] 1.4 Implement GET `/api/analytics/cmc`: same filter params; return list of { cmc, count } (numeric or bucketed e.g. 7+)
- [x] 1.5 Implement GET `/api/analytics/sets`: same filter params; optional limit (default e.g. 10); return list of { set_name, count } ordered by count descending
- [x] 1.6 Add optional cache for analytics responses keyed by filter params (e.g. 30s TTL) to avoid repeated heavy aggregation

## 2. Frontend – Navigation and route

- [x] 2.1 Add route `/analytics` in `App.tsx` and create `Analytics` page component (e.g. `frontend/src/pages/Analytics.tsx`)
- [x] 2.2 Add "Analytics (beta)" link next to Settings in the Dashboard header (same flex/group as ThemeToggle and Settings)
- [x] 2.3 Ensure Analytics page uses same layout/theme as rest of app (ThemeContext, Tailwind)

## 3. Frontend – Analytics page data and KPIs

- [x] 3.1 Add API client functions for GET `/api/analytics/rarity`, `/color-identity`, `/cmc`, `/sets`, and use GET `/api/stats` with same params for KPIs
- [x] 3.2 On Analytics page, hold drill-down state (e.g. rarity, type, set_name, color_identity, cmc) in React state; pass as query params to stats and analytics endpoints
- [x] 3.3 Display KPI cards: total cards and total value (and optionally average price) for current context using GET `/api/stats` with current filters
- [x] 3.4 Add "View all" / "Clear filters" control that clears drill-down state and refetches all data for full collection

## 4. Frontend – Charts and interactivity

- [x] 4.1 Add charting library dependency (e.g. Recharts) and implement rarity chart (bar/column); fetch from GET `/api/analytics/rarity` with current filters; make each bar/segment clickable to set rarity in drill-down state
- [x] 4.2 Implement color-identity chart; fetch from GET `/api/analytics/color-identity`; make segments clickable to set color_identity in drill-down state
- [x] 4.3 Implement CMC chart; fetch from GET `/api/analytics/cmc`; make buckets clickable to set cmc in drill-down state
- [x] 4.4 Implement sets chart (top N); fetch from GET `/api/analytics/sets`; make set clickable to set set_name in drill-down state
- [x] 4.5 When drill-down state changes, refetch all analytics endpoints and GET `/api/stats` with the new params so KPIs and every chart update
- [x] 4.6 Display active drill-down context (e.g. chips or subtitle) so user knows current subset

## 5. Frontend – Loading, empty, and error states

- [x] 5.1 Show skeleton loaders (or spinners) for KPIs and charts while data is loading
- [x] 5.2 Show empty state when filtered context has zero cards (message, no misleading empty charts)
- [x] 5.3 Show error message and retry option when analytics or stats API fails
- [x] 5.4 Ensure charts use theme-aware colors and readable labels/legends (light/dark)
