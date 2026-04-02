# Design: Hero CardMatrix Background Fix

## Root Cause Analysis

The `CardMatrix` canvas component is mounted in `App.tsx` (line 37) as a sibling that renders before the `Landing` page component in the React tree:

```
App.tsx (fragment root)
  <CardMatrix />              → canvas.pointer-events-none.fixed.inset-0.z-0
  <LandingNavbar />
  <Routes>
    <Landing />               → div.relative.z-10.min-h-screen
      <Hero />                → section.min-h-screen.pt-20.pb-16.bg-dracula-bg  ← PROBLEM
      <BentoGrid />           → section.py-20.bg-dracula-current/20             ← OK
      <FinalCTA />            → section.py-20.bg-gradient-to-r.from-dracula-bg.via-dracula-purple/20.to-dracula-bg  ← needs audit
      <Footer />              → footer.bg-dracula-bg/80                         ← OK
```

**Z-index stacking:**
- `CardMatrix` canvas: `fixed inset-0 z-0` — sits at z-index 0 behind everything
- `Landing` wrapper: `relative z-10` — positions above the canvas (correct)
- `Hero <section>`: carries `bg-dracula-bg` which resolves to `background-color: #282a36` (fully opaque) — this paints a solid rectangle over the entire viewport height (`min-h-screen`), hiding the canvas

The `Landing` wrapper does not itself carry a background class (no issue there). The bug is entirely in `Hero.tsx` line 16.

## Section-by-Section Audit

### Hero.tsx — NEEDS CHANGE

**Current class on `<section>` (line 16):**
```
"min-h-screen pt-20 pb-16 bg-dracula-bg flex items-center"
```

**Problem:** `bg-dracula-bg` = `background-color: #282a36` at 100% opacity. This is a solid fill covering `min-h-screen` (100vh). The canvas underneath is completely invisible.

**Body fallback:** `index.css` line 35 sets `body { background-color: #282a36; }`. This means removing `bg-dracula-bg` from the Hero section leaves the page body providing the dark background color — no white flash, no visual regression.

**Fix:** Remove `bg-dracula-bg`. Replace with a very subtle gradient tint that (a) maintains sufficient contrast for the headline text, (b) allows the canvas to show through, and (c) is consistent with the spec language "Hero `<section>` element's background gradient opacity SHALL be at most 20% on slate and 10% on purple."

**New class string:**
```
"min-h-screen pt-20 pb-16 flex items-center bg-gradient-to-b from-dracula-bg/20 via-transparent to-transparent"
```

**Why this gradient:** A top-to-bottom fade from 20% dracula-bg opacity at the top (blends with the LandingNavbar area) to fully transparent in the middle and bottom gives the text area a comfortable dark surface without permanently occluding the canvas. The hero headline uses `bg-clip-text` with a gradient (purple → pink) which is inherently high-contrast. The subtitle uses `text-dracula-fg` (`#f8f8f2`) on a dark body background — sufficient contrast even with 0% section background.

**Alternative considered:** A flat `bg-dracula-bg/10` (10% opacity solid tint). This was rejected because it provides no gradual transition at the top edge where `LandingNavbar` visually transitions into the hero. The gradient approach is more intentional.

### BentoGrid.tsx — NO CHANGE REQUIRED

**Current class on `<section>` (line 31):**
```
"py-20 md:py-32 bg-dracula-current/20 px-4 sm:px-6 lg:px-8"
```

`bg-dracula-current/20` = `background-color: #44475a` at 20% opacity. This is semi-transparent — the canvas IS visible through this section. No change needed.

### FinalCTA.tsx — NEEDS CHANGE

**Current class on `<section>` (line 14):**
```
"py-20 md:py-32 bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg px-4 sm:px-6 lg:px-8"
```

The gradient uses `from-dracula-bg` and `to-dracula-bg` — these are the full-opacity Dracula background color (`#282a36`) as stops on the left and right edges. Even though the center (`via-dracula-purple/20`) is semi-transparent, the left and right ~25% of the section width are fully opaque. On a standard viewport this means the canvas edges are occluded.

**Fix:** Change gradient stops to use opacity modifiers so the entire gradient is semi-transparent:
```
"py-20 md:py-32 bg-gradient-to-r from-dracula-bg/80 via-dracula-purple/20 to-dracula-bg/80 px-4 sm:px-6 lg:px-8"
```

`/80` = 80% opacity — still provides a visually solid dark feel at the edges while allowing ~20% canvas bleed-through. This retains the horizontal purple accent in the center of the CTA band.

**Why 80% not lower:** The FinalCTA is a focused conversion section. It needs to read as a distinct visual region. Too much canvas bleed-through (e.g., /20) would make this section feel unstructured. 80% is the conservative choice — visible improvement to the canvas bleed-through at edges while maintaining the section's visual weight.

### Footer.tsx — NO CHANGE REQUIRED

**Current class on `<footer>` (line 7):**
```
"bg-dracula-bg/80 border-t border-dracula-current px-4 sm:px-6 lg:px-8"
```

`bg-dracula-bg/80` = 80% opacity. The footer already uses a semi-transparent background. The canvas is already visible through the footer. No change needed.

## Z-Index Stacking Summary (Post-Fix)

| Layer | Element | z-index | Background |
|---|---|---|---|
| 0 | `<canvas>` (CardMatrix) | z-0 (fixed) | transparent |
| 1 | `Landing` wrapper | z-10 (relative) | none |
| 2 | `LandingNavbar` | (inherits z-10) | bg-dracula-bg/90 (existing) |
| 2 | Hero `<section>` | (inherits z-10) | bg-gradient (20% → 0%) |
| 2 | BentoGrid `<section>` | (inherits z-10) | bg-dracula-current/20 |
| 2 | FinalCTA `<section>` | (inherits z-10) | bg-gradient (80% → 20% → 80%) |
| 2 | Footer `<footer>` | (inherits z-10) | bg-dracula-bg/80 |

After this change, every landing section either has no background, a semi-transparent background, or a gradient with opacity modifiers. The body `background-color: #282a36` provides the solid dark canvas behind all of them.

## Reduced Motion Behavior (Unchanged)

`useReducedMotion` (in `frontend/src/components/backgrounds/useReducedMotion.ts`) is consumed by `CardMatrix`. When `prefers-reduced-motion: reduce` is active, `CardMatrix` renders a single static frame and does not animate. This behavior is entirely within `CardMatrix` and is unaffected by these CSS class changes.

## Viewport Resize Behavior (Unchanged)

`CardMatrix` uses a debounced `resize` event listener (200ms timeout) to re-size the canvas. The Hero section is `min-h-screen` (not fixed height), so it expands with content. Neither the Hero class change nor the FinalCTA gradient change affects the canvas resize logic.

## Existing Tests

The `dracula-theme.test.tsx` file lives in `frontend/src/components/backgrounds/__tests__/`. It tests the `CardMatrix`/`AetherParticles` background components — not the Hero component class strings. No test currently asserts `bg-dracula-bg` on the Hero `<section>`. No test regressions expected.

The `frontend/src/components/landing/__tests__/` directory exists but contains no Hero-specific test file. No additional test changes are required beyond a visual verification.

## Files Changed

| File | Change |
|---|---|
| `frontend/src/components/landing/Hero.tsx` | Line 16: remove `bg-dracula-bg`, add gradient tint |
| `frontend/src/components/landing/FinalCTA.tsx` | Line 14: add `/80` opacity modifier to `from-` and `to-` gradient stops |
