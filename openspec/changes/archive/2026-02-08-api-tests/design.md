## Context

The backend is a FastAPI app (`backend.api.main`) with routes for health, cards, stats, analytics, process, import, settings, and WebSockets. Collection data is provided by `get_cached_collection()` in `backend.api.dependencies`, which reads from Postgres (if `DATABASE_URL` is set) or Google Sheets. There are no tests that hit the HTTP API; existing tests cover deckdex core (config, card_fetcher, spreadsheet, main CLI). Adding API tests requires exercising the app without real I/O.

## Goals / Non-Goals

**Goals:**
- Run API tests with no database or Google Sheets; use mocked `get_cached_collection` (and any other data source) so tests are fast and deterministic.
- Cover at least GET `/api/health`, GET `/api/stats`, and GET `/api/cards` (list, with pagination and filters) so the main collection contract is protected.
- Reuse the existing test runner (`pytest` from repo root) and keep tests in the same `tests/` tree.

**Non-Goals:**
- Testing process, jobs, import, image, or analytics endpoints in this change.
- End-to-end tests against a real DB or Sheets; only unit/integration tests with mocks.
- Changing production API code beyond what is strictly necessary to make it testable (e.g. no mandatory dependency injection if we can patch cleanly).

## Decisions

1. **Use FastAPI TestClient**  
   Use `from fastapi.testclient import TestClient` with `app` from `backend.api.main`. Tests are synchronous `def test_*`; no need for async test client in this scope. If the project does not already depend on `httpx`, add it (TestClient depends on it in current FastAPI/Starlette).

2. **Patch `get_cached_collection` where it is used**  
   Routes import `get_cached_collection` from `backend.api.dependencies`. Patch it in the route modules that are under test so the app uses the mock when handling the request: e.g. `patch('backend.api.routes.stats.get_cached_collection', return_value=...)` and `patch('backend.api.routes.cards.get_cached_collection', return_value=...)`. This avoids touching production code and keeps tests isolated.

3. **Shared fixture data for collection**  
   Define a small list of dicts (e.g. 2–3 cards with name, rarity, type, set_name, price) in the test module or a conftest and reuse it for stats and cards tests. Use at least one card with a parseable price so stats tests can assert total_value / average_price. Include variety (e.g. different rarity/set) so filter tests can assert narrowing.

4. **Location: `tests/test_api.py`**  
   Single module `tests/test_api.py` with classes or functions for health, stats, and cards. Keeps the change small; splitting into `tests/api/` can be a follow-up if the file grows.

5. **Logging during tests**  
   Do not rely on loguru configuration from `main`; if test output is noisy, tests can patch or disable loguru for the test run, or leave as-is and rely on pytest capture. No change to main.py for test-only logging.

## Risks / Trade-offs

- **Patch target drift:** If routes are refactored to get collection via a different path (e.g. a shared service), patch targets may need updating. Mitigation: patch the callable that the route actually uses (e.g. still `get_cached_collection` in dependencies) so only the import path might change.
- **Cache state:** Stats (and possibly cards) use in-memory caches. Tests that change mock data between requests might see cached responses. Mitigation: use a fresh mock return value per test or clear caches in setUp/teardown if the same app instance is reused; or rely on different query params so cache keys differ.
- **Optional httpx:** If `httpx` is not in requirements, add it to the root `requirements.txt` (or the file used when running pytest) so TestClient is available.
