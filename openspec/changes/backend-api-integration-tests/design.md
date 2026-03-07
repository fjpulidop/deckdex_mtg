## Context

The DeckDex test suite covers backend routes with varying depth. After reading the actual test files:

- `tests/test_import_routes.py` — fully covers all 5 import endpoints via TestClient (20+ tests). No work needed.
- `tests/test_external_apis_routes.py` — fully covers `GET /api/settings/external-apis` and `PUT /api/settings/external-apis` via TestClient. No work needed.
- `tests/test_insights_service.py` — covers `InsightsService` and `InsightsSuggestionEngine` as pure Python (no HTTP). The three route handlers in `backend/api/routes/insights.py` are untested at the HTTP level.
- No test file covers `GET /api/settings/scryfall-credentials` or `PUT /api/settings/scryfall-credentials` from `backend/api/routes/settings_routes.py`.

The insights routes call `get_cached_collection` (a module-level function, not a FastAPI Depends) and then construct `InsightsService` / `InsightsSuggestionEngine` inline. The scryfall-credentials routes call module-level `get_scryfall_credentials` and `set_scryfall_credentials` from `backend.api.settings_store`.

Both patterns follow the same approach used in `test_import_routes.py`: patch module-level callables with `unittest.mock.patch`, override `get_current_user_id` via `app.dependency_overrides`.

## Goals / Non-Goals

**Goals:**
- HTTP integration tests for all three insights routes: `GET /api/insights/catalog`, `POST /api/insights/{insight_id}`, `GET /api/insights/suggestions`
- HTTP integration tests for both scryfall-credentials routes: `GET /api/settings/scryfall-credentials`, `PUT /api/settings/scryfall-credentials`
- Cover success paths, error paths (404, 501, 500, 400), and authentication override pattern
- Match fixture scope (`scope="function"`) and mock conventions from existing test files

**Non-Goals:**
- No changes to any production code (routes, services, dependencies)
- No additional coverage of import routes (already comprehensive)
- No additional coverage of external-apis settings routes (already comprehensive)
- No frontend changes, no locale file changes, no `client.ts` changes
- No end-to-end DB integration; all repos and services are mocked

## Decisions

### Decision 1: Patch `get_cached_collection` at the route module level

The insights routes call `get_cached_collection` imported directly into `backend.api.routes.insights`:

```python
from ..dependencies import get_cached_collection, get_current_user_id
```

The correct patch target is `backend.api.routes.insights.get_cached_collection` — this is where the name is bound at call time. Patching `backend.api.dependencies.get_cached_collection` would not intercept calls already resolved through the route module's namespace.

Alternative considered: override `get_collection_repo` to return a mock repo. Rejected — `get_cached_collection` has TTL caching logic that would complicate setup and could produce cross-test contamination from the module-level `_collection_cache` dict.

### Decision 2: Patch `InsightsService` and `InsightsSuggestionEngine` at the route module level

The `execute_insight` and `insights_suggestions` routes construct service objects inline. Patching `backend.api.routes.insights.InsightsService` and `backend.api.routes.insights.InsightsSuggestionEngine` allows full control of return values without running real computation. This avoids duplicating the service unit tests that already exist in `test_insights_service.py`.

For `GET /api/insights/catalog`, no patch is needed — the route returns the module-level `INSIGHTS_CATALOG` constant directly.

### Decision 3: Patch `get_scryfall_credentials` / `set_scryfall_credentials` at the settings_routes module level

These are imported into `backend.api.routes.settings_routes` from `backend.api.settings_store`. The correct patch target is `backend.api.routes.settings_routes.get_scryfall_credentials` and `backend.api.routes.settings_routes.set_scryfall_credentials`.

### Decision 4: Fixture scope is `scope="function"` for all fixtures

Per project convention (`.claude/rules/testing.md` and `CLAUDE.md`), all pytest fixtures with mocked deps MUST use `scope="function"`. Module-scoped mocks cause cross-test pollution. This matches `tests/test_decks.py` pattern.

### Decision 5: Rate limiter patching for insights routes

The insights routes do not use `@limiter.limit()` decorators, so no rate-limiter patching is required. The scryfall-credentials routes also do not use rate limiting. This simplifies fixtures compared to `test_import_routes.py`.

### Decision 6: Auth override via `app.dependency_overrides`

`get_current_user_id` is a FastAPI `Depends`-based dependency on all insights and settings routes. Override via `app.dependency_overrides[get_current_user_id] = lambda: 1` in each fixture, cleaned up in teardown (via yield or tearDown). This is the established pattern across all existing route test files.

## Risks / Trade-offs

**[Risk] Module-level `_collection_cache` state leaks across tests** → Mitigation: patch `get_cached_collection` so the real cache is never populated during tests. Each test controls its own return value.

**[Risk] `INSIGHTS_CATALOG` is a real list imported from `backend.api.services.insights_service`** → This is acceptable for the catalog test; the list is a pure constant with no external deps. Importing it in tests is safe and verifies the route actually returns the real catalog.

**[Risk] `settings_store` may access the filesystem** → The `get_scryfall_credentials` / `set_scryfall_credentials` functions read/write a JSON sidecar file. Patching them at the route module level ensures no real filesystem access during tests.

## Migration Plan

No migration required. This change is additive — two new test files only.

After implementation, run `pytest tests/test_insights_routes.py tests/test_settings_scryfall_credentials_routes.py -v` to verify all new tests pass, then `pytest tests/` to verify no regressions.

## Open Questions

None. All required information was obtained from reading the production route files and existing test patterns.
