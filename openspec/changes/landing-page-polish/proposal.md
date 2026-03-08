# Proposal: Landing Page Polish

## What

This change delivers the final visual and test polish for the DeckDex landing page, closing the remaining 5 open deliverables from Issue #62.

The landing page is structurally complete: Hero, BentoGrid, FinalCTA, and Footer all render. The outstanding work is entirely about visual quality and test coverage:

1. **BentoGrid gradient and icon styling** — The spec requires each BentoCard to render a visually distinct gradient illustration area with a relevant, styled icon. The current `BentoCard` component renders the illustration as a subtle, near-invisible icon (`text-white/20`) against a low-opacity gradient background. The icon area is hard to see at first glance, and there is no per-card color distinction in the icon itself. The spec explicitly forbids raw dimension text (`600x500px`) — this was never present in the current implementation, but the "visual polish" requirement means the illustration area must be more visually impactful.

2. **Hero image fallback validation** — The `Hero` component implements the fallback via an `onError` handler that hides the `<img>` and shows a sibling `<div>`. This pattern is correct but has zero test coverage. The spec scenario must be verified by automated tests.

3. **Footer auth-context tests** — The `Footer` component renders consistently regardless of auth state (it has no auth-dependent branches). The `LandingNavbar` does have auth-dependent rendering paths but that component is not part of the Footer requirement. The spec requires footer rendering tests for authenticated and unauthenticated contexts — these confirm that the Footer renders correctly when mounted within the full Landing page structure under both auth states.

## Why

The issue tracker explicitly lists these as unverified deliverables. Without test coverage for the fallback scenario and footer rendering, regressions could slip through silently. Without the gradient/icon visual refinement, the landing page does not fully satisfy the spec requirement that "each feature card SHALL show a visually styled illustration area with gradient colors and an icon relevant to the feature."

## Scope

**In scope:**
- `frontend/src/components/landing/BentoCard.tsx` — increase illustration icon opacity and add icon color theming tied to each card's gradient palette
- `frontend/src/components/landing/BentoGrid.tsx` — pass per-card icon color class to `BentoCard`
- `frontend/src/pages/__tests__/Landing.test.tsx` — new test file covering hero fallback and footer auth-context rendering

**Out of scope:**
- Any changes to `Hero.tsx`, `FinalCTA.tsx`, `Footer.tsx`, `Landing.tsx` — these are structurally correct already
- Backend changes
- i18n key additions — all existing keys cover the tested content
- Accessibility changes — covered by a separate spec change

## Success Criteria

1. Each BentoCard illustration area renders with an icon visible at resting opacity (`text-white/50` or higher) and a distinct icon color tint per card
2. No raw dimension text appears anywhere in the BentoGrid section
3. A test asserts that when the hero `<img>` fires `onError`, the fallback `<div>` becomes visible and the image is hidden
4. A test asserts the Footer renders (finds copyright text or social links) when mounted under an unauthenticated auth context
5. A test asserts the Footer renders correctly when mounted under an authenticated auth context
6. All existing tests continue to pass — zero regressions
