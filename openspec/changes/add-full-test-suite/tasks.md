## Layer 1 — Vitest frontend setup

- [ ] 1.1 Install Vitest and Testing Library deps in `frontend/`:
  ```
  npm install -D vitest @vitest/ui jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom
  ```
- [ ] 1.2 Create `frontend/vitest.config.ts` with `environment: 'jsdom'`, `setupFiles: ['./src/test/setup.ts']`, and `include: ['src/**/__tests__/**/*.test.{ts,tsx}']`
- [ ] 1.3 Create `frontend/src/test/setup.ts` that imports `@testing-library/jest-dom/vitest` for DOM matchers
- [ ] 1.4 Add `"test": "vitest run"` and `"test:watch": "vitest"` scripts to `frontend/package.json`

## Layer 1 — Frontend hook tests

- [ ] 2.1 Create `frontend/src/hooks/__tests__/useWebSocket.test.ts`:
  - Stub `WebSocket` globally with a mock class that exposes `onopen`, `onmessage`, `onclose`, `onerror`
  - Assert that `status` starts as `'disconnected'` when `jobId` is `null`
  - Assert that `status` transitions to `'connecting'` when a non-null `jobId` is passed
  - Simulate `onopen`; assert `status` becomes `'connected'`
  - Simulate `onmessage` with a `progress` event; assert `progress` state updates correctly
  - Simulate `onmessage` with a `complete` event; assert `complete` becomes `true` and `summary` is set
  - Simulate `onclose`; assert `status` becomes `'disconnected'`
- [ ] 2.2 Create `frontend/src/api/__tests__/client.test.ts`:
  - Stub global `fetch` with `vi.fn()`
  - Assert that `apiFetch` injects `Authorization: Bearer <token>` when `access_token` is in `sessionStorage`
  - Assert that `apiFetch` throws an error mentioning "Cannot reach the backend" when `fetch` rejects with `Failed to fetch`
  - Assert that a successful fetch returns the `Response` unchanged

## Layer 1 — Frontend component tests

- [ ] 3.1 Create `frontend/src/components/__tests__/CardTable.test.tsx`:
  - Render `<CardTable cards={[]} />` and assert "No cards" or empty state message is shown
  - Render with 3 mock cards; assert 3 `<tr>` rows are present in the table body
  - Click the "Price" column header; assert the rows are re-ordered by price ascending
  - Click the "Price" header again; assert rows are re-ordered descending
- [ ] 3.2 Create `frontend/src/components/__tests__/Filters.test.tsx`:
  - Render `<Filters>` with mocked callback props and empty state
  - Use `userEvent.type` to type into the search input; assert `onSearchChange` is called with the typed value
  - Change the rarity select; assert `onRarityChange` is called with the new value
  - Click the "Clear filters" button; assert `onClearFilters` is called

## Layer 1 — Verification

- [ ] 4.1 Run `npm run test` from `frontend/`; all Vitest tests pass with no failures

## Layer 2 — Additional pytest (backend)

- [ ] 5.1 Create `tests/test_api_extended.py`:
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

- [ ] 6.1 Run `pytest tests/test_api_extended.py -v` from repo root; all new tests pass

## Layer 3 — Playwright setup

- [ ] 7.1 Install Playwright in the frontend package (or a root `package.json`):
  ```
  cd frontend && npm install -D @playwright/test
  npx playwright install chromium
  ```
- [ ] 7.2 Create `playwright.config.ts` at repo root with:
  - `testDir: './e2e'`
  - `use: { baseURL: 'http://localhost:5173' }`
  - `webServer` config pointing to `npm run dev --prefix frontend` (port 5173)
  - Set `timeout` to 10 000 ms and `retries` to 0
- [ ] 7.3 Create `e2e/` directory at repo root
- [ ] 7.4 Create `e2e/smoke.spec.ts` with the following tests:
  - `'dashboard page loads'`: navigate to `/`; assert page title contains "DeckDex" or a heading is visible
  - `'landing page has sign-in or dashboard content'`: navigate to `/`; assert either a sign-in button or a card table element is present (handles both auth and no-auth states)
  - `'navigation links are rendered'`: navigate to `/`; assert at least one `<nav>` or navigation element is present
  - `'no console errors on load'`: navigate to `/`; collect console errors; assert none are uncaught JS errors (network errors for missing backend are acceptable — filter by `page.on('pageerror', ...)`)

## Layer 3 — Verification

- [ ] 8.1 With the frontend dev server running, run `npx playwright test` from repo root; all 4 smoke tests pass (or are skipped if `SKIP_E2E=1`)

## Final check

- [ ] 9.1 Run `pytest tests/` from repo root; all tests (original + extended) pass
- [ ] 9.2 Run `npm run test` from `frontend/`; all Vitest tests pass
- [ ] 9.3 Confirm no production source files were modified (only `package.json` scripts/devDeps and test files were added)
