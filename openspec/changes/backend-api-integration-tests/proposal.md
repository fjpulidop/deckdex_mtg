## Why

Multiple backend route areas lack FastAPI TestClient-based HTTP integration tests. After auditing the test suite:

- `tests/test_import_routes.py` — already comprehensive (20+ TestClient tests for all 5 import endpoints)
- `tests/test_external_apis_settings.py` — unit-only logic tests, no HTTP round-trips
- `tests/test_external_apis_routes.py` — HTTP integration tests for `/api/settings/external-apis` already exist
- `tests/test_insights_service.py` — pure computation unit tests; no TestClient tests for the 3 insights routes
- No tests at all for `GET /api/settings/scryfall-credentials` and `PUT /api/settings/scryfall-credentials`

The real gap is two specific areas: (1) HTTP-level integration tests for the three insights routes (`/api/insights/catalog`, `/api/insights/{id}`, `/api/insights/suggestions`), and (2) HTTP-level integration tests for the two scryfall-credentials settings routes. These routes have real error-handling logic (404, 501, 500) that is only exercised via TestClient.

## What Changes

Two new test files are added to `tests/`:

1. `tests/test_insights_routes.py` — TestClient integration tests for all three insights routes. Mocks `get_cached_collection` and the `InsightsService`/`InsightsSuggestionEngine` classes at the route layer. Covers: success path, 404 for unknown insight ID, 501 for not-yet-implemented insight, 500 on unexpected errors, and the catalog endpoint returning the full `INSIGHTS_CATALOG` list.

2. `tests/test_settings_scryfall_credentials_routes.py` — TestClient integration tests for `GET /api/settings/scryfall-credentials` and `PUT /api/settings/scryfall-credentials`. Mocks `get_scryfall_credentials` and `set_scryfall_credentials` from `backend.api.settings_store`. Covers: credentials configured, not configured, store/clear via PUT.

No production code is modified. No existing tests are changed.

## Capabilities

### New Capabilities

- `backend-insights-route-tests`: HTTP integration test coverage for the three insights API routes via FastAPI TestClient
- `backend-scryfall-credentials-route-tests`: HTTP integration test coverage for the two scryfall-credentials settings routes via FastAPI TestClient

### Modified Capabilities

(none)

## Impact

- `tests/test_insights_routes.py` — new file (created)
- `tests/test_settings_scryfall_credentials_routes.py` — new file (created)
- No changes to any production route, service, or model file
- No changes to locale files, `client.ts`, or any frontend file
