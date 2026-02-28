## Layer 1 — Vitest frontend setup

- [x] 1.1 Install Vitest and Testing Library deps in `frontend/`:
  ```
  npm install -D vitest @vitest/ui jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom
  ```
- [x] 1.2 Create `frontend/vitest.config.ts` with `environment: 'jsdom'`, `setupFiles: ['./src/test/setup.ts']`, and `include: ['src/**/__tests__/**/*.test.{ts,tsx}']`
- [x] 1.3 Create `frontend/src/test/setup.ts` that imports `@testing-library/jest-dom/vitest` for DOM matchers
- [x] 1.4 Add `"test": "vitest run"` and `"test:watch": "vitest"` scripts to `frontend/package.json`

## Layer 1 — Frontend hook tests

- [x] 2.1 Create `frontend/src/hooks/__tests__/useWebSocket.test.ts`:
  - Stub `WebSocket` globally with a mock class that exposes `onopen`, `onmessage`, `onclose`, `onerror`
  - Assert that `status` starts as `'disconnected'` when `jobId` is `null`
  - Assert that `status` transitions to `'connecting'` when a non-null `jobId` is passed
  - Simulate `onopen`; assert `status` becomes `'connected'`
  - Simulate `onmessage` with a `progress` event; assert `progress` state updates correctly
  - Simulate `onmessage` with a `complete` event; assert `complete` becomes `true` and `summary` is set
  - Simulate `onclose`; assert `status` becomes `'disconnected'`
- [x] 2.2 Create `frontend/src/api/__tests__/client.test.ts`:
  - Stub global `fetch` with `vi.fn()`
  - Assert that `apiFetch` injects `Authorization: Bearer <token>` when `access_token` is in `sessionStorage`
  - Assert that `apiFetch` throws an error mentioning "Cannot reach the backend" when `fetch` rejects with `Failed to fetch`
  - Assert that a successful fetch returns the `Response` unchanged

## Layer 1 — Frontend component tests

- [x] 3.1 Create `frontend/src/components/__tests__/CardTable.test.tsx`:
  - Render `<CardTable cards={[]} />` and assert "No cards" or empty state message is shown
  - Render with 3 mock cards; assert 3 `<tr>` rows are present in the table body
  - Click the "Price" column header; assert the rows are re-ordered by price ascending
  - Click the "Price" header again; assert rows are re-ordered descending
- [x] 3.2 Create `frontend/src/components/__tests__/Filters.test.tsx`:
  - Render `<Filters>` with mocked callback props and empty state
  - Use `userEvent.type` to type into the search input; assert `onSearchChange` is called with the typed value
  - Change the rarity select; assert `onRarityChange` is called with the new value
  - Click the "Clear filters" button; assert `onClearFilters` is called

## Layer 1 — Verification

- [x] 4.1 Run `npm run test` from `frontend/`; all Vitest tests pass with no failures

## Layer 2 — Additional pytest (backend)

- [x] 5.1 Create `tests/test_api_extended.py`:
  - Import `TestClient(app)` and override `get_current_user_id` the same way as `test_api.py`
  - Add `class TestJobs`:
    - `test_jobs_returns_200`: GET `/api/jobs` returns 200
    - `test_jobs_returns_list`: response JSON is a list
  - Add `class TestAnalyticsRarity`:
    - `test_rarity_returns_200`: GET `/api/analytics/rarity` with mocked `get_cached_collection` (patch `backend.api.routes.analytics.get_cached_collection`) returns 200
    - `test_rarity_returns_list`: response JSON is a list
    - `test_rarity_aggregates_correctly`: with a mock collection of 2 commons and 1 rare, response contains entries with correct counts
  - Add `class TestAnalyticsSets`:
    - `test_sets_returns_200`: GET `/api/analytics/sets` with mocked collection returns 200
    - `test_sets_contains_set_name`: response list entries have a `set_name` key
  - Add `class TestCardsColorFilter`:
    - `test_cards_color_identity_filter`: GET `/api/cards?color_identity=U` with a mocked collection containing cards of different color identities returns only cards matching `U`

## Layer 2 — Verification

- [x] 6.1 Run `pytest tests/test_api_extended.py -v` from repo root; all new tests pass

## Layer 3 — Playwright setup

- [x] 7.1 Install Playwright in the frontend package (or a root `package.json`):
  ```
  cd frontend && npm install -D @playwright/test
  npx playwright install chromium
  ```
- [x] 7.2 Create `frontend/playwright.config.ts` (co-located with node_modules) with:
  - `testDir: './e2e'`
  - `use: { baseURL: 'http://localhost:5173' }`
  - `webServer` config pointing to `npm run dev` (port 5173)
  - Set `timeout` to 10 000 ms and `retries` to 0
- [x] 7.3 Create `frontend/e2e/` directory
- [x] 7.4 Create `frontend/e2e/smoke.spec.ts` with 5 smoke tests:
  - `'landing page loads and has correct title'`
  - `'landing page renders sign-in button or dashboard content'`
  - `'navigation element is rendered on the landing page'`
  - `'no uncaught JS errors on landing page load'`
  - `'login page renders sign-in button'`

## Layer 3 — Verification

- [x] 8.1 Run `npx playwright test --config=playwright.config.ts` from `frontend/`; all 5 smoke tests pass

## Final check

- [x] 9.1 Run `pytest tests/` from repo root; all tests (original + extended) pass — 93 passed
- [x] 9.2 Run `npm run test` from `frontend/`; all Vitest tests pass — 21 passed (4 test files)
- [x] 9.3 Confirm no production source files were modified (only `package.json` scripts/devDeps and test files were added)
