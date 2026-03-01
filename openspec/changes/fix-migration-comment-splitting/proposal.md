## Why

The migration runner in `scripts/setup_db.py` splits SQL files by `;` to extract individual statements. This naive split doesn't account for semicolons inside SQL comments (`-- ...`). Migration `013_add_is_admin_to_users.sql` has a comment containing `;`:

```sql
-- Defaults to FALSE; bootstrap admin via DECKDEX_ADMIN_EMAIL env var
```

The `;` inside the comment causes the runner to split mid-comment, producing a fragment starting with `bootstrap admin via...` which PostgreSQL rejects as a syntax error. This breaks `docker compose up --build` on every restart.

## What Changes

1. Fix the SQL statement splitter in `setup_db.py` to strip full-line `--` comments before splitting by `;`
2. Fix the offending comment in `013_add_is_admin_to_users.sql` as a belt-and-suspenders measure

## Capabilities

### Modified Capabilities
- None (this is infrastructure/tooling, not a user-facing capability)

## Impact

**Affected code:**
- `scripts/setup_db.py` — `run_migrations()` function (the split logic)
- `migrations/013_add_is_admin_to_users.sql` — comment text

**Risk:** Very low. The change only affects how comment lines are handled before splitting. All existing migrations with comments-on-their-own-lines and no semicolons in comments are unaffected.

## Non-goals

- Adding a full SQL parser (overkill for `--` line comments)
- Handling block comments (`/* ... */`) — not used in any migration
- Adding a migration tracking table (separate concern)
- Handling semicolons inside string literals (not present in migrations)
