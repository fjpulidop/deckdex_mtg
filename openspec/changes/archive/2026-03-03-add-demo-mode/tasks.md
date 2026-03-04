## 1. Mock Data

- [x] 1.1 Create `frontend/src/data/demoData.ts` with `DEMO_CARDS` (30+ cards, varied rarities/sets/prices), `DEMO_CATALOG` (5+ insight entries with icons and categories), and `DEMO_SUGGESTIONS` (3 suggestion chips)

## 2. DemoContext

- [x] 2.1 Create `frontend/src/contexts/DemoContext.tsx` exporting `DemoProvider` and `useDemoMode` hook (`isDemoMode: boolean`)
- [x] 2.2 Add `isDemoMode` guard at the top of `useCards` in `useApi.ts` — when true, return `{ data: DEMO_CARDS, isLoading: false, error: null }` shape
- [x] 2.3 Add `isDemoMode` guard to `useInsightsCatalog` — return `DEMO_CATALOG` mock
- [x] 2.4 Add `isDemoMode` guard to `useInsightsSuggestions` — return `DEMO_SUGGESTIONS` mock

## 3. Demo Page & Route

- [x] 3.1 Create `frontend/src/pages/Demo.tsx` wrapping `<Dashboard />` inside `<DemoProvider>` with a dismissible top banner ("You're viewing a demo — sign in to manage your real collection")
- [x] 3.2 Add `/demo` route in `frontend/src/App.tsx` (public, no `<ProtectedRoute>`) rendering `<Demo />`

## 4. Screenshot Script

- [x] 4.1 Create `frontend/scripts/screenshot-demo.mjs` using Playwright: navigate to `http://localhost:5173/demo`, wait for `table tbody tr` to be visible, screenshot full viewport (1280×800), save to `frontend/public/dashboard-preview.png`
- [x] 4.2 Add `"screenshot:demo": "node scripts/screenshot-demo.mjs"` script to `frontend/package.json`
- [x] 4.3 Run `npm run screenshot:demo` and verify `frontend/public/dashboard-preview.png` is generated correctly

## 5. Landing Page Updates

- [x] 5.1 Update `frontend/src/components/landing/Hero.tsx` — replace the gradient placeholder div with an `<img src="/dashboard-preview.png" alt="DeckDex dashboard preview" />` with a gradient fallback on error
- [x] 5.2 Add "Try live demo" secondary CTA button to `Hero.tsx` (unauthenticated view only), linking to `/demo`
- [x] 5.3 Add "Try live demo" secondary button to `frontend/src/components/landing/FinalCTA.tsx` (unauthenticated view only)
- [x] 5.4 Import and render `<Footer />` in `frontend/src/pages/Landing.tsx`

## 6. Verification

- [x] 6.1 Visit `/demo` in browser — confirm Dashboard renders with mock cards, no network errors in console
- [x] 6.2 Test search and rarity filters on `/demo` — confirm filtering works on mock data
- [x] 6.3 Visit `/` — confirm Hero shows the screenshot image and "Try live demo" button
- [x] 6.4 Run `npm run test` (E2E smoke tests) — confirm no regressions
