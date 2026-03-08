# Proposal: Close API Test Coverage Gaps

## What

Fill three coverage gaps in the existing API test suite without touching any production code:

1. **`conftest.py` fixture scoping** — The shared `client` fixture uses `scope="module"`, which causes cross-test pollution when `dependency_overrides` are set module-level (as in `test_api.py` and `test_api_extended.py`). The fixture must be changed to `scope="function"` and the two older test files that set module-level overrides must be audited.

2. **Stats endpoint — additional filtering scenarios** — `test_api.py` covers empty, non-empty, and rarity-filtered stats. Missing coverage: set_name filter, search filter, and the multi-filter combination (rarity + set_name). These are pure in-memory (Google Sheets) path tests; no DB mock needed beyond returning `None` from `get_collection_repo`.

3. **Cards list — additional edge cases** — `test_api.py` covers empty, non-empty, limit/offset pagination, set_name filter, and color_identity filter. Missing coverage: rarity filter, search (name substring), and sort parameter behaviour (unknown sort_by falls back to `created_at`; invalid sort_dir falls back to `desc`).

## Why

The spec at `openspec/specs/api-tests/spec.md` requires stats filtering with arbitrary query params and cards list filtering by rarity and search. These cases are listed in the spec but not implemented. The `scope="module"` fixture is a known cross-test pollution pattern identified across multiple sprints (documented in `MEMORY.md`). Fixing it now prevents false test passes when test order changes.

The deck CRUD and health endpoint requirements are **already fully covered**:
- Health: `TestHealth` in `tests/test_api.py` covers 200 + body fields + exact values.
- Deck CRUD + 404s: all scenarios in `tests/test_decks.py` (27 tests, `scope="function"` fixture).
- Deck card management: fully covered in `tests/test_decks.py`.

## Scope

- **Files changed**: `tests/conftest.py`, `tests/test_api.py`, `tests/test_api_extended.py`
- **New tests added** (inside existing files, not new files): stats set_name/search/multi-filter; cards rarity/search/sort-fallback
- **No production code changes** — purely test additions and a fixture scope fix
- **No new test files** — all additions go into the existing files to keep the test surface coherent

## Success Criteria

1. `pytest tests/test_api.py tests/test_api_extended.py tests/test_decks.py tests/conftest.py -v` passes with zero failures.
2. `conftest.py` `client` fixture uses `scope="function"`.
3. `test_api.py` and `test_api_extended.py` do not set `app.dependency_overrides` at module level (moved into per-test setUp or per-test patches).
4. New stats tests verify set_name filter, search filter, and multi-filter combination.
5. New cards tests verify rarity filter, search filter, and sort_by/sort_dir fallback behaviour.
