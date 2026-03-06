## Why

The collection API loads all cards into Python memory for every request — filtering, stats, and all 5 analytics aggregations run as Python iterations over the full dataset. A cache user-isolation bug (single global `_collection_cache` not keyed by user_id) allows one user's collection to be served to another. The `/api/cards` response returns a flat array with no total count, making proper pagination UI impossible.

## What Changes

- **CRITICAL BUG FIX**: Key `_collection_cache` by `user_id` to prevent cross-user data leakage
- **SQL-level filtering**: Add `get_cards_filtered(user_id, filters, limit, offset) -> (cards, total)` to `PostgresCollectionRepository`; Google Sheets path unchanged
- **SQL-level stats**: Replace `get_cached_collection() + filter_collection() + calculate_stats()` with a single `SELECT COUNT, SUM, AVG` SQL query (Postgres path)
- **SQL-level analytics**: Replace Python Counter loops with SQL `GROUP BY` queries for all 5 analytics endpoints (Postgres path)
- **BREAKING: Paginated cards response**: Change `/api/cards` response from `Card[]` to `{ items: Card[], total: number, limit: number, offset: number }`
- **Filter options endpoint**: Add `GET /api/cards/filter-options` returning distinct type/set values from DB
- **Frontend migration**: Update `api/client.ts`, `hooks/useApi.ts`, `Dashboard.tsx`, `CardTable.tsx` for paginated response; remove `limit: 10000`

## Capabilities

### New Capabilities
- `sql-filtering`: SQL-level parameterized filtering and pagination in the Postgres collection repository (Postgres path only; Google Sheets fallback unchanged)

### Modified Capabilities
- `web-api-backend`: `/api/cards` response shape changes to paginated wrapper (BREAKING); new `GET /api/cards/filter-options` endpoint added
- `web-dashboard-ui`: Dashboard consumes paginated cards response; filter options come from dedicated endpoint instead of derived from full card list

## Impact

- `deckdex/storage/repository.py`: new `get_cards_filtered` method on `PostgresCollectionRepository`
- `backend/api/dependencies.py`: `_collection_cache` keyed by `user_id`; `get_cached_collection` fallback kept for Google Sheets
- `backend/api/routes/stats.py`: SQL aggregation path for Postgres, Python fallback for Sheets
- `backend/api/routes/analytics.py`: SQL GROUP BY path for Postgres (all 5 endpoints), Python fallback for Sheets
- `backend/api/routes/cards.py`: use `get_cards_filtered`; return `CardPage` paginated wrapper
- `frontend/src/api/client.ts`: new `CardPage` interface; updated `getCards` return type; new `getFilterOptions`
- `frontend/src/hooks/useApi.ts`: updated `useCards` hook to return `CardPage`
- `frontend/src/pages/Dashboard.tsx`: remove `limit: 10000`; use `filter-options` endpoint for type/set dropdowns
- `frontend/src/components/CardTable.tsx`: accept `serverTotal` prop for pagination controls

## Non-goals

- Virtual scrolling / infinite scroll UI
- Combined analytics endpoint (batching all 5 into 1 request)
- Redis/memcached distributed caching
- Google Sheets performance optimization (Python in-memory path remains unchanged)
- Cursor-based pagination (limit/offset is sufficient for current scale)
