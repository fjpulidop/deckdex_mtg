## 1. Migration [core]

- [ ] 1.1 Create `migrations/015_cards_filter_indexes.sql` with the composite index on `(user_id, rarity)`, single-column index on `(cmc)`, and composite index on `(user_id, set_name)`. All three `CREATE INDEX` statements must use `IF NOT EXISTS`. Header comment must follow the pattern from existing migrations (e.g. `-- DeckDex MTG: ...` and `-- Run with: psql $DATABASE_URL -f migrations/015_cards_filter_indexes.sql`). Done when: file exists, parses as valid SQL (no syntax errors), and contains exactly three `CREATE INDEX IF NOT EXISTS` statements.

## 2. Tests [test]

- [ ] 2.1 Create `tests/test_cards_index_migration.py`. The file must verify: (a) `migrations/015_cards_filter_indexes.sql` exists at the expected path, (b) the file content contains `IF NOT EXISTS` on each index definition (three occurrences), (c) the index names `idx_cards_user_rarity`, `idx_cards_cmc`, and `idx_cards_user_set_name` all appear in the SQL. Use only stdlib (`pathlib`, `re`) — no database connection required. Done when: `pytest tests/test_cards_index_migration.py` passes with no errors.

- [ ] 2.2 Verify all pre-existing tests still pass: `pytest tests/`. No regressions from the new migration file. Done when: full test suite passes (no new failures).

## 3. Context Bundle [core]

- [ ] 3.1 After completing tasks 1.1 and 2.1, confirm the migration README at `migrations/README.md` does not need updating (the README states "run `for f in migrations/*.sql; do psql ...`" which picks up new files automatically). No update is needed. Done when: README is confirmed sufficient as-is and no documentation gap exists.
