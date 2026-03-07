## Why

The analytics API has five endpoints (`/rarity`, `/color-identity`, `/cmc`, `/sets`, `/type`) but only two have tests. Three endpoints have zero test coverage, the price history endpoint (`GET /api/cards/{id}/price-history`) has none, and the `/type` endpoint violates the project's core architecture convention by reaching into private repository methods (`_build_filter_clauses`, `_get_engine`) and executing raw SQL directly from the route layer. This is a correctness and maintainability risk that must be resolved before the analytics feature is considered stable.

## What Changes

- **Fix `/api/analytics/type` architecture violation**: Move the hybrid SQL+Python type aggregation into a new `get_type_line_data` repository method. Route delegates to the repository — no direct SQLAlchemy or raw SQL in route code.
- **Add test coverage for `/api/analytics/color-identity`**: Status code, response shape, and aggregation correctness (Sheets path).
- **Add test coverage for `/api/analytics/cmc`**: Status code, response shape, CMC bucket ordering (0 < 1 < … < 7+ < Unknown), and edge cases (null CMC → "Unknown", cmc ≥ 7 → "7+").
- **Add test coverage for `/api/analytics/type`**: Status code, response shape, type extraction logic (priority order, em-dash split, "Other" fallback).
- **Add test coverage for `GET /api/cards/{id}/price-history`**: Postgres-path happy path (mock repo), Sheets path returns 501, card-not-found returns 404.
- **No frontend changes.** No migration changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `analytics-dashboard`: The `/api/analytics/type` endpoint implementation changes to use a proper repository method instead of reaching into private internals. No external contract change — same URL, same request/response schema. The spec gains an implementation note requiring that the endpoint use a public repository method.

## Impact

- `backend/api/routes/analytics.py` — rewrite `analytics_type` to call a new public repo method.
- `deckdex/storage/repository.py` — add `get_type_line_data(user_id, filters)` to `CollectionRepository` ABC (default returns `[]`) and implement it in `PostgresCollectionRepository` (lightweight SELECT type_line, quantity query with filter clause delegation to `_build_filter_clauses`).
- `tests/test_api_extended.py` — add test classes for `color-identity`, `cmc`, `type`, and `price-history`.

## Non-goals

- No cache eviction/LRU changes to `_analytics_cache`.
- No Postgres integration tests (no live DB in CI).
- No frontend changes.
- No changes to other analytics endpoints.
