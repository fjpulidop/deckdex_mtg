# Proposal: Fix Landing Page Visual Hierarchy and Dracula Theme Rendering

**Change name:** `fix-landing-dracula-theme-rendering`
**Layer:** Frontend only
**Complexity:** Low (< 1 day)
**Tracking:** GitHub Issue #146

---

## Problem Statement

The landing page renders with broken visual hierarchy: section backgrounds bleed into one another and body text in several components appears black instead of the intended Dracula foreground color (`#f8f8f2`).

The root cause is a Tailwind version mismatch between configuration format and engine.

`frontend/src/index.css` opens with `@import "tailwindcss"`, which activates the **Tailwind v4 engine**. In v4, color tokens must be declared inside an `@theme { }` block in the CSS file. The project instead defines them in `frontend/tailwind.config.js` under `theme.extend.colors`, which is the **Tailwind v3 format**. In v4, that file is silently ignored — no custom utility classes (e.g., `text-dracula-fg`, `bg-dracula-bg`, `border-dracula-current`) are generated. The browser falls back to its own default for unknown color classes, which is black for `color` properties and transparent for `background-color` properties.

The secondary symptom follows from the first: section backgrounds use opacity-modified Dracula classes such as `bg-dracula-bg/80` and `bg-dracula-bg/20`. Because the base token is not registered, these opacity modifiers also produce transparent backgrounds, making sections visually indistinguishable from each other and from the `CardMatrix` canvas behind them.

---

## Proposed Solution

**Migrate Dracula + primary + accent color tokens from `tailwind.config.js` (v3 format) into an `@theme` block in `index.css` (v4 format).** No Tailwind version bump is required — this is a configuration format correction.

Once tokens are declared in `@theme`, all existing class names in all landing components (`text-dracula-fg`, `bg-dracula-bg/80`, `from-dracula-purple`, etc.) will resolve to their intended hex values without any changes to the component files themselves.

With tokens resolving correctly, each section will still need a review pass to verify that section backgrounds are visually distinct. The specific issue is that Hero, BentoGrid, and FinalCTA all use low-opacity variants of the same `dracula-bg` base, which will still look similar once the token is fixed. The section background classes should be adjusted to use solid or higher-opacity Dracula backgrounds that create clear visual breaks.

In parallel, `Landing.tsx` must be verified for `LandingNavbar` inclusion. The component is already rendered at the `App.tsx` level (line 37: `{isLandingPage && <LandingNavbar />}`), so the composition is correct — no change needed there.

---

## Scope

**In scope:**
- Add `@theme` block to `frontend/src/index.css` with all Dracula, primary, and accent tokens
- Update section background classes on Hero, BentoGrid, and FinalCTA for visual separation
- Verify LandingNavbar composition in Landing.tsx and App.tsx
- Audit all Dashboard-adjacent components for any dracula/primary/accent class regressions caused by the `@theme` migration

**Out of scope:**
- Any logic changes in React components
- New components or new routes
- Tailwind version upgrade
- Backend changes of any kind

---

## Acceptance Criteria

1. All Dracula utility classes (`text-dracula-fg`, `bg-dracula-bg`, `border-dracula-current`, etc.) resolve to their correct hex values — verifiable via browser DevTools computed styles.
2. No text in any landing section renders in black (`#000000` or `#0d0f0f`) — all body/paragraph text is `#f8f8f2` (dracula-fg) or `#6272a4` (dracula-comment).
3. The three content sections (Hero, BentoGrid, FinalCTA) are visually distinguishable from each other when scrolling — each has a unique background treatment creating clear section breaks.
4. The `LandingNavbar` is present and rendered above the page content with correct Dracula styling.
5. `npm run build` completes without errors and `npm run lint` reports zero new violations.
6. The BentoCard gradient backgrounds are visible and distinct per card (cyan / purple / pink / orange / green).
