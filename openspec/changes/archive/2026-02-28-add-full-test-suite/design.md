## Context

The project has a FastAPI backend (`backend/api/main.py`, routes under `backend/api/routes/`), a React 19 + Vite 7 frontend (`frontend/`), and an existing pytest suite (`tests/`). The frontend has no test infrastructure at all. The backend test suite covers health, stats, and cards but leaves jobs, analytics, settings, and CRUD paths untested. No E2E tests exist.

## Goals / Non-Goals

**Goals:**
- Layer 1 (Vitest): Set up Vitest + Testing Library in the frontend. Test `useWebSocket` hook logic, `useCards`/`useStats` query hooks (mocked fetch), `client.ts` fetch helper, `CardTable` render and sort, and `Filters` input wiring.
- Layer 2 (pytest extended): Add `tests/test_api_extended.py` covering GET `/api/jobs` (empty and with a mock job), GET `/api/analytics` (mocked collection), and at least one cards filter regression beyond what `test_api.py` already covers.
- Layer 3 (Playwright): Add smoke E2E tests for: dashboard page loads and card table is visible; filter by search updates URL/state; card detail modal opens on row click and closes on Escape; navigation links work.

**Non-Goals:**
- Full component snapshot testing or visual regression.
- E2E tests that require a real database or Google Sheets (use test fixtures or MSW).
- Testing every backend route; this change is additive, not exhaustive.
- Changing production code; only test files and config are added.

## Decisions

### Layer 1 — Vitest + Testing Library

1. **Test runner: Vitest 3 with jsdom environment**
   Vitest integrates natively with Vite 7 (same config pipeline). Use `environment: 'jsdom'` so DOM APIs are available. Add `setupFiles` that imports `@testing-library/jest-dom/vitest` for DOM matchers.

2. **Config location: `frontend/vitest.config.ts`**
   Separate from `vite.config.ts` so build and test configs don't interfere. Import from `vitest/config` (not `vite`) and reference the same React plugin.

3. **Test file locations: `frontend/src/**/__tests__/*.test.ts(x)`**
   Co-locate tests with source. e.g. `hooks/__tests__/useWebSocket.test.ts`, `components/__tests__/CardTable.test.tsx`.

4. **Mock strategy for hooks**
   - `useWebSocket`: use `vi.useFakeTimers()` and a manual `WebSocket` mock via `vi.stubGlobal('WebSocket', MockWS)`. Test that state transitions from `connecting` → `connected` → `disconnected` correctly on `onopen`/`onclose`.
   - `useCards` / `useStats`: wrap in `QueryClientProvider` with a fresh `QueryClient`. Mock `fetch` globally with `vi.stubGlobal('fetch', vi.fn())` returning a resolved `Response`.
   - `client.ts` `apiFetch`: mock `fetch` to test auth header injection and network error transformation.
   - `CardTable`: render with `cards` prop containing 2–3 mock cards; assert rows count, sort click changes order.
   - `Filters`: render with callback props; simulate input; assert callbacks fire.

5. **`@testing-library/user-event` for interaction**
   Use `userEvent.setup()` and `await user.type(...)` / `await user.click(...)` for realistic DOM interaction simulation.

### Layer 2 — Additional pytest

6. **New file: `tests/test_api_extended.py`**
   Import same `client` and `app` from `test_api.py` style. Override `get_current_user_id` the same way. Add:
   - `TestJobs`: GET `/api/jobs` returns 200 and a list (empty is fine; no mock needed since jobs are in-memory).
   - `TestAnalytics`: GET `/api/analytics` with mocked `get_cached_collection` returns 200 and expected shape (at minimum `rarity_breakdown` or a dict key).
   - `TestCardsRegression`: filter by `color_identity` with mocked collection; assert narrowing works.

7. **Patch targets for analytics**
   `backend.api.routes.analytics` imports collection via `get_cached_collection` from `backend.api.dependencies`. Patch `backend.api.routes.analytics.get_cached_collection`.

### Layer 3 — Playwright E2E

8. **Config: `playwright.config.ts` at repo root**
   Use `webServer` to start the frontend (`npm run dev --prefix frontend`) and a backend stub or the real backend. For portability, use a `baseURL` of `http://localhost:5173`. Tests should work against a running dev stack; skip in CI if stack is not available (via `SKIP_E2E` env var).

9. **Test location: `e2e/` at repo root**
   Keeps E2E separate from unit tests. Files: `e2e/smoke.spec.ts`.

10. **Smoke tests (4 scenarios)**
    a. Dashboard: navigate to `/`, assert `<table>` or `"No cards"` text is present.
    b. Filter search: type into search input, assert URL includes `?search=` or component re-renders.
    c. Card detail: if cards exist, click first row, assert modal opens (look for a heading with card name).
    d. Navigation: click a nav link (e.g. "Collection"), assert URL changes.
    Since the dev stack may have auth (Google OAuth), tests will target the landing page and unauthenticated routes, or use a test user seeded by a fixture script. For now, target pages that work without auth.

11. **Playwright install**
    Add `@playwright/test` to `devDependencies` in `frontend/package.json` (simplest: one `package.json` manages both frontend and E2E deps). Run `npx playwright install chromium` once.

## Risks / Trade-offs

- **Vitest / jsdom limitations:** `useWebSocket` uses `window.location` to build the WS URL; in jsdom `window.location.protocol` is `http:`, which is fine — tests can assert the constructed URL or just state transitions.
- **Playwright requires running stack:** E2E tests are skipped in offline/CI environments without the dev server. This is acceptable for a smoke test suite; full CI integration is a follow-up.
- **Analytics endpoint shape:** The analytics route aggregates cards data; the exact response shape should be confirmed from `backend/api/routes/analytics.py` before writing assertions. Test should assert HTTP 200 and at least one top-level key rather than exact values.
- **Job state is in-memory:** GET `/api/jobs` returns whatever is in the server's memory. Test should assert 200 and that the response is a list, not assert specific job contents.
