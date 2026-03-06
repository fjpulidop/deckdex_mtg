## Why

The collection API loads every card into memory for every request — filtering and pagination happen in Python after a full-collection fetch. At scale (5k+ cards) this becomes a memory and latency bottleneck. More critically, the collection cache is a single global dict not keyed by user_id, meaning cached data from one user leaks to another — a correctness bug that must be fixed immediately.

## What Changes

- **CRITICAL BUG FIX**: Key `_collection_cache` by `user_id` in `backend/api/dependencies.py` to prevent cross-user data leakage.
- Add `get_cards_filtered(user_id, filters, limit, offset) -> (cards, total)` to `deckdex/storage/repository.py` with parameterized SQL WHERE/LIMIT/OFFSET.
- Replace `get_cached_collection() + filter_collection() + calculate_stats()` in `routes/stats.py` with a single SQL aggregation query (Postgres path).
- Replace Python Counter loops in `routes/analytics.py` with SQL GROUP BY queries for all 5 endpoints (Postgres path).
- **BREAKING**: Change `GET /api/cards` response from `Card[]` to `{ items: Card[], total: number, limit: number, offset: number }`.
- Add `GET /api/cards/filter-options` returning distinct type_line and set_name values.
- Update frontend `api/client.ts`, `hooks/useApi.ts`, `Dashboard.tsx`, and `CardTable.tsx` to use paginated response and filter-options endpoint.

## Non-goals

- Virtual scrolling / infinite scroll UI (not in scope; server pagination controls only)
- Combined `/api/analytics/all` single-request endpoint (future optimization)
- Redis/memcached caching (future)
- Google Sheets performance optimization (Python path kept as-is)

## Capabilities

### New Capabilities
- `sql-filtering-and-pagination`: SQL-level parameterized filtering, LIMIT/OFFSET pagination with total count, and filter-options endpoint for the Postgres path.

### Modified Capabilities
- `web-api-backend`: Cards list endpoint response shape changes (paginated wrapper); new filter-options endpoint added.
- `web-dashboard-ui`: Dashboard and CardTable consume paginated response; filter options from dedicated endpoint.

## Impact

- `deckdex/storage/repository.py`: New `get_cards_filtered()` and `get_cards_stats()` methods on `PostgresCollectionRepository`
- `backend/api/dependencies.py`: Cache keyed by user_id
- `backend/api/routes/cards.py`: Paginated response model; new `/filter-options` endpoint
- `backend/api/routes/stats.py`: SQL aggregation for Postgres path
- `backend/api/routes/analytics.py`: SQL GROUP BY for Postgres path (5 endpoints)
- `frontend/src/api/client.ts`: New `CardListResponse` type; updated `getCards()` return type; new `getFilterOptions()`
- `frontend/src/hooks/useApi.ts`: Updated `useCards` hook; new `useFilterOptions` hook
- `frontend/src/pages/Dashboard.tsx`: Remove `limit: 10000`; use filter-options endpoint
- `frontend/src/components/CardTable.tsx`: Accept and display server-side pagination total
