# Tasks: Close API Test Coverage Gaps

All tasks are test-only. No production code changes. Execute in order — each task builds on the previous.

---

## Task 1 — Fix `conftest.py` fixture scope

**File**: `tests/conftest.py`

**What**: Change the `client` fixture from `scope="module"` to `scope="function"`.

**Context**: The fixture at line 65 uses `scope="module"`, which means the `dependency_overrides` it installs persist for the entire test module and the teardown `pop` only fires once. This is the module-level pollution pattern documented in `MEMORY.md` as a known failure mode.

**Change**:
```python
# Before (line 65):
@pytest.fixture(scope="module")
def client():

# After:
@pytest.fixture(scope="function")
def client():
```

No other changes to `conftest.py`. The `sample_cards` fixture has no scope annotation (defaults to `function`) — leave it unchanged.

**Acceptance criteria**:
- `conftest.py` line 65 reads `@pytest.fixture(scope="function")` (or no scope annotation, which also defaults to function, but explicit is preferred).
- `pytest tests/conftest.py -v` collects with no errors.
- The teardown line `app.dependency_overrides.pop(get_current_user_id, None)` remains in the fixture's `finally`/post-yield block.

**CRITICAL**: Never use `scope="module"` on any fixture that sets `app.dependency_overrides`. This rule applies to all test files.

---

## Task 2 — Refactor `test_api.py` to eliminate module-level dependency override

**File**: `tests/test_api.py`

**What**: Remove the two module-level lines that permanently install the auth override and replace them with `setUpClass`/`tearDownClass` on each `unittest.TestCase` class.

**Context**: Lines 18–20 of `test_api.py` currently read:
```python
app.dependency_overrides[get_current_user_id] = lambda: 1
client = TestClient(app)
```
This permanently mutates the shared `app` singleton. Every subsequent test file that imports will find the override already set, making test isolation impossible.

**Change pattern** — apply to all three classes (`TestHealth`, `TestStats`, `TestCardsList`):

```python
@classmethod
def setUpClass(cls):
    from backend.api.dependencies import get_current_user_id
    from backend.api.main import app
    from fastapi.testclient import TestClient
    app.dependency_overrides[get_current_user_id] = lambda: 1
    cls.client = TestClient(app)

@classmethod
def tearDownClass(cls):
    from backend.api.dependencies import get_current_user_id
    from backend.api.main import app
    app.dependency_overrides.pop(get_current_user_id, None)
```

Remove the module-level:
```python
# DELETE these two lines:
app.dependency_overrides[get_current_user_id] = lambda: 1
client = TestClient(app)
```

Update all `client.get(...)` / `client.post(...)` calls in test methods to `self.client.get(...)` / `self.client.post(...)`.

`TestStats.setUp` calls `clear_stats_cache()` — keep this unchanged, it still runs before each test method.

**Acceptance criteria**:
- No module-level `app.dependency_overrides` assignment in `test_api.py`.
- All three classes have `setUpClass`/`tearDownClass`.
- `pytest tests/test_api.py -v` passes all existing tests (no regressions).
- CRITICAL: `tearDownClass` uses `app.dependency_overrides.pop(get_current_user_id, None)` — never `.clear()`.

---

## Task 3 — Add missing stats filter tests to `test_api.py`

**File**: `tests/test_api.py` — `TestStats` class

**What**: Add three new test methods covering set_name filter, search filter, and multi-filter combination.

**Context**: The spec requires "with query params (rarity, set_name, etc.) → filtered subset only". Only rarity is currently covered. The standard 3-card fixture in `SAMPLE_CARDS` (Lightning Bolt/common/M10, Black Lotus/mythic rare/LEA, Counterspell/common/M10) provides the data needed for all three new tests.

Both `get_collection_repo` and `get_cached_collection` must be patched for each test to force the Google Sheets path. Stats cache must be cleared in `setUp` (already done — these new tests inherit it).

**New test methods**:

```python
def test_stats_with_set_name_filter_returns_filtered_subset(self):
    with (
        patch("backend.api.routes.stats.get_collection_repo", return_value=None),
        patch("backend.api.routes.stats.get_cached_collection", return_value=SAMPLE_CARDS),
    ):
        response = self.client.get("/api/stats/", params={"set_name": "LEA"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data["total_cards"], 1)          # Only Black Lotus
    self.assertAlmostEqual(data["total_value"], 25000.0, places=1)
    self.assertIn("last_updated", data)

def test_stats_with_search_filter_returns_matched_subset(self):
    with (
        patch("backend.api.routes.stats.get_collection_repo", return_value=None),
        patch("backend.api.routes.stats.get_cached_collection", return_value=SAMPLE_CARDS),
    ):
        response = self.client.get("/api/stats/", params={"search": "bolt"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data["total_cards"], 1)          # Only Lightning Bolt

def test_stats_with_multi_filter_rarity_and_set_name(self):
    with (
        patch("backend.api.routes.stats.get_collection_repo", return_value=None),
        patch("backend.api.routes.stats.get_cached_collection", return_value=SAMPLE_CARDS),
    ):
        response = self.client.get("/api/stats/", params={"rarity": "common", "set_name": "M10"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data["total_cards"], 2)          # Lightning Bolt + Counterspell
    self.assertAlmostEqual(data["total_value"], 1.7, places=1)
```

**Acceptance criteria**:
- Three new test methods present in `TestStats`.
- Each new test passes independently when run with `pytest tests/test_api.py::TestStats -v`.
- No new failures in other `TestStats` methods.

