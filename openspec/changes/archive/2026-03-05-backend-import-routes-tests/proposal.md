## Why

The import routes (`backend/api/routes/import_routes.py`) handle 5 critical endpoints for collection ingestion — file upload, text import, resolve, preview, and from-resolved-cards — but have zero automated test coverage. Any refactor or bug fix is blind, and regressions will only be caught in production.

## What Changes

- Add `tests/test_import_routes.py` with pytest-style tests (no `unittest.TestCase`) for all 5 import endpoints
- Cover happy paths and error paths (400, 501, 413) for each endpoint
- Mock all external dependencies (`get_collection_repo`, `get_current_user_id`, parsers, `ResolveService`, `ImporterService`) so tests need no DB or Scryfall access

## Capabilities

### New Capabilities
- `import-routes-tests`: pytest test module covering all 5 import API endpoints with mocked dependencies

### Modified Capabilities
- `api-tests`: extend the existing test spec to include requirements for import endpoint coverage

## Impact

- New file: `tests/test_import_routes.py`
- No production code changes
- No new dependencies (all mocking via `unittest.mock`)
- CI test run time increases modestly (all tests are in-memory)

## Non-goals

- End-to-end integration tests with a real PostgreSQL database
- Tests for the importer service internals (already partially covered in `test_external_apis_routes.py`)
- Frontend import UI tests
