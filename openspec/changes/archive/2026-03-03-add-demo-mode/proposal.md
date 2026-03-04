## Why

The landing page Hero section contains a visual placeholder where a real dashboard screenshot should appear, leaving a poor first impression for potential users. There is no way for visitors to experience the product before signing in, reducing conversion.

## What Changes

- **New `/demo` public route**: A fully interactive version of the Dashboard rendered with hardcoded mock card data, bypassing auth entirely. Visitors can explore the UI (search, filter, insights) without registering.
- **Landing Hero screenshot**: A Playwright script captures `/demo` at 1280×800 and saves the result as `frontend/public/dashboard-preview.png`. The Hero component is updated to display this real image.
- **Landing CTA update**: Add a "Try live demo" link in the Hero and FinalCTA sections pointing to `/demo`, alongside the existing sign-in button.
- **Mock data layer**: A `DemoContext` intercepts `useCards`, `useInsightsCatalog`, and `useInsightsSuggestions` hooks to return realistic MTG card data when in demo mode.

## Non-goals

- No backend changes — demo mode is entirely frontend.
- No persistence — demo data is hardcoded, not editable.
- No auth bypass for real routes — `/dashboard` stays protected.
- No automated CI screenshot refresh (manual script only for now).

## Capabilities

### New Capabilities

- `demo-mode`: Public `/demo` route rendering the real Dashboard UI with mock data and a DemoContext provider that short-circuits API hooks.
- `landing-page`: Core requirements for the public landing page: sections, Hero image, live demo CTA, and screenshot tooling.

### Modified Capabilities

(none)

## Impact

- `frontend/src/App.tsx` — add `/demo` route (public, no ProtectedRoute)
- `frontend/src/contexts/DemoContext.tsx` — new context providing mock data
- `frontend/src/pages/Demo.tsx` — wrapper page with DemoProvider + Dashboard + demo banner
- `frontend/src/hooks/useApi.ts` — hooks check DemoContext and return mock data
- `frontend/src/components/landing/Hero.tsx` — replace placeholder with real screenshot + "Try demo" CTA
- `frontend/src/components/landing/FinalCTA.tsx` — add "Try demo" button
- `frontend/scripts/screenshot-demo.ts` — Playwright script (one-off, not in test suite)
- `frontend/public/dashboard-preview.png` — generated artifact
