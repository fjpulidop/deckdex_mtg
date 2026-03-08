# Delta Spec: Import Routes Tests — Coverage Gaps

Base spec: `openspec/specs/import-routes-tests/spec.md`

This delta supersedes two items in the base spec.

---

## Override: Fixture Scope

**Base spec says** (line 44):
> One `@pytest.fixture(scope="module")` for the shared `TestClient` with `get_current_user_id` overridden

**This delta overrides to**:
> The `import_client` fixture MUST use `scope="function"`, not `scope="module"`.

**Rationale**: `scope="module"` violates the project-wide test isolation convention. All other route test fixtures (`conftest.py`, `test_decks.py`, `test_admin_routes.py`, `test_insights_routes.py`, `test_settings_scryfall_credentials_routes.py`) use `scope="function"`. Module-scoped mocks with `MagicMock` can cause cross-test state pollution, making failures non-deterministic. The project MEMORY explicitly flags this as a "pattern that always breaks."

---

## Addition: Scryfall Fallback Cap Validation

**New test requirement** (adds to `POST /api/import/resolve` section):

- **Scryfall cap enforcement**: When `ResolveService` is configured with `scryfall_enabled=True` and receives more than 50 unresolved cards (i.e., cards not matched by catalog), it MUST call `fetcher.autocomplete` at most `SCRYFALL_LOOKUP_CAP` (50) times. Cards beyond the cap receive `status="not_found"` and are included in the results list. The total result count equals the total input count (no cards are dropped).

### Test location

`tests/test_import_routes.py` — unit test on `ResolveService` directly (not via HTTP).

### Test specification

Function name: `test_import_resolve_scryfall_cap_not_exceeded`

Setup:
- 55 `ParsedCard` dicts with unique names (`"Fake Card 0"` through `"Fake Card 54"`)
- `catalog_repo=None` (forces all cards to Scryfall branch)
- `mock_fetcher.autocomplete.return_value = []` (no suggestions returned)
- `scryfall_enabled=True`

Assertions:
1. `mock_fetcher.autocomplete.call_count == SCRYFALL_LOOKUP_CAP` (exactly 50, not 55)
2. `len(results) == 55` (all input cards produce a result)
3. All 55 results have `status == "not_found"` (empty autocomplete → not_found)

No HTTP request is made. This tests `ResolveService.resolve()` in isolation.
