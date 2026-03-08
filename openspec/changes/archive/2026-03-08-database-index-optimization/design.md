## Context

The `cards` table in PostgreSQL has accumulated indexes incrementally across 14 migrations. The current index landscape for `cards` is:

| Index | Columns | Migration |
|---|---|---|
| `idx_cards_name` | `(name)` | 001 |
| `idx_cards_set_name` | `(set_name)` | 001 |
| `idx_cards_user_id` | `(user_id)` | 006 |
| `idx_cards_name_set_user` | `(user_id, name, set_id)` | 007 |
| `idx_cards_scryfall_id` | `(scryfall_id)` | 004 (global_image_cache) |

The `_build_filter_clauses` method in `deckdex/storage/repository.py` generates `WHERE` clauses for these column patterns:

- `user_id = :user_id` — always present (covered by `idx_cards_user_id`)
- `LOWER(rarity) = :rarity` — **no composite index with user_id**
- `set_name = :set_name` — single-column index exists, but no composite with user_id
- `cmc IS NOT NULL AND FLOOR(cmc) = :cmc` — **no index on cmc**
- `cmc IS NOT NULL AND cmc >= 7` — **no index on cmc**

Without a composite `(user_id, rarity)` index, a rarity filter requires PostgreSQL to either use `idx_cards_user_id` and re-evaluate rarity on every row for that user, or scan the full table. At scale (thousands of cards per user), this degrades the GET /api/cards/ response time and any analytics query that includes a rarity dimension.

Similarly, `cmc` filter operations require a sequential scan because `cmc` has no index at all.

The `set_name` single-column index (`idx_cards_set_name`) can be used by the planner for an unscoped query, but user-scoped queries (`user_id = X AND set_name = Y`) benefit more from a composite index where the leading column is `user_id`.

## Goals / Non-Goals

**Goals:**
- Add a composite index `(user_id, rarity)` to accelerate rarity-filtered card queries
- Add a single-column index on `cmc` to accelerate CMC range and equality queries
- Add a composite index `(user_id, set_name)` to complement the existing single-column index for user-scoped set filtering
- Deliver as a single additive migration (`015_cards_filter_indexes.sql`) using `IF NOT EXISTS` for idempotency
- Add a test verifying the migration SQL is structurally correct and idempotent

**Non-Goals:**
- Modifying any application code in `repository.py` or any route
- Adding partial indexes (e.g., `WHERE rarity = 'mythic'`) — the filter values are user-controlled and variable
- Live query plan verification against a real database in CI
- Indexing `color_identity` or `type_line` (LIKE patterns do not benefit from standard B-tree indexes)
- Covering indexes (PostgreSQL optimizer handles projection efficiently for these low-cardinality columns)

## Decisions

### Decision 1: Composite (user_id, rarity) over individual indexes

**Chosen:** Composite index `(user_id, rarity)`.

**Rationale:** Every query in `_build_filter_clauses` starts with `user_id = :user_id`. A composite index with `user_id` as the leading column lets PostgreSQL seek directly to the user's partition of the index tree and then apply the rarity predicate within that subset. A standalone `idx_cards_rarity` would be less efficient for user-scoped queries because the planner would need to intersect two indexes.

**Alternative considered:** Individual `(rarity)` index — rejected because all production queries are user-scoped. An isolated rarity index would be used only for admin-style unscoped queries which don't exist in the current codebase.

### Decision 2: Single-column index on cmc

**Chosen:** Single-column index `(cmc)`.

**Rationale:** The CMC filter generates two distinct predicates: `FLOOR(cmc) = :cmc` (equality on floored value) and `cmc >= 7` (range). A B-tree index on `cmc` supports the range scan (`cmc >= 7`) efficiently. For the `FLOOR(cmc) = :cmc` predicate, a standard index enables an index range scan (`cmc >= N AND cmc < N+1`), which the planner may choose when selectivity is high enough.

A composite `(user_id, cmc)` was considered but rejected: CMC distribution is low-cardinality (values 0-7+) and user collections are small enough that scanning the user's CMC subset after an index seek on `user_id` is already cheap via `idx_cards_user_id`. The standalone cmc index also benefits any future unscoped analytics queries.

**Alternative considered:** Functional index `(FLOOR(cmc))` — rejected because it would not support the `cmc >= 7` range predicate and adds index maintenance overhead without broader benefit.

### Decision 3: Composite (user_id, set_name) alongside existing (set_name)

**Chosen:** Add composite index `(user_id, set_name)`.

**Rationale:** The existing `idx_cards_set_name ON cards (set_name)` from migration 001 covers unscoped set queries. However, `get_filter_options` and `get_cards_filtered` always include `user_id` in the WHERE clause. The composite index allows the planner to use a single index for both predicates rather than an index intersection. Both indexes coexist without conflict; the planner selects the most selective one for each query shape.

**Alternative considered:** Drop `idx_cards_set_name` and replace with composite — rejected because the old index may still benefit INSERT/UPDATE path on older planner statistics, and `CREATE INDEX IF NOT EXISTS` for the new one costs nothing to add alongside it.

### Decision 4: Single migration file, not individual per-index files

**Chosen:** All three indexes in one migration `015_cards_filter_indexes.sql`.

**Rationale:** The three indexes are logically related (they all serve the filtering and analytics queries). A single migration reduces migration count overhead and is consistent with how migration 006 batched user_id index creation. Each `CREATE INDEX` uses `IF NOT EXISTS` so the migration is idempotent and safe to re-run.

## Risks / Trade-offs

**[Risk] Index creation blocks on large tables** → Mitigation: The production dataset is a personal MTG collection (hundreds to low thousands of cards). Table lock duration for index creation on this size is milliseconds. For larger deployments, `CREATE INDEX CONCURRENTLY` would be used; this is a known escape hatch but not needed for the target use case.

**[Risk] Write amplification on heavily updated tables** → Mitigation: The `cards` table has infrequent writes (import batch, individual edits). Index maintenance overhead on writes is negligible for this access pattern.

**[Risk] Planner may not use new indexes for low row counts** → Mitigation: PostgreSQL's statistics-based planner will prefer sequential scans for very small tables (< ~1000 rows) even with indexes present. This is correct behavior — indexes provide value as collections grow. The `pg_stat_user_indexes` view can confirm index usage at runtime.

**[Risk] FLOOR(cmc) predicate may not use the cmc index on all Postgres versions** → Mitigation: The index on raw `cmc` still benefits the `cmc >= 7` range predicate and `cmc IS NOT NULL` conditions. The FLOOR equality case may require PostgreSQL 14+ for stable function-based plan choices; acceptable given the project's PostgreSQL target.

## Migration Plan

1. Developer runs: `psql "$DATABASE_URL" -f migrations/015_cards_filter_indexes.sql`
2. All three `CREATE INDEX IF NOT EXISTS` statements execute; each takes < 1 second on target dataset sizes
3. PostgreSQL planner automatically uses new indexes on next query execution
4. No application restart required
5. No data migration required

**Rollback:** `DROP INDEX IF EXISTS idx_cards_user_rarity; DROP INDEX IF EXISTS idx_cards_cmc; DROP INDEX IF EXISTS idx_cards_user_set_name;` — zero data loss risk.

## Open Questions

None. This is a purely additive change with no ambiguous requirements.
