# Tasks: Import Test Coverage Gaps

Two tasks. Both touch only `tests/test_import_routes.py`. No production code changes. No migrations. No frontend changes.

---

## Task 1: Fix `import_client` fixture scope [test]

**File**: `tests/test_import_routes.py`

**What**: Change `@pytest.fixture(scope="module")` to `@pytest.fixture(scope="function")` on the `import_client` fixture (line 66).

**Why**: `scope="module"` violates the project-wide test isolation convention and risks cross-test MagicMock state pollution. All other route test fixtures in the project use `scope="function"`. See design.md for full rationale.

**How**:

At line 66, replace:
```python
@pytest.fixture(scope="module")
def import_client():
```
with:
```python
@pytest.fixture(scope="function")
def import_client():
```

No other changes to the fixture body.

**Acceptance criteria**:
- `@pytest.fixture(scope="module")` no longer appears anywhere in `tests/test_import_routes.py`.
- `pytest tests/test_import_routes.py -v` passes all 19 existing tests with 0 errors and 0 failures.
- No test isolation warnings related to fixture scope appear in the pytest output.

**Dependencies**: None. Can be done first or in parallel with Task 2.

---

## Task 2: Add Scryfall fallback cap test [test]

**File**: `tests/test_import_routes.py`

**What**: Add a new test function `test_import_resolve_scryfall_cap_not_exceeded` that directly unit-tests `ResolveService.resolve()` to confirm the 50-lookup cap is enforced.

**Why**: The `SCRYFALL_LOOKUP_CAP = 50` constant in `backend/api/services/resolve_service.py` has no test coverage. The cap guard at line 70 (`scryfall_lookups < SCRYFALL_LOOKUP_CAP`) will silently regress if the constant or condition is changed.

**How**:

Add this function anywhere in the test file (end of file is fine, after `test_import_external_cards_replace_mode`):

```python
# ===========================================================================
# ResolveService unit tests
# ===========================================================================


def test_import_resolve_scryfall_cap_not_exceeded():
    """ResolveService caps Scryfall autocomplete calls at SCRYFALL_LOOKUP_CAP (50).

    When 55 cards are submitted with no catalog match and Scryfall enabled,
    fetcher.autocomplete must be called at most 50 times. All 55 cards must
    appear in the results (cap does not drop cards).
    """
    from typing import List

    from backend.api.services.resolve_service import SCRYFALL_LOOKUP_CAP, ResolveService
    from deckdex.importers.base import ParsedCard

    # 55 unique fake card names — none will match catalog (catalog=None)
    cards: List[ParsedCard] = [
        {"name": f"Fake Card {i}", "quantity": 1, "set_name": None}
        for i in range(55)
    ]

    mock_fetcher = MagicMock()
    mock_fetcher.autocomplete.return_value = []  # no suggestions; all stay not_found

    service = ResolveService(
        catalog_repo=None,
        card_fetcher=mock_fetcher,
        scryfall_enabled=True,
    )
    results = service.resolve(cards)

    # All 55 cards must have a result — cap does not drop entries
    assert len(results) == 55

    # Scryfall must have been called at most SCRYFALL_LOOKUP_CAP times
    assert mock_fetcher.autocomplete.call_count == SCRYFALL_LOOKUP_CAP

    # All results are not_found (empty autocomplete → no match, no suggestions)
    not_found_count = sum(1 for r in results if r["status"] == "not_found")
    assert not_found_count == 55
```

**Notes**:
- `MagicMock` is already imported at the top of `test_import_routes.py` (`from unittest.mock import MagicMock, patch`).
- `ParsedCard` is a `TypedDict` — construct as plain dict literals, not constructor calls.
- This test does NOT use the `import_client` fixture. It tests `ResolveService` directly and has no HTTP layer involvement.
- No additional imports at module level are needed; use local imports inside the function.

**Acceptance criteria**:
- `pytest tests/test_import_routes.py::test_import_resolve_scryfall_cap_not_exceeded -v` passes.
- The assertion `mock_fetcher.autocomplete.call_count == SCRYFALL_LOOKUP_CAP` holds with the current `SCRYFALL_LOOKUP_CAP = 50` value.
- If `SCRYFALL_LOOKUP_CAP` is lowered to 49, the test fails (proving the test is sensitive to the cap value).
- All 20 tests in `tests/test_import_routes.py` pass after both tasks are applied.

**Dependencies**: None. Can be done in parallel with Task 1. However, verifying the full suite (all 20 tests pass) requires Task 1 to be complete first.

---

## Verification

After both tasks are complete:

```bash
pytest tests/test_import_routes.py -v
```

Expected: 20 passed, 0 failed, 0 errors.

Full suite regression check:

```bash
pytest tests/ -x --tb=short
```

Expected: All tests pass. No new failures introduced by the fixture scope change.
