## Context

The app has a main Dashboard (card list, stats, filters) and a Settings page. Stats and cards are filtered via shared logic (`filter_collection` in `backend/api/filters.py`) and served by GET `/api/stats` and GET `/api/cards`. The collection is provided by `get_cached_collection()` (or repository when Postgres is configured). There is no analytics layer today. The data model includes Card fields: rarity, type_line, set_name, color_identity, cmc, price; PriceHistory exists for temporal data but may not be populated in all deployments. The frontend uses React, Vite, Tailwind, TanStack Query, and a shared theme (light/dark).

## Goals / Non-Goals

**Goals:**
- Add an Analytics (beta) page reachable from the main nav, with KPIs and charts (rarity, color identity, CMC, set).
- Make the dashboard interactive: clicking a chart segment applies a drill-down filter and all data (KPIs + charts) refetches with that filter.
- Reuse existing filter semantics and collection access; keep backend changes localized (new routes, aggregation logic).
- Use a single, consistent charting approach and theme-aware visuals.

**Non-Goals:**
- Price history / time-series charts in the first version (can be added later when PriceHistory is reliably populated).
- Export or report generation.
- Real-time streaming of analytics; polling or refetch on interaction is sufficient.

## Decisions

### 1. Analytics API shape: dedicated prefix and one summary endpoint

- **Choice:** New router under `/api/analytics/` with endpoints: e.g. `GET /api/analytics/summary`, `GET /api/analytics/rarity`, `GET /api/analytics/color-identity`, `GET /api/analytics/cmc`, `GET /api/analytics/sets`. Each accepts the same optional query params as `/api/stats` (search, rarity, type, set_name, price_min, price_max).
- **Rationale:** Clear separation from stats/cards; frontend can call summary once for KPIs and then one request per chart (or batch if we add a composite endpoint later). Same filter contract as the rest of the app.
- **Alternatives:** Single GET `/api/analytics` returning all aggregations in one payload — reduces round-trips but larger response; we can introduce that later if needed.

### 2. Backend aggregation: reuse filtered collection, aggregate in memory (or SQL when Postgres)

- **Choice:** Use existing `get_cached_collection()` (or repository) and `filter_collection()` with the request’s filter params; then compute aggregations (count by rarity, color_identity, cmc, set_name) over the filtered list. When the backing store is Postgres, implement equivalent logic with SQL (GROUP BY) and the same filter conditions to avoid loading full collection into memory.
- **Rationale:** Keeps behavior consistent with stats/cards and avoids duplicating filter logic. In-memory aggregation is acceptable for moderate collection sizes; SQL path scales better when DB is present.
- **Alternatives:** Always use SQL when available; keep in-memory only for Sheets — acceptable and can be refined in a follow-up.

### 3. Color identity normalization

- **Choice:** Expose color identity as returned by the data model (e.g. "W", "U", "WU", "C" for colorless). If the model stores a string or array, normalize to a canonical string key per card (e.g. sorted "WUBRG" substring or "C") and aggregate counts per key. Top N or limit for the sets endpoint (e.g. 10) to keep the sets chart readable.
- **Rationale:** Matches how cards are stored; frontend can display as-is or map to labels. No schema change required.

### 4. Frontend chart library

- **Choice:** Use a single charting library (e.g. Recharts or Nivo) that supports bar/pie/area charts, theming, and click handlers. Prefer one that works well with React and Tailwind and supports dark mode.
- **Rationale:** Consistency and maintainability; one dependency to theme and style. Specific library can be chosen at implementation time (Recharts is a common choice).
- **Alternatives:** Chart.js, Victory; decision can be finalized during implementation.

### 5. Drill-down state: URL query params vs local state

- **Choice:** Hold drill-down filters (e.g. rarity=Rare) in React state on the Analytics page; optional enhancement: sync to URL query params so "Analytics?rarity=Rare" is shareable and back/forward work. MVP can ship with local state only.
- **Rationale:** Simplest MVP is local state; URL sync improves shareability and bookmarking without changing the API.
- **Alternatives:** Full URL-only state from day one — more complexity; can add later.

### 6. KPIs on Analytics page: reuse GET /api/stats vs dedicated summary

- **Choice:** Use existing GET `/api/stats` with the same filter params (including drill-down) for the Analytics page KPIs. No separate `/api/analytics/summary` unless we later need extra fields (e.g. distinct sets count). Spec already allows "existing or new endpoint."
- **Rationale:** Avoids duplicate logic and keeps one source of truth for total_cards, total_value, average_price.
- **Alternatives:** New `/api/analytics/summary` that returns same shape — redundant unless we add analytics-specific metrics later.

## Risks / Trade-offs

- **Heavy drill-down + large collection:** Many clicks that change filters can cause a burst of requests. Mitigation: optional short TTL cache per filter key (similar to stats cache) for analytics endpoints; debounce or batch refetches on the frontend if needed.
- **Sheets backend:** In-memory aggregation over full collection could be slow for very large Sheets. Mitigation: keep collection cache as-is; if performance becomes an issue, recommend Postgres or add pagination/limits for analytics when using Sheets.
- **Color identity shape:** If the stored field varies (string vs array), aggregation logic must normalize. Mitigation: define a small helper that maps each card to a single color-identity key for grouping.

## Migration Plan

- No data migration. Feature is additive: new route, new page, new API routes.
- Deploy: ship backend with new analytics routes; ship frontend with Analytics link and page. No feature flag required for beta; link label "Analytics (beta)" sets expectation.
- Rollback: remove Analytics link and route; disable or remove analytics router in backend if needed.

## Open Questions

- Whether to add a composite `GET /api/analytics` that returns summary + all aggregations in one response to reduce latency (can be done in a follow-up).
- Exact chart library and chart types (bar vs pie for rarity/color) — to be fixed at implementation time per design system and accessibility.