---

## Task 4 — Add missing cards list filter and sort tests to `test_api.py`

**File**: `tests/test_api.py` — `TestCardsList` class

**What**: Add four new test methods covering rarity filter, search filter, and sort parameter fallback behaviour.

**Context**: The spec requires cards list filtering by rarity and search (same semantics as stats). Sort fallback behaviour (unknown `sort_by` and `sort_dir` values silently fall back to defaults) is implemented in `backend/api/routes/cards.py` (`_ALLOWED_SORT_COLUMNS` set + `"asc"/"desc"` check) but has no test coverage. These tests exercise the Google Sheets path (patch `get_collection_repo` to return `None`).

Note on rarity value: `SAMPLE_CARDS` has `"mythic rare"` (with space). The `filter_collection` function does case-insensitive equality match on `rarity`. Pass `params={"rarity": "mythic rare"}` directly — `TestClient` URL-encodes spaces automatically.

**New test methods**:

```python
def test_cards_with_rarity_filter_returns_only_matching(self):
    with (
        patch("backend.api.routes.cards.get_collection_repo", return_value=None),
        patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS),
    ):
        response = self.client.get("/api/cards/", params={"rarity": "mythic rare"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(len(data["items"]), 1)
    self.assertEqual(data["total"], 1)
    self.assertEqual(data["items"][0]["name"], "Black Lotus")

def test_cards_with_search_filter_returns_only_matching(self):
    with (
        patch("backend.api.routes.cards.get_collection_repo", return_value=None),
        patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS),
    ):
        response = self.client.get("/api/cards/", params={"search": "bolt"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(len(data["items"]), 1)
    self.assertEqual(data["total"], 1)
    self.assertEqual(data["items"][0]["name"], "Lightning Bolt")

def test_cards_invalid_sort_by_does_not_error(self):
    """Unknown sort_by silently falls back to created_at — must return 200, not 400."""
    with (
        patch("backend.api.routes.cards.get_collection_repo", return_value=None),
        patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS),
    ):
        response = self.client.get("/api/cards/", params={"sort_by": "invalid_column"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertIn("items", data)

def test_cards_invalid_sort_dir_does_not_error(self):
    """Unknown sort_dir silently falls back to desc — must return 200, not 400."""
    with (
        patch("backend.api.routes.cards.get_collection_repo", return_value=None),
        patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS),
    ):
        response = self.client.get("/api/cards/", params={"sort_dir": "sideways"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertIn("items", data)
```

**Acceptance criteria**:
- Four new test methods present in `TestCardsList`.
- Each passes when run with `pytest tests/test_api.py::TestCardsList -v`.
- No new failures in existing `TestCardsList` methods.

---

## Task 5 — Refactor `test_api_extended.py` to eliminate module-level dependency override

**File**: `tests/test_api_extended.py`

**What**: Remove lines 17–19 (module-level `app.dependency_overrides` + `client = TestClient(app)`) and add `setUpClass`/`tearDownClass` to each `unittest.TestCase` class.

**Context**: Same problem as `test_api.py`. The module-level override is installed at import time and never cleaned up. This file has 8 test classes:
`TestJobs`, `TestAnalyticsRarity`, `TestAnalyticsSets`, `TestCardsColorFilter`, `TestAnalyticsColorIdentity`, `TestAnalyticsCmc`, `TestAnalyticsType`, `TestCardPriceHistory`.

**Change pattern** — identical to Task 2, apply to all 8 classes:

```python
@classmethod
def setUpClass(cls):
    from backend.api.dependencies import get_current_user_id
    from backend.api.main import app
    from fastapi.testclient import TestClient
    app.dependency_overrides[get_current_user_id] = lambda: 1
    cls.client = TestClient(app)

@classmethod
def tearDownClass(cls):
    from backend.api.dependencies import get_current_user_id
    from backend.api.main import app
    app.dependency_overrides.pop(get_current_user_id, None)
```

Update all `client.get(...)` calls to `self.client.get(...)`.

`setUp` methods that call `_analytics_mod._analytics_cache.clear()` remain unchanged — they still run before each test method.

**Acceptance criteria**:
- No module-level `app.dependency_overrides` assignment in `test_api_extended.py`.
- All 8 classes have `setUpClass`/`tearDownClass`.
- `pytest tests/test_api_extended.py -v` passes all existing tests with no regressions.
- CRITICAL: `tearDownClass` uses `.pop(key, None)` — never `.clear()`.

---

## Task 6 — Full regression run

**What**: Run the complete test suite to confirm no cross-test pollution after all changes.

**Command**:
```bash
pytest tests/test_api.py tests/test_api_extended.py tests/test_decks.py tests/test_insights_routes.py tests/test_admin_routes.py tests/test_settings_scryfall_credentials_routes.py -v
```

Then run the entire suite:
```bash
pytest tests/ -v
```

**Acceptance criteria**:
- All pre-existing tests continue to pass.
- All new tests added in Tasks 3 and 4 pass.
- Zero test failures.
- No `scope="module"` fixtures remain in any test file that sets `app.dependency_overrides`.
- No module-level `app.dependency_overrides` assignments remain in `test_api.py` or `test_api_extended.py`.

**Note**: The `test_api.py` and `test_api_extended.py` tests use `unittest.TestCase` — pytest collects them fine but they appear as `tests/test_api.py::TestHealth::test_health_returns_200` etc. All should show `PASSED`.
