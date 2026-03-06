# Tasks: sql-pagination-and-filtering

## Task 1: Fix cache user isolation bug
- [x] In `backend/api/dependencies.py`, change `_collection_cache` from a single dict to `dict[int, dict]` keyed by `user_id`
- [x] Update `get_cached_collection(user_id, force_refresh)` to key cache entries by `user_id` (use `user_id or 0` for anonymous/Sheets mode)
- [x] Update `clear_collection_cache()` to accept optional `user_id` and clear only that user's entry (or all if None)
- [x] Fix `_stats_cache` in `stats.py` to include `user_id` in the cache key tuple
- [x] Fix `_analytics_cache` in `analytics.py` to include `user_id` in the cache key tuple

## Task 2: Add SQL-level filtering to repository
- [x] Add `CardFilters` dataclass to `deckdex/storage/repository.py` with fields: `search`, `rarity`, `type_`, `color_identity`, `set_name`, `price_min`, `price_max`
- [x] Add abstract method `get_cards_filtered` to `CollectionRepository` base class (returns `(List[Dict], int)`)
- [x] Implement `get_cards_filtered` on `PostgresCollectionRepository` using `COUNT(*) OVER() AS total, * FROM cards WHERE ... LIMIT :limit OFFSET :offset`
- [x] Add abstract method `get_stats_aggregated` to `CollectionRepository` base class
- [x] Implement `get_stats_aggregated` on `PostgresCollectionRepository` with `SELECT SUM(quantity), SUM(price_eur * quantity), AVG(price_eur)`
- [x] Add abstract method `get_analytics_grouped` to `CollectionRepository` base class
- [x] Implement `get_analytics_grouped` on `PostgresCollectionRepository` with `SELECT <col>, SUM(quantity) GROUP BY <col>`
- [x] Add abstract method `get_filter_options` to `CollectionRepository` base class
- [x] Implement `get_filter_options` on `PostgresCollectionRepository` with `SELECT DISTINCT type_line` and `SELECT DISTINCT set_name`

## Task 3: SQL-level stats aggregation
- [x] In `backend/api/routes/stats.py`, add a Postgres path: call `repo.get_stats_aggregated(user_id, filters)` when `get_collection_repo()` returns a repo
- [x] Add `user_id` to `_stats_cache` key
- [x] Keep existing `get_cached_collection() + filter_collection() + calculate_stats()` as the Google Sheets fallback

## Task 4: SQL-level analytics aggregation
- [x] In `backend/api/routes/analytics.py`, add a Postgres path for `analytics_rarity`: call `repo.get_analytics_grouped(user_id, filters, 'rarity')`
- [x] Add Postgres path for `analytics_color_identity` (dimension `'color_identity'`; apply `_normalize_color_identity` post-query)
- [x] Add Postgres path for `analytics_cmc` (dimension `'cmc'`; apply bucket logic post-query)
- [x] Add Postgres path for `analytics_sets` (dimension `'set_name'`; apply limit post-query)
- [x] Add Postgres path for the type analytics endpoint (dimension `'type_line'`)
- [x] Add `user_id` to `_analytics_cache` key for all endpoints

## Task 5: Paginated cards API response
- [x] In `backend/api/routes/cards.py`, add a `CardPage` Pydantic model: `items: List[Card]`, `total: int`, `limit: int`, `offset: int`
- [x] Update `GET /api/cards` route to return `CardPage` instead of `List[Card]`
- [x] Use `repo.get_cards_filtered()` when Postgres repo is available; fall back to `get_cached_collection() + filter_collection() + slice` for Sheets, wrapping in `CardPage`
- [x] Add `GET /api/cards/filter-options` endpoint returning `{'types': [...], 'sets': [...]}` with 30s cache keyed by user_id

## Task 6: Frontend API client update
- [x] In `frontend/src/api/client.ts`, add `CardPage` interface: `{ items: Card[]; total: number; limit: number; offset: number }`
- [x] Update `api.getCards()` return type from `Promise<Card[]>` to `Promise<CardPage>`
- [x] Add `api.getFilterOptions()` function calling `GET /api/cards/filter-options`
- [x] Add `FilterOptions` interface: `{ types: string[]; sets: string[] }`

## Task 7: Frontend hooks update
- [x] In `frontend/src/hooks/useApi.ts`, update `useCards` hook to return `CardPage` (or compatible shape for demo mode)
- [x] Add `useFilterOptions` hook using TanStack Query, staleTime 60s

## Task 8: Dashboard update
- [x] In `frontend/src/pages/Dashboard.tsx`, remove `limit: 10000` from `useCards` call
- [x] Add `useFilterOptions()` hook call; use `filterOptions?.types` for type dropdown and `filterOptions?.sets` for set dropdown
- [x] Update `resultCount` prop passed to `Filters` to use `data?.total ?? displayCards.length`
- [x] Update `displayCards` to use `data?.items ?? []`

## Task 9: CardTable serverTotal prop
- [x] In `frontend/src/components/CardTable.tsx`, add optional `serverTotal?: number` prop to `CardTableProps`
- [x] When `serverTotal` is provided, display it in the pagination footer alongside current page info (e.g., "Page 1 of N · X total cards")
