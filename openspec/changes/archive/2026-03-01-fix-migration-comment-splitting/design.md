## Context

`scripts/setup_db.py` runs all `.sql` migration files on every container start. The `run_migrations()` function splits file contents by `;` and executes each fragment. This breaks when a `--` comment contains a `;`, because the split doesn't distinguish between statement-terminating semicolons and semicolons inside comments.

Currently affected: `013_add_is_admin_to_users.sql` (the only migration with `;` in a comment). But any future migration with a `;` in a comment would hit the same bug.

## Goals / Non-Goals

**Goals:**
- Make the migration runner ignore `;` inside `--` line comments
- Keep the fix minimal and easy to understand

**Non-Goals:**
- Full SQL parsing (block comments, string literals, dollar-quoted strings)
- Migration tracking table or idempotency framework
- Changing how Python migrations are executed

## Decisions

### Decision 1: Strip comment lines before splitting

**Choice:** Remove all full-line `--` comments from the SQL content before splitting by `;`.

**Alternatives considered:**
- Regex-based splitting that skips `;` in comments: More complex, harder to read, same result for our case
- Character-by-character parser tracking comment state: Overkill for line comments
- Only fix the comment text in `013`: Fixes the symptom, not the root cause

**Rationale:**
- All `--` comments in our migrations are full-line comments (no inline `-- comment` after SQL)
- Stripping comment lines before splitting is a 3-line change
- The existing `strip_leading_comments()` already handles leading comments per fragment — but it runs too late (after the bad split)
- Moving comment removal to before the split is the natural fix

**Implementation:**
```
Before:
  sql_content → split(";") → strip_leading_comments(fragment) → execute

After:
  sql_content → strip_comment_lines() → split(";") → strip_leading_comments(fragment) → execute
```

### Decision 2: Also fix the comment in 013

**Choice:** Replace `;` with `.` in the comment text as a belt-and-suspenders fix.

**Rationale:**
- Defense in depth: even if someone reverts the runner fix, the migration works
- Zero risk (it's a comment)

## Risks / Trade-offs

### Risk: Stripping inline comments after SQL

If a future migration has inline comments like:
```sql
SELECT 1; -- this does something
```

The comment stripping would remove the line entirely, losing the `SELECT 1;`. However, looking at all 13 migrations, **none** use inline comments — all comments are on their own lines. This is acceptable for now. If inline comments appear in the future, the runner can be enhanced then.

### Trade-off: Simplicity vs completeness

We're choosing a simple line-based approach over a full SQL-aware parser. This handles our actual usage pattern (full-line `--` comments) without added complexity.
