# Context Bundle: database-index-optimization

Compact reference for the developer implementing this change. Contains the exact patterns and file details needed to execute without re-reading every file.

## Files to Create

| File | Action |
|---|---|
| `migrations/015_cards_filter_indexes.sql` | Create new |
| `tests/test_cards_index_migration.py` | Create new |

## Files for Reference Only (no changes)

| File | Why relevant |
|---|---|
| `deckdex/storage/repository.py` | Contains the query methods that benefit from these indexes |
| `migrations/001_cards_table.sql` | Shows existing indexes and `cards` table DDL |
| `migrations/006_add_user_id.sql` | Shows existing user_id index pattern |
| `migrations/014_price_history.sql` | Most recent migration — establishes file header style |

---

## Migration File Pattern

From `migrations/014_price_history.sql` (exact header style to follow):

```sql
-- DeckDex MTG: <description>
-- Run with: psql $DATABASE_URL -f migrations/015_cards_filter_indexes.sql
```

From `migrations/001_cards_table.sql` (IF NOT EXISTS pattern):

```sql
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards (name);
CREATE INDEX IF NOT EXISTS idx_cards_set_name ON cards (set_name);
```

From `migrations/006_add_user_id.sql` (single-column user_id index):

```sql
CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards (user_id);
```

From `migrations/007_add_quantity_to_cards.sql` (composite index pattern):

```sql
CREATE INDEX IF NOT EXISTS idx_cards_name_set_user ON cards (user_id, name, set_id);
```

---

## Existing Index Inventory on cards Table

All currently defined — do NOT recreate these:

```
idx_cards_name            ON cards (name)                    — migration 001
idx_cards_set_name        ON cards (set_name)                — migration 001
idx_cards_scryfall_id     ON cards (scryfall_id)             — migration 004
idx_cards_user_id         ON cards (user_id)                 — migration 006
idx_cards_name_set_user   ON cards (user_id, name, set_id)   — migration 007
```

---

## Target Index Definitions for Migration 015

```sql
CREATE INDEX IF NOT EXISTS idx_cards_user_rarity
    ON cards (user_id, rarity);

CREATE INDEX IF NOT EXISTS idx_cards_cmc
    ON cards (cmc);

CREATE INDEX IF NOT EXISTS idx_cards_user_set_name
    ON cards (user_id, set_name);
```

---

## Query Patterns Being Accelerated

From `deckdex/storage/repository.py`, method `_build_filter_clauses` (lines 548-632):

```python
# rarity filter — needs idx_cards_user_rarity
conditions.append("LOWER(rarity) = :rarity")
params["rarity"] = rarity.strip().lower()

# set_name filter — needs idx_cards_user_set_name
conditions.append("set_name = :set_name")
params["set_name"] = set_name.strip()

# cmc filter — needs idx_cards_cmc
conditions.append("cmc IS NOT NULL AND FLOOR(cmc) = :cmc")
# OR
conditions.append("cmc IS NOT NULL AND cmc >= 7")
```

Always paired with `user_id = :user_id` as the leading condition.

---

## Test File Pattern

From `tests/test_price_history_repository.py` (no-DB test pattern):

```python
# Tests that use no real database — pure unit tests
from deckdex.storage.repository import PostgresCollectionRepository
# Use MagicMock engine injected into repo._eng
```

For the migration test, no database or mock engine is needed — only `pathlib` and string matching:

```python
import re
from pathlib import Path

MIGRATION_PATH = Path(__file__).parent.parent / "migrations" / "015_cards_filter_indexes.sql"

def test_migration_file_exists():
    assert MIGRATION_PATH.exists()

def test_migration_is_idempotent():
    sql = MIGRATION_PATH.read_text()
    matches = re.findall(r"CREATE INDEX IF NOT EXISTS", sql, re.IGNORECASE)
    assert len(matches) == 3

def test_migration_contains_expected_index_names():
    sql = MIGRATION_PATH.read_text()
    assert "idx_cards_user_rarity" in sql
    assert "idx_cards_cmc" in sql
    assert "idx_cards_user_set_name" in sql
```

---

## cards Table Schema (columns relevant to these indexes)

From `migrations/001_cards_table.sql`:

```sql
CREATE TABLE IF NOT EXISTS cards (
    id BIGSERIAL PRIMARY KEY,
    -- ...
    cmc DOUBLE PRECISION,          -- indexed by idx_cards_cmc
    rarity TEXT,                   -- indexed by idx_cards_user_rarity
    set_name TEXT,                 -- indexed by idx_cards_user_set_name
    -- ...
    user_id BIGINT REFERENCES users(id)  -- leading column in composites, added by migration 006
);
```

`user_id` is `NOT NULL` (enforced by migration 006).

---

## Dependency: No Application Code Changes

No changes are needed to:
- `deckdex/storage/repository.py` — query SQL is unchanged; indexes are transparent
- `backend/api/routes/` — no route changes
- `frontend/` — no frontend changes
- `openspec/specs/sql-filtering-and-pagination/spec.md` — delta spec is in the change directory

The migration file and test file are the complete deliverable.
