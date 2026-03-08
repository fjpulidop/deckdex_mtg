# Design: Landing Page Polish

## Impact Analysis

### Files changed

| File | Change type | Reason |
|---|---|---|
| `frontend/src/components/landing/BentoCard.tsx` | Modify | Add `iconColor` prop; increase illustration icon opacity and apply color tint |
| `frontend/src/components/landing/BentoGrid.tsx` | Modify | Pass `iconColor` per card; review and confirm no raw dimension text |
| `frontend/src/pages/__tests__/Landing.test.tsx` | Create | Hero fallback test + Footer auth-context tests |

No other files change. `Hero.tsx`, `FinalCTA.tsx`, `Footer.tsx`, and `Landing.tsx` are structurally correct and do not need modification.

---

## BentoCard Visual Refinement

### Problem statement

`BentoCard.tsx` renders the illustration icon with `text-white/20`, which produces an icon at 20% opacity — nearly invisible against the gradient background. The spec says:

> each feature card SHALL show a visually styled illustration area with gradient colors and an icon relevant to the feature

20% opacity does not satisfy "visually styled with gradient colors and an icon relevant to the feature." The icon must be legible at rest and clearly themed to the card's color palette.

### Design decision: `iconColor` prop on `BentoCard`

**Approach:** Add an optional `iconColor: string` prop to `BentoCardProps`. This prop accepts a Tailwind text color utility class (e.g., `"text-blue-400/60"`). When provided, it replaces the default `text-white/20` class on the illustration icon wrapper.

**Why this approach over alternatives:**
- **Alternative 1 — Derive color from `gradientFrom`/`gradientTo`**: These strings are already in `from-blue-500/20` format. Parsing them to produce a matching icon color requires string manipulation that is fragile and untestable. Passing an explicit `iconColor` prop keeps derivation logic in `BentoGrid.tsx` where the card vocabulary lives.
- **Alternative 2 — Hard-code icon colors inside `BentoCard` via the size**: Not viable — `BentoCard` is a generic component and shouldn't know which feature it represents.
- **Alternative 3 — CSS custom properties or inline styles**: Overkill for a Tailwind project. Tailwind utility classes are the established pattern throughout the codebase.

**Chosen approach rationale:** Explicit prop, minimal surface area, consistent with the Tailwind-first pattern in every landing component.

### Icon opacity and color values per card

The gradient colors already defined in `BentoGrid.tsx` inform the icon color choices:

| Card | `gradientFrom` | `iconColor` value |
|---|---|---|
| Collection Management | `from-blue-500/20` | `text-blue-400/60` |
| Deck Builder | `from-purple-500/20` | `text-purple-400/60` |
| AI Insights | `from-pink-500/20` | `text-pink-400/60` |
| Real-time Progress | `from-amber-500/20` | `text-amber-400/60` |
| Pricing Analytics | `from-green-500/20` | `text-green-400/60` |

Opacity `/60` (60%) is chosen because:
- It is legible against the illustration background gradient (which sits at `opacity-10` to `opacity-15`)
- It maintains the subtle aesthetic — these are background illustration elements, not foreground content
- On hover, the group-hover transition in the current code already transitions to `text-white/30`; we preserve that behavior by also updating the hover state to `group-hover:text-white/50`

### `BentoCard.tsx` change summary

```
BentoCardProps {
  // existing props unchanged ...
  iconColor?: string;   // NEW: Tailwind text color class for illustration icon
}
```

In the illustration `div`, replace:
```tsx
<div className="relative text-white/20 group-hover:text-white/30 transition-colors duration-300">
```
with:
```tsx
<div className={`relative transition-colors duration-300 ${iconColor ?? 'text-white/40 group-hover:text-white/60'}`}>
```

The default fallback (`text-white/40 group-hover:text-white/60`) applies when `iconColor` is not passed — this improves the default vs the previous `text-white/20` even without an explicit color. It also acts as a safety net for any future card that does not specify a color.

### Raw dimension text audit

A search of `BentoCard.tsx` and `BentoGrid.tsx` confirms no string matching `\d+x\d+px` is present. The `sizeClasses` record in `BentoCard` uses Tailwind classes (`h-96`, `h-48`, `h-40`, `h-32`), not rendered text. This requirement is already satisfied — no code change is needed to address it specifically.

---

## Hero Image Fallback Tests

### Mechanism being tested

`Hero.tsx` lines 89–103:

```tsx
<img
  src="/dashboard-preview.png"
  alt="DeckDex dashboard preview"
  className="absolute inset-0 w-full h-full object-cover object-top"
  onError={(e) => {
    const target = e.currentTarget;
    target.style.display = 'none';
    const fallback = target.nextElementSibling as HTMLElement | null;
    if (fallback) fallback.style.display = 'flex';
  }}
/>
<div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 via-slate-900 to-slate-900 items-center justify-center hidden">
  <div className="h-32 w-32 rounded-lg bg-gradient-to-br from-purple-500/30 to-pink-500/30 blur-xl" />
</div>
```

