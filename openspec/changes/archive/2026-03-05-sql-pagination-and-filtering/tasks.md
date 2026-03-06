# Tasks: SQL-Level Filtering, Aggregation, and Paginated API Responses

## Task 1: Fix collection cache user isolation (CRITICAL BUG)
- [x] In `backend/api/dependencies.py`, change `_collection_cache` from a single dict to `dict[int, dict]` keyed by `user_id`
- [x] Update `get_cached_collection()` to read/write from `_collection_cache[user_id or 0]`
- [x] Update `clear_collection_cache()` to accept optional `user_id` and clear all if not provided

## Task 2: Add SQL-level methods to repository
- [x] Add `get_cards_filtered(user_id, filters, limit, offset) -> tuple[list, int]` to `PostgresCollectionRepository` in `deckdex/storage/repository.py`
  - Build parameterized WHERE clauses from filter dict
  - Use `COUNT(*) OVER() as total_count` window function
  - Handle all filter keys: search, rarity, type_, color_identity, set_name, price_min, price_max, cmc (including 7+ and Unknown buckets)
- [x] Add `get_cards_stats(user_id, filters) -> dict` to `PostgresCollectionRepository`
  - Single SQL aggregation: total_cards (SUM quantity), total_value, average_price
- [x] Add `get_cards_analytics(user_id, filters, dimension, limit) -> list[dict]` to `PostgresCollectionRepository`
  - Support dimensions: rarity, color_identity, set_name, cmc
  - Return list of {label, count} sorted by count DESC
- [x] Add abstract method stubs to `CollectionRepository` ABC

## Task 3: Update stats route to use SQL aggregation (Postgres path)
- [x] In `backend/api/routes/stats.py`, detect Postgres repo and call `repo.get_cards_stats()` instead of loading full collection
- [x] Keep existing Python path for Google Sheets
- [x] Include `user_id` in stats cache key

## Task 4: Update analytics route to use SQL GROUP BY (Postgres path)
- [x] In `backend/api/routes/analytics.py`, detect Postgres repo and call `repo.get_cards_analytics()` for rarity, color-identity, sets, cmc endpoints
- [x] For `type` endpoint: use SQL query + Python primary-type extraction (keep existing `_extract_primary_type`)
- [x] Keep existing Python Counter path for Google Sheets
- [x] Include `user_id` in analytics cache key

## Task 5: Update cards route with paginated response and filter-options endpoint
- [x] Add `CardListResponse` Pydantic model with `items`, `total`, `limit`, `offset` fields
- [x] Change `GET /api/cards/` to return `CardListResponse`
  - Postgres path: use `repo.get_cards_filtered()` directly
  - Sheets path: existing collection + filter + Python slice, wrapped in `CardListResponse`
- [x] Add `GET /api/cards/filter-options` endpoint (registered BEFORE `/{card_id_or_name}`)
  - Add `FilterOptions` Pydantic model with `types` and `sets` fields
  - Postgres path: `SELECT DISTINCT type_line` and `SELECT DISTINCT set_name` from cards
  - Sheets path: derive from cached collection

## Task 6: Update frontend API client types
- [x] Add `CardListResponse` interface to `frontend/src/api/client.ts` (named `CardPage`)
- [x] Change `getCards()` return type from `Promise<Card[]>` to `Promise<CardPage>`
- [x] Add `getFilterOptions()` function returning `Promise<FilterOptions>`

## Task 7: Update frontend hooks
- [x] Update `useCards` in `frontend/src/hooks/useApi.ts` to return `CardPage`
- [x] Update demo mode fallback in `useCards` to wrap in `CardPage` shape
- [x] Add `useFilterOptions()` hook

## Task 8: Update Dashboard page
- [x] In `frontend/src/pages/Dashboard.tsx`, remove `limit: 10000` from `useCards` call
- [x] Add `useFilterOptions()` hook and pass options to `Filters` component
- [x] Update references from `cards` (array) to `cards?.items` (array within paginated response)

## Task 9: Update CardTable component
- [x] In `frontend/src/components/CardTable.tsx`, add optional `serverTotal?: number` prop
- [x] Display total count in the table footer when provided
