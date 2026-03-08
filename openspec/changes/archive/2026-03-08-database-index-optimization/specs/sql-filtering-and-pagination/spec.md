# Delta Spec: SQL Filtering and Pagination — Index Coverage

**Base spec:** `openspec/specs/sql-filtering-and-pagination/spec.md`

This delta adds index coverage requirements to the existing SQL filtering spec. All other requirements from the base spec remain unchanged.

## Added Requirements

### Database Indexes

The following indexes MUST exist on the `cards` table to support the filtering and analytics queries defined in the base spec:

#### Required indexes (new — added by migration 015)

- **`idx_cards_user_rarity`** — Composite index on `(user_id, rarity)`
  - Supports: `WHERE user_id = :user_id AND LOWER(rarity) = :rarity` in `_build_filter_clauses`
  - Supports: `GROUP BY rarity` dimension in `get_cards_analytics`
  - Index type: B-tree (default)

- **`idx_cards_cmc`** — Single-column index on `(cmc)`
  - Supports: `WHERE cmc IS NOT NULL AND FLOOR(cmc) = :cmc` in `_build_filter_clauses`
  - Supports: `WHERE cmc IS NOT NULL AND cmc >= 7` in `_build_filter_clauses`
  - Supports: `GROUP BY cmc` dimension in `get_cards_analytics`
  - Index type: B-tree (default)

- **`idx_cards_user_set_name`** — Composite index on `(user_id, set_name)`
  - Supports: `WHERE user_id = :user_id AND set_name = :set_name` in `_build_filter_clauses`
  - Supports: `SELECT DISTINCT set_name FROM cards WHERE user_id = :user_id` in `get_filter_options`
  - Index type: B-tree (default)

#### Pre-existing indexes (from earlier migrations — no change)

These indexes already exist and continue to cover other query patterns:

- `idx_cards_user_id ON cards (user_id)` — migration 006
- `idx_cards_name_set_user ON cards (user_id, name, set_id)` — migration 007
- `idx_cards_set_name ON cards (set_name)` — migration 001

### Migration

All three new indexes MUST be created using `IF NOT EXISTS` to ensure idempotency. The migration file is `migrations/015_cards_filter_indexes.sql`.

## No Changes To

- Query SQL in `_build_filter_clauses`, `get_cards_filtered`, `get_cards_stats`, `get_cards_analytics`, `get_filter_options`
- API endpoint signatures or response shapes
- Frontend components or hooks
- Google Sheets path (indexes are PostgreSQL-only; Google Sheets path is unaffected)
