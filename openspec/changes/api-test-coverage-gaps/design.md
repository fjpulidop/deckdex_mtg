# Design: Close API Test Coverage Gaps

## Base spec reference

`openspec/specs/api-tests/spec.md`

---

## 1. Current state analysis

### What already exists and is correct

| Test file | Coverage confirmed |
|---|---|
| `tests/test_api.py` — `TestHealth` | `GET /api/health` 200 + service/version/status body verified. **Complete.** |
| `tests/test_api.py` — `TestStats` | Empty collection zeros, non-empty aggregates, rarity filter. |
| `tests/test_api.py` — `TestCardsList` | Empty, non-empty, limit/offset pagination, set_name filter. |
| `tests/test_api_extended.py` — `TestCardsColorFilter` | color_identity filter. |
| `tests/test_decks.py` | All 27 deck CRUD, card management, batch, import, and 501 scenarios. `scope="function"` fixture. **Complete.** |
| `tests/test_insights_routes.py` | All insights scenarios. `scope="function"` fixture. **Complete.** |
| `tests/test_admin_routes.py` | All admin scenarios. `scope="function"` fixture. **Complete.** |

### What is missing or broken

#### 1.1 `conftest.py` — `client` fixture scope

```python
# CURRENT (line 65) — BROKEN
@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_current_user_id] = lambda: 1
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user_id, None)
```

`scope="module"` causes the override set during one test to persist into other modules if pytest collects them in the same process. The teardown `pop` only runs once at module end, not between tests. This is the exact pattern documented as dangerous in `MEMORY.md`.

Fix: change to `scope="function"`.

#### 1.2 `test_api.py` and `test_api_extended.py` — module-level overrides

```python
# test_api.py line 18 — PROBLEMATIC
app.dependency_overrides[get_current_user_id] = lambda: 1
client = TestClient(app)
```

```python
# test_api_extended.py line 17 — PROBLEMATIC
app.dependency_overrides[get_current_user_id] = lambda: 1
client = TestClient(app)
```

These set the override permanently on the shared `app` singleton at import time and never clear it. This means any test module that imports after these runs will have the override already in place. The correct pattern (used in every recent test file) is to set the override in a `setUp`/fixture and pop it in `tearDown`/finalizer.

Fix: move the override into a `setUpClass`/`tearDownClass` pair in each class (since these files use `unittest.TestCase`), or wrap each test method's body with the override active. The cleanest approach for the existing `unittest.TestCase` structure is to use `setUpClass` and `tearDownClass` on each class, which is still per-class isolated rather than module-permanent.

However, since these files use `client = TestClient(app)` as a module-level singleton, the safest minimal fix that does not restructure the entire file is: add a module-level `teardown_module` function that pops the override, and document the known limitation. A better fix is to refactor each class to use `setUpClass`/`tearDownClass` with override install/removal.

**Decision**: Refactor each `unittest.TestCase` class in both files to use `setUpClass` and `tearDownClass` with `app.dependency_overrides` install/removal. The `client` singleton moves to `cls.client`. This is the pattern that prevents cross-module pollution while keeping the unittest structure intact.

#### 1.3 Missing stats filter tests

The spec requires "with query params (rarity, set_name, etc.) → filtered subset only". Currently `test_api.py` has only `rarity` filter. Missing:
- `set_name` filter — `SAMPLE_CARDS` has M10 (2) and LEA (1); `set_name=LEA` should return 1 card (Black Lotus, total_value=25000)
- `search` filter — name substring match; `search=bolt` should return only Lightning Bolt
- Multi-filter combination — `rarity=common&set_name=M10` should return 2 cards

#### 1.4 Missing cards list filter tests

The spec requires "filters → only matching cards (same semantics as stats)". Currently covers set_name and color_identity. Missing:
- `rarity` filter — `rarity=mythic+rare` returns only Black Lotus (1 item)
- `search` filter — `search=bolt` returns only Lightning Bolt (1 item)
- `sort_by` fallback — invalid sort_by value (e.g. `sort_by=invalid`) falls back to `created_at` without error (route validates via `_ALLOWED_SORT_COLUMNS`)
- `sort_dir` fallback — invalid sort_dir (e.g. `sort_dir=sideways`) falls back to `desc` without error

---

## 2. Implementation approach

### 2.1 `conftest.py` — change fixture scope

Single-line change: `scope="module"` → `scope="function"`.

The `sample_cards` fixture is already `scope="function"` (no scope annotation means function). No change needed there.

### 2.2 `test_api.py` — refactor to class-level setup

Replace the module-level:
```python
app.dependency_overrides[get_current_user_id] = lambda: 1
client = TestClient(app)
```

