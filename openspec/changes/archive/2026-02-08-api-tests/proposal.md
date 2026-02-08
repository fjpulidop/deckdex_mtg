## Why

The backend API (health, stats, cards) has no automated tests. Changes to routes, filters, or dependencies can break the contract without detection. Adding tests for at least health, stats, and cards will protect the API surface and make refactors safer.

## What Changes

- **New test suite:** Automated tests for the FastAPI backend that exercise GET `/api/health`, GET `/api/stats`, and GET `/api/cards` (and related query parameters) without requiring a real database or Google Sheets.
- **Test harness:** Use FastAPI `TestClient` (or equivalent) with mocked collection data so tests run in CI and locally without external services.
- **Scope (this change):** Health (200 + body), stats (empty and non-empty collection, optional filters), cards list (empty, pagination, filters). No tests for process/jobs/import/image in this change.

## Capabilities

### New Capabilities

- **api-tests:** The project SHALL include an automated test suite for the backend API that verifies the health endpoint and the collection statistics and cards list endpoints with mocked collection data, so that the API contract can be validated without a live database or Google Sheets.

### Modified Capabilities

None.

## Impact

- **Tests:** New test module(s) under `tests/` (e.g. `test_api.py` or `tests/api/`) that depend on FastAPI TestClient; optional dependency `httpx` if required by TestClient.
- **CI:** Existing `pytest` runs will include the new tests; no new CI jobs required.
- **Backend code:** No change to production routes; only test code and possibly test-time dependency injection or mocking of `get_cached_collection` (and related dependencies as needed).