The image starts visible and the fallback `div` starts `hidden`. On `onError`, the image gets `display: none` and the fallback gets `display: flex`.

### Test approach

The test renders `Hero` in isolation (not the full `Landing` page) to keep it fast and focused. It mocks:
- `@/contexts/AuthContext` — provides `isAuthenticated: false` (the hero renders identically regardless; unauthenticated is simpler since it shows the sign-in button)
- `react-i18next` — the test setup already initializes i18n with English translations (see `frontend/src/test/setup.ts`), so no additional mock needed
- `framer-motion` — `motion.div` can be left un-mocked; jsdom handles inline styles without animation

To trigger `onError` in jsdom, fire the `error` event on the `<img>` element using `fireEvent.error(imgEl)` from `@testing-library/react`.

**Assertions:**
1. Before firing error: `img` is in the document with `src="/dashboard-preview.png"`; fallback `div` has `style.display` equal to `''` (not yet modified)
2. After `fireEvent.error(img)`: `img` has `style.display === 'none'`; the fallback `div` has `style.display === 'flex'`

The fallback `div` is identified by querying for the sibling `div` after the `img` (or by its Tailwind class presence). Since it has no text content or accessible role, we locate it as the `img.nextElementSibling`.

### Why not use `waitFor`?

The `onError` handler in `Hero.tsx` is synchronous — it directly sets `style.display` on two DOM nodes. There is no async work, so `fireEvent.error` is sufficient and `waitFor` is unnecessary.

---

## Footer Auth-Context Tests

### What the Footer actually renders

`Footer.tsx` has no auth-dependent branches. It renders the same four-column link grid plus social links regardless of whether the user is authenticated. This means the "auth-context tests" are really tests that confirm Footer renders without error when the surrounding auth context is in either state.

**Why test both states?**
The issue requirement is explicit. Additionally, if Footer is ever modified to add auth-dependent UI (e.g., a "Go to Dashboard" link in the footer), these tests will catch any regressions for both states.

### Render approach

Use a `renderFooter(isAuthenticated: boolean)` helper that wraps `Footer` with:
- `MemoryRouter` (Footer may eventually use Link components)
- A mocked `AuthContext` provider via `vi.mock('@/contexts/AuthContext', ...)` returning the requested `isAuthenticated` value

Actually — since `Footer.tsx` does not call `useAuth()`, wrapping with `MemoryRouter` alone is sufficient. But to be explicit and defensive, the test mocks `AuthContext` anyway so the test is future-proof.

**Assertions (both auth states):**
- `footer` element is in the document (`getByRole('contentinfo')`)
- Copyright text renders (contains the current year — use regex `/\d{4}/`)
- Social links render: GitHub, Twitter, Discord links visible (queried by `aria-label`)

Since the Footer uses `t('footer.copyright', { year: ... })` and the test setup initializes i18n with actual English translations (`frontend/src/locales/en.json`), the translations render correctly without additional mocking.

---

## Test File Structure

**Path:** `frontend/src/pages/__tests__/Landing.test.tsx`

**Test suites:**
1. `describe('Hero image fallback')` — 2 tests (before/after error)
2. `describe('Footer rendering', () => { describe('when unauthenticated', ...) describe('when authenticated', ...) })` — 2×3 = 6 tests

**Mocks required:**
- `vi.mock('@/contexts/AuthContext', ...)` — controls `isAuthenticated` value
- `vi.mock('@/utils/auth', ...)` — stubs `redirectToGoogleLogin` (called by Hero sign-in button)
- `vi.mock('framer-motion', ...)` — optional; only needed if jsdom can't handle framer animations. The Dashboard test does NOT mock framer-motion, so we follow the same pattern and leave it un-mocked.

**Imports:**
```ts
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Hero } from '@/components/landing/Hero';
import { Footer } from '@/components/landing/Footer';
```

---

## No Changes to `Landing.tsx`

The page component (`frontend/src/pages/Landing.tsx`) is 15 lines and is already correct. It imports and renders Hero, BentoGrid, FinalCTA, and Footer in order. No changes needed.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Tailwind purge strips dynamically constructed class strings | All `iconColor` values are static strings passed as props in `BentoGrid.tsx` — they are present in source and will not be purged |
| jsdom `fireEvent.error` does not trigger `onError` | Confirmed: `fireEvent.error` dispatches a synthetic `error` event; React's synthetic event system propagates it to the `onError` handler |
| i18n keys for footer not initialized in test | The test setup at `frontend/src/test/setup.ts` already loads `en.json` — all footer keys are present in that file |
| `framer-motion` throws in jsdom | Existing Dashboard and DeckBuilder tests run without mocking framer-motion — this project's jsdom config handles it |
