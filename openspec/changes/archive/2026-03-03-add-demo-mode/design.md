## Context

The Dashboard (`/dashboard`) is gated behind `<ProtectedRoute>`, which redirects unauthenticated users to `/login`. All data flows through `useCards`, `useInsightsCatalog`, and `useInsightsSuggestions` hooks in `useApi.ts`, which call the FastAPI backend. There is no existing mechanism to serve the Dashboard UI without a valid JWT cookie.

The Hero section of the landing page renders a gradient placeholder where a real dashboard screenshot should appear. There is currently no tooling to generate this screenshot.

## Goals / Non-Goals

**Goals:**
- Public `/demo` route renders the real Dashboard component with mock data (no backend calls, no auth).
- `DemoContext` intercepts the three data hooks and returns hardcoded MTG card data.
- A one-off Playwright script generates `frontend/public/dashboard-preview.png` from `/demo`.
- Landing Hero component shows the real screenshot and links to `/demo`.

**Non-Goals:**
- No backend changes.
- No CI automation of the screenshot (manual `npm run screenshot:demo` for now).
- No editable/persistent demo state.
- No auth bypass for `/dashboard` — only `/demo` is public.

## Decisions

### Decision 1: DemoContext pattern (not hook patching or MSW)

**Options considered:**
- **A. Mock Service Worker (MSW)**: Intercepts `fetch` at the network layer. Requires adding a dev dependency and a service worker registration. Works transparently with existing hooks.
- **B. Hook-level DemoContext (chosen)**: A React context `isDemoMode: boolean` is read at the top of each data hook. When `true`, hooks return hardcoded data instead of calling the API.
- **C. Separate hooks**: Create `useDemoCards`, `useDemoInsights`, etc. and use them in a cloned `DemoPage` component.

**Rationale for B:** No new dependencies. No service worker complexity. The three affected hooks (`useCards`, `useInsightsCatalog`, `useInsightsSuggestions`) are simple to gate. The Dashboard component stays unchanged — the same JSX renders in both real and demo modes.

### Decision 2: `/demo` page as wrapper, not a cloned Dashboard

`frontend/src/pages/Demo.tsx` wraps `<Dashboard />` inside `<DemoProvider>` and adds a dismissible banner ("You're viewing a demo — sign in to manage your real collection"). No duplication of Dashboard logic.

### Decision 3: Playwright screenshot as a standalone npm script

The script (`frontend/scripts/screenshot-demo.ts`) is a one-off utility, not part of the E2E test suite. It runs against the already-running dev server (`:5173`), navigates to `/demo`, waits for cards to render, then saves a full-viewport PNG. Added as `npm run screenshot:demo` in `frontend/package.json`.

**Why not in `e2e/`?** The output is a build artifact (`public/dashboard-preview.png`), not a test result. Mixing screenshot generation with smoke tests complicates CI.

### Decision 4: Mock data lives in a single file

`frontend/src/data/demoData.ts` exports `DEMO_CARDS`, `DEMO_CATALOG`, and `DEMO_SUGGESTIONS` as typed constants. Centralising them makes it easy to update the showcase data without touching context or hook code.

## Risks / Trade-offs

- **Screenshot goes stale**: If the Dashboard UI changes, the Hero image becomes outdated. Mitigation: document `npm run screenshot:demo` in the README; consider a CI step later.
- **Demo data quality**: Fake data must look realistic enough to be convincing. Mitigation: use real card names, real set codes, and plausible prices drawn from MTG market knowledge.
- **Hook coupling**: Adding a `useDemoContext()` call to `useCards` etc. adds a small implicit dependency. Mitigation: the check is a single top-of-hook guard (`if (isDemo) return { data: DEMO_CARDS, isLoading: false }`), easy to remove.
- **Demo UX misalignment**: If mock data is too sparse or too rich, the demo misrepresents the real product. Mitigation: use ~50 cards across multiple rarities and sets to simulate a real collection.

## Migration Plan

1. Add `DemoContext` + `demoData.ts` (no visible change yet).
2. Wire hooks to check `isDemoMode`.
3. Add `Demo.tsx` page + `/demo` route in `App.tsx`.
4. Run `npm run screenshot:demo`, commit `dashboard-preview.png`.
5. Update `Hero.tsx` to use the image and add "Try demo" CTA.
6. Update `FinalCTA.tsx` with "Try demo" button.

Rollback: remove the `/demo` route and revert Hero to the gradient placeholder. No backend or DB changes to undo.

## Open Questions

- Should `/demo` be linked from the Navbar (authenticated view) as "Share demo"? Out of scope for now.
- Should the screenshot be committed to git or generated at build time? Committed for simplicity; can revisit.
