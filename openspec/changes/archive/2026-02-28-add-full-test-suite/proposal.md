## Why

The project has solid core tests (`tests/test_card_fetcher.py`, `test_config_loader.py`, etc.) and a basic API test suite (`tests/test_api.py`) but **zero frontend tests** and **no end-to-end tests**. Frontend logic (WebSocket state machine, API client, card table rendering, filter wiring) can break silently across refactors. E2E smoke tests are missing entirely, so regressions in the user-visible flow are only caught manually.

This change adds a three-layer test suite that covers the missing gaps without changing production code:

1. **Vitest + Testing Library** — unit/integration tests for the React frontend (hooks, API client, key components)
2. **Additional pytest** — regression tests for backend routes not covered by the existing suite (jobs, analytics, settings, and cards filters regression)
3. **Playwright** — E2E smoke tests that verify navigation, the card table, filters, and the card detail modal in a browser

## What Changes

- **Frontend (Layer 1):** Install `vitest`, `@vitest/ui`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, and `@testing-library/jest-dom`. Add `vitest.config.ts` and a `test` script to `package.json`. Write tests for `useWebSocket`, `useCards`, `useStats`, `client.ts` (fetch mocking), `CardTable`, and `Filters`.
- **Backend (Layer 2):** Add `tests/test_api_extended.py` covering GET `/api/jobs`, GET `/api/analytics` (mocked), and POST `/api/cards` CRUD paths. Existing `test_api.py` stays untouched.
- **E2E (Layer 3):** Install Playwright (`@playwright/test`), add `playwright.config.ts` at repo root, write smoke tests in `e2e/` for: landing/dashboard navigation, card table loading, filter application, and card detail modal open/close.

## Capabilities

### New Capabilities

- **frontend-unit-tests:** The project SHALL have a Vitest-based unit/integration test suite for the React frontend that tests hooks and components in isolation without a real backend.
- **backend-regression-tests:** The project SHALL have additional pytest coverage for jobs and analytics API routes using mocked data, so those contracts are regression-tested.
- **e2e-smoke-tests:** The project SHALL have Playwright E2E smoke tests that boot the full stack (or use a mock server) and verify core user flows in a browser.

### Modified Capabilities

None.

## Impact

- **Frontend:** New `devDependencies` in `frontend/package.json`; new `vitest.config.ts`; new `frontend/src/**/__tests__/` test files. No production code changes.
- **Backend:** New `tests/test_api_extended.py`; no production code changes.
- **E2E:** New `playwright.config.ts`, new `e2e/` directory; new `@playwright/test` devDependency in root `package.json` (created if absent) or `frontend/package.json`.
- **CI:** `npm run test` in `frontend/`, `pytest tests/` from repo root, and `npx playwright test` all run independently.
