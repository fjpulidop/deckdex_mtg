# Testing Exploration (2026-03-05)

## Current State Summary

### Backend Tests (tests/)
- 15 test files, 184 test functions total
- ALL use unittest.TestCase style (except test_setup_db which uses plain class)
- conftest.py provides pytest fixtures (client, sample_cards) but NO test file uses them yet
- pyproject.toml has pytest config with strict-markers, slow/integration markers declared but unused

### Frontend Tests (4 files)
- CardTable.test.tsx (6 tests) - rendering, sorting, row click
- Filters.test.tsx (4 tests) - rendering, callbacks, debounce
- useWebSocket.test.ts (5 tests) - connection states, progress messages
- client.test.ts (4 tests) - credentials, error handling, JSON parsing
- Vitest configured with jsdom, @testing-library/jest-dom
- ZERO page-level tests, ZERO context tests

### What IS Tested (Backend)
- Health, Stats, Cards list endpoints (test_api.py, test_api_extended.py)
- Analytics rarity/sets, Jobs list, color_identity filter
- Catalog routes: search, autocomplete, get card, sync, sync status
- External APIs settings: get/put, 503 on no postgres
- CatalogRepository: search, autocomplete, upsert, sync state
- CatalogSyncJob: Scryfall card parsing (basic, DFC, edge cases)
- Config: validation, loading, merging, env overrides, priority
- CardFetcher: search, fuzzy match, OpenAI integration, error handling
- SpreadsheetClient: init, get cards, update cells
- CLI processor: config creation, factory, dry run
- Admin: is_admin_user, require_admin
- ImageStore: put/get/exists/delete, filesystem operations
- Setup DB: SQL splitting logic

### What is NOT Tested (Backend)
- Deck routes (backend/api/routes/decks.py) - ZERO tests
- Import routes (backend/api/routes/import_routes.py) - ZERO route tests
- Process routes (backend/api/routes/process.py) - ZERO tests
- Insights routes (backend/api/routes/insights.py) - ZERO tests
- Auth routes (backend/api/routes/auth.py) - ZERO tests
- WebSocket progress (backend/api/websockets/progress.py) - ZERO tests
- Services: insights_service, card_image_service, importer_service (partial), processor_service, scryfall_service, resolve_service, catalog_service
- Storage: deck_repository, job_repository, repository (main), user_settings_repository
- Importers: moxfield, mtgo, tappedout, generic_csv parsers - ZERO tests
- magic_card_processor end-to-end flow

### What is NOT Tested (Frontend)
- ALL pages: Dashboard, Analytics, DeckBuilder, Import, Landing, Settings, Admin, Demo, Login
- Most components: Navbar, Modals (CardDetail, DeckDetail, CardForm, Confirm, ImportList, JobLog, Settings, Profile, DeckCardPicker), ActiveJobs, CollectionInsights, etc.
- Contexts: ThemeContext, AuthContext, DemoContext, ActiveJobsContext
- Hooks: useCardImage

### Infrastructure Gaps
- No CI/CD (.github/workflows/)
- No E2E tests (no Playwright/Cypress)
- pytest-cov configured but coverage not measured regularly
- All backend tests use unittest style despite pytest being the runner
- SAMPLE_CARDS duplicated across test_api.py, test_api_extended.py, test_catalog_routes.py (conftest exists but unused)
- No test data factories
- Markers (slow, integration) declared but never applied

## Key Patterns/Issues
- Tests inline helper functions to avoid import chain issues (test_admin, test_external_apis_settings)
- Heavy mock nesting in catalog tests (mock_conn setup is verbose)
- TestClient created at module level in multiple files (not via conftest fixture)
- auth override duplicated in every API test file
