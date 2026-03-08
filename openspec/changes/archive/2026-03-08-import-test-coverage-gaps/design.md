# Design: Import Test Coverage Gaps

## Impact Analysis

### Files Modified

| File | Change |
|---|---|
| `tests/test_import_routes.py` | Change `import_client` fixture scope from `module` → `function`; add one new test function |

### Files Read (Context Only, No Changes)

| File | Purpose |
|---|---|
| `backend/api/services/resolve_service.py` | Contains `SCRYFALL_LOOKUP_CAP = 50` and the cap guard at line 70 |
| `backend/api/routes/import_routes.py` | Import routes; `POST /api/import/resolve` constructs `ResolveService` |
| `tests/conftest.py` | Reference fixture pattern (`scope="function"`) |

No production code changes. No migrations. No frontend changes.

## Design Decision 1: Fixture Scope Change

### Problem

`import_client` at line 66 of `test_import_routes.py` declares `scope="module"`. This means a single `TestClient` instance (with `dependency_overrides` and a mocked limiter) is shared across all 19 test functions in the module. Any test that mutates `app.dependency_overrides` or `app.state` during the module's lifetime can affect subsequent tests.

### Decision: Change to `scope="function"`

Every other fixture in the project uses `scope="function"`:
- `conftest.py` line 65: `@pytest.fixture(scope="function") def client()`
- `tests/test_decks.py` line 45: `@pytest.fixture(scope="function") def deck_client()`
- `tests/test_admin_routes.py` line 34, 45, 66: all `scope="function"`
- `tests/test_insights_routes.py` line 47: `@pytest.fixture(scope="function")`
- `tests/test_settings_scryfall_credentials_routes.py` line 26: `scope="function"`

The original spec (`openspec/specs/import-routes-tests/spec.md`) explicitly says `scope="module"`, but this contradicts the project-wide pattern and the documented pitfall ("scope='module' on pytest fixtures with MagicMock → cross-test pollution"). The spec is wrong on this point; the convention takes precedence.

**Rationale**: `scope="function"` creates and tears down the fixture per test, guaranteeing isolation. The performance cost (19 instead of 1 `TestClient` constructions) is negligible for a unit test suite.

**No behavioral change**: The fixture setup/teardown logic is identical — only the scope string changes. All 19 existing tests continue to pass.

## Design Decision 2: Scryfall Cap Test

### Problem

`ResolveService.resolve()` uses a local `scryfall_lookups` counter, incrementing it before each Scryfall call, and skips Scryfall if `scryfall_lookups >= SCRYFALL_LOOKUP_CAP` (50). This logic is on line 70 of `resolve_service.py`. No test exercises this boundary — the existing tests mock `ResolveService.resolve` at the whole-method level, bypassing the internal cap logic entirely.

### Decision: Test `ResolveService.resolve()` directly (unit test, not HTTP test)

**Option A — HTTP test**: Submit 55 cards to `POST /api/import/resolve` with a mocked `fetcher.autocomplete`. This exercises the full route → service path.

**Option B — Unit test on `ResolveService` directly**: Instantiate `ResolveService` with a mock fetcher, call `service.resolve(55_cards)`, assert `fetcher.autocomplete.call_count <= 50`.

**Chosen: Option B (unit test on `ResolveService`).**

Rationale:
- Option A requires constructing an HTTP request with 55 valid card text lines, patching `load_config`, `CardFetcher`, `get_catalog_repo`, and `get_user_settings_repo` all simultaneously — too much ceremony for a simple boundary condition.
- The cap logic is in `ResolveService`, not in the route. Testing the service unit is more targeted and less brittle to HTTP-layer changes.
- `ResolveService` is already imported directly in route tests via its module path — it is clearly a testable unit.
- The test file is `tests/test_import_routes.py`, which is the natural home for this test given it is part of the import-routes spec deliverables.

### Test Design

```
def test_import_resolve_scryfall_cap_not_exceeded():
    """When >50 unresolved cards are submitted, ResolveService caps Scryfall lookups at 50."""
    from backend.api.services.resolve_service import SCRYFALL_LOOKUP_CAP, ResolveService
    from deckdex.importers.base import ParsedCard

    # Build 55 cards with unique names so none match the catalog (catalog=None)
    # ParsedCard is a TypedDict — construct as plain dicts conforming to the type
    cards: List[ParsedCard] = [
        {"name": f"Fake Card {i}", "quantity": 1, "set_name": None}
        for i in range(55)
    ]

    mock_fetcher = MagicMock()
    mock_fetcher.autocomplete.return_value = []  # No suggestions — all remain not_found

    service = ResolveService(
        catalog_repo=None,
        card_fetcher=mock_fetcher,
        scryfall_enabled=True,
    )
    results = service.resolve(cards)

    assert len(results) == 55
    assert mock_fetcher.autocomplete.call_count == SCRYFALL_LOOKUP_CAP
    # Cards beyond cap have status "not_found" (Scryfall was not consulted)
    not_found_count = sum(1 for r in results if r["status"] == "not_found")
    assert not_found_count == 55  # none had suggestions from empty autocomplete
```

**Key assertions:**
1. `mock_fetcher.autocomplete.call_count == SCRYFALL_LOOKUP_CAP` — exactly 50 calls, no more.
2. `len(results) == 55` — all 55 cards get a result entry (cap does not drop cards).
3. All cards have `status == "not_found"` since `autocomplete` returns `[]`.

**Why plain dicts typed as `ParsedCard`**: `ParsedCard` is a `TypedDict` (see `deckdex/importers/base.py` line 12) — it cannot be instantiated with a constructor call. Plain dicts with the correct keys (`name`, `quantity`, `set_name`) satisfy the TypedDict contract at runtime. `resolve_service.py` line 39 accesses `pc["name"]`, `pc["quantity"]`, `pc.get("set_name")` — all dict operations, no class methods needed.

**Why `catalog_repo=None`**: When catalog is None, the service skips catalog lookup (line 50 checks `if self._catalog is not None`), so all 55 cards fall through to the Scryfall branch.

## Risks and Edge Cases

### Risk 1: `ParsedCard` is not a plain dict
If `ParsedCard` requires construction via a factory function or has mandatory fields not covered by the simple constructor, the test will fail. Mitigation: read the actual `ParsedCard` definition before finalizing — it is in `deckdex/importers/base.py`. The tasks section includes this verification step.

### Risk 2: Fixture scope change breaks a test that relied on shared state
If any existing test was accidentally relying on setup done by a previous test (e.g., a mock set by a `with patch(...)` block that was never restored), changing to `scope="function"` could expose the latent bug. Mitigation: run full test suite before and after and compare results.

### Risk 3: Spec says `scope="module"` — deviation must be documented
The base spec at `openspec/specs/import-routes-tests/spec.md` line 44 explicitly specifies `scope="module"`. This change deliberately contradicts the spec. The delta spec artifact must document this override with its rationale.

## Data Flow (Cap Test)

```
test calls service.resolve(55 ParsedCards)
  └─ for each card (0–49):
       catalog_repo is None → skip catalog
       scryfall_enabled=True AND scryfall_lookups(0–49) < 50 → call fetcher.autocomplete()
       autocomplete returns [] → entry status = "not_found"
  └─ for each card (50–54):
       catalog_repo is None → skip catalog
       scryfall_lookups(50) >= 50 → SKIP Scryfall
       entry status = "not_found"
  └─ returns 55 results, autocomplete called exactly 50 times
```