With per-class `setUpClass`/`tearDownClass` methods that install and remove the override. Each class gets its own `cls.client`. The `SAMPLE_CARDS` constant remains module-level (pure data, no side effects).

Stats cache is cleared in existing `setUp`; keep that intact.

Add three new test methods to `TestStats`:
- `test_stats_with_set_name_filter_returns_filtered_subset` — patches both `get_collection_repo` and `get_cached_collection`, calls `GET /api/stats/?set_name=LEA`, asserts `total_cards=1`, `total_value=25000.0`
- `test_stats_with_search_filter_returns_filtered_subset` — `search=bolt`, asserts `total_cards=1`
- `test_stats_with_multi_filter_rarity_and_set_name` — `rarity=common&set_name=M10`, asserts `total_cards=2`

Add three new test methods to `TestCardsList`:
- `test_cards_with_rarity_filter_returns_only_matching` — `rarity=mythic+rare` (URL-encoded), asserts 1 item, name=Black Lotus
- `test_cards_with_search_filter_returns_only_matching` — `search=bolt`, asserts 1 item
- `test_cards_invalid_sort_by_does_not_error` — `sort_by=invalid_column`, asserts 200 (fallback applied silently)
- `test_cards_invalid_sort_dir_does_not_error` — `sort_dir=sideways`, asserts 200

Note: rarity value in `SAMPLE_CARDS` is `"mythic rare"` (with space). The filter in `filter_collection` does case-insensitive substring match. Use `params={"rarity": "mythic rare"}` directly.

### 2.3 `test_api_extended.py` — refactor to class-level setup

Same pattern: replace module-level override with `setUpClass`/`tearDownClass` on each class. The `client` singleton becomes `cls.client`. Each `setUp` that clears the analytics cache remains unchanged.

No new tests needed in this file — all its coverage areas are already complete.

### 2.4 Patch strategy: Google Sheets path

All new stats and cards tests use the Google Sheets path (simpler, no repo mock needed beyond returning `None`):

```python
with (
    patch("backend.api.routes.stats.get_collection_repo", return_value=None),
    patch("backend.api.routes.stats.get_cached_collection", return_value=SAMPLE_CARDS),
):
    response = self.client.get("/api/stats/", params={"rarity": "common", "set_name": "M10"})
```

This is the same pattern used in every existing stats/cards test. It exercises the Python `filter_collection` function in `backend/api/filters.py` directly.

Stats cache must be cleared in `setUp` before each stats test (already done in existing `TestStats.setUp`). New tests inherit this.

### 2.5 Validation errors return HTTP 400

The project overrides FastAPI's default 422 with a custom 400 handler in `backend/api/main.py`:
```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, ...)
```

Any test that checks validation rejection must assert 400, not 422. The new tests do not involve invalid request bodies (they use valid query params), so this does not apply directly — but it is documented here as a constraint for future tests.

---

## 3. File-by-file change summary

### `tests/conftest.py`

- Line 65: `scope="module"` → `scope="function"`

### `tests/test_api.py`

- Remove lines 18–20 (module-level override + `client = TestClient(app)`)
- Add `setUpClass`/`tearDownClass` to `TestHealth`, `TestStats`, `TestCardsList`
- Change `client.get(...)` → `self.client.get(...)` (or `cls.client.get(...)`) throughout
- Add 3 new methods to `TestStats`
- Add 4 new methods to `TestCardsList`

### `tests/test_api_extended.py`

- Remove lines 17–19 (module-level override + `client = TestClient(app)`)
- Add `setUpClass`/`tearDownClass` to all 8 classes
- Change `client.get(...)` → `self.client.get(...)` throughout
- No new test methods needed

---

## 4. What is explicitly not changing

- `tests/test_decks.py` — fully compliant, no changes
- `tests/test_insights_routes.py` — fully compliant, no changes
- `tests/test_admin_routes.py` — fully compliant, no changes
- `tests/test_settings_scryfall_credentials_routes.py` — fully compliant, no changes
- All production code under `backend/`, `deckdex/`, `frontend/` — no changes

---

## 5. Risk assessment

**Low risk overall** — pure test refactoring, no production code.

Potential pitfall: `setUpClass` is a `classmethod`, so it does not participate in `unittest.mock.patch` context manager cleanly. The override install/remove pattern (`app.dependency_overrides[dep] = ...` / `app.dependency_overrides.pop(dep, None)`) does not use `patch` and is safe in classmethods.

Potential pitfall: stats cache is a module-level dict in `backend/api/routes/stats.py`. If two test classes run without clearing it, a cached result from one class's test could bleed into another. The existing `setUp` calls `clear_stats_cache()`, which handles this correctly. The refactor must preserve this `setUp` call.
