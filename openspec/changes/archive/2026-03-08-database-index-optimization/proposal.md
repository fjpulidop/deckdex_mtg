## Why

The `cards` table currently lacks indexes on `(user_id, rarity)` and `cmc`, which are used directly in `WHERE` clauses by `_build_filter_clauses` in `PostgresCollectionRepository`. As collections grow, these unindexed filter paths force PostgreSQL to perform full sequential scans against the user's entire card set, degrading response times for the card list, analytics, and stats endpoints. Adding targeted indexes completes the indexing strategy started in migrations 006 and 007.

## What Changes

- **New migration `015_cards_filter_indexes.sql`**: Adds three indexes:
  - `idx_cards_user_rarity` — composite index on `(user_id, rarity)` for rarity-filtered queries
  - `idx_cards_cmc` — single-column index on `cmc` for CMC range and equality filtering
  - `idx_cards_user_set_name` — composite index on `(user_id, set_name)` to complement the existing single-column `idx_cards_set_name` for user-scoped set filtering
- **Query plan tests**: New pytest file `tests/test_cards_index_migration.py` verifying the migration SQL is syntactically valid and idempotent (`IF NOT EXISTS`).

## Capabilities

### New Capabilities

None. This is a pure infrastructure improvement.

### Modified Capabilities

- `sql-filtering-and-pagination`: The existing spec defines the query behavior but does not specify which indexes must support it. This change adds an index coverage requirement to satisfy the performance expectations implied by the spec.

## Impact

- `migrations/` — one new `.sql` file (`015_cards_filter_indexes.sql`)
- `deckdex/storage/repository.py` — no code changes; indexes are transparent to application code
- `tests/` — one new test file verifying migration properties
- Existing query behavior in `get_cards_filtered`, `get_cards_stats`, `get_cards_analytics`, and `get_filter_options` benefits immediately on next query planner cycle after migration runs

## Non-goals

- No changes to query SQL or application logic
- No changes to frontend or backend API layer
- No query plan analysis using live database connections in tests (no DB required in CI)
- No changes to Google Sheets path (indexes are PostgreSQL-only)
