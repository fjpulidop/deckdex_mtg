## 1. Fix the migration runner

- [ ] 1.1 In `scripts/setup_db.py`, in `run_migrations()`, add comment-line stripping before the `split(";")` call. Strip lines where `line.strip().startswith("--")` from `sql_content` before splitting.
  - **Modifies:** `scripts/setup_db.py` (lines ~110-119)
  - **Verify:** The remaining `strip_leading_comments()` function still works (it handles leading blank lines in fragments after the split)

## 2. Fix the comment in migration 013

- [ ] 2.1 In `migrations/013_add_is_admin_to_users.sql`, replace the `;` in the comment with `.` — change "Defaults to FALSE; bootstrap" to "Defaults to FALSE. Bootstrap"
  - **Modifies:** `migrations/013_add_is_admin_to_users.sql` (line 2)

## 3. Test

- [ ] 3.1 Add a test in `tests/` that verifies `run_migrations`-style splitting handles semicolons inside `--` comments correctly
  - **Creates:** test case in existing test file or new `tests/test_setup_db.py`
  - **Verify:** Test passes with `pytest tests/test_setup_db.py`
