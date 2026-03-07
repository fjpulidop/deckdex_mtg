# Theme Persistence & Consistency Exploration

**Date:** 2026-03-07
**Spec:** `openspec/specs/theme-preference/spec.md`
**Original design:** `openspec/changes/archive/2026-02-08-dark-mode-dashboard/design.md`

## Current State

### What's Built
- **ThemeContext** (`frontend/src/contexts/ThemeContext.tsx`): React context with `useTheme` hook, `dark`/`light` type, localStorage persistence under key `deckdex-theme`, default dark
- **ThemeToggle** (`frontend/src/components/ThemeToggle.tsx`): Sun/Moon icon button with proper aria-label, placed in Navbar only
- **Flash prevention**: `main.tsx` lines 11-13 apply `dark` class synchronously before React renders (reads localStorage, toggles classList)
- **Tailwind v4 dark mode**: `@custom-variant dark (&&:where(.dark, .dark *))` in `index.css`
- **Body backgrounds**: CSS-based `body { background: #f3f4f6 }` / `.dark body { background: #111827 }` in `index.css`
- **40 files** use `dark:` Tailwind variants -- extensive coverage across pages, modals, components

### Architecture Summary
1. `index.html` -- no `dark` class on `<html>` (blank)
2. `main.tsx` -- synchronous script sets `dark` class before React mount
3. `ThemeContext` -- React state + localStorage + classList in sync
4. Components -- use Tailwind `dark:` variants

## Gaps Found

### BUG: Login.tsx has ZERO dark mode support
- `Login.tsx` uses hardcoded light-only classes: `bg-white`, `text-gray-800`, `bg-gray-100`, `text-gray-600`, `bg-red-50`, `text-red-700`
- No `dark:` variants anywhere in the file
- Loading spinner state also missing dark mode (`bg-gray-100`, `text-gray-600`)
- **Impact**: Bright white flash on login page when user has dark theme preference

### BUG: InsightComparisonRenderer uses wrong dark mode detection
- Uses `@media (prefers-color-scheme: dark)` combined with `.dark` selector
- This is doubly wrong: (1) DeckDex uses class-based dark mode, not media query, (2) requiring BOTH media query AND class means styles only apply when system is dark AND class is set
- Dark background colors for present/absent items may not apply correctly

### MISSING: No cross-tab synchronization
- Spec requires "restored on reload and across tabs"
- No `StorageEvent` listener in ThemeContext
- If user opens two tabs and changes theme in one, the other stays on old theme

### MISSING: No system preference detection
- Design doc explicitly deferred this as "non-goal for MVP"
- `prefers-color-scheme` media query is not used for initial default
- Only one component references it (InsightComparisonRenderer, incorrectly)
- Minor gap -- spec says default dark, which is fine

### MISSING: `index.html` has no initial dark class
- Flash prevention relies on `main.tsx` synchronous JS, which runs after HTML parse
- A true zero-flash solution would set `class="dark"` on `<html>` and have an inline `<script>` in `<head>` that reads localStorage before any CSS paints
- Current approach works for most cases since `main.tsx` runs before React, but there's a theoretical flash window between HTML parse and script execution

### MISSING: ThemeToggle only in Navbar, not in Settings page
- Spec says "Control in nav (Dashboard + Settings)"
- ThemeToggle is only in Navbar (which appears on all pages), not as a dedicated Settings control
- Navbar presence covers the intent, but Settings page has no theme section

### INCONSISTENCY: Recharts axis color override
- `index.css` has `.dark .deck-detail-mana-curve .recharts-cartesian-axis-tick text { fill: #e5e7eb }`
- This is a one-off CSS override for chart text -- PriceChart.tsx may need similar treatment
- No systematic approach for chart theming

### MINOR: Demo.tsx banner doesn't need dark variants (gradient bg is intentional)
### MINOR: Settings.tsx toggle knob uses `bg-white` without dark variant (intentional -- it's a toggle switch)

## Improvement Ideas

| # | Idea | Value | Complexity | Impact/Effort |
|---|------|-------|------------|---------------|
| 1 | Fix Login.tsx dark mode (add dark: variants to all elements) | HIGH -- broken page for dark users | Small (1hr) | **HIGHEST** |
| 2 | Fix InsightComparisonRenderer dark mode detection (remove @media query, use .dark class only) | MEDIUM -- subtle visual bug | Small (15min) | **VERY HIGH** |
| 3 | Add cross-tab sync via StorageEvent listener in ThemeContext | MEDIUM -- spec compliance, nice UX | Small (30min) | **HIGH** |
| 4 | Move flash-prevention to inline `<script>` in index.html `<head>` | LOW -- current approach works 99% of time | Small (15min) | MEDIUM |
| 5 | Add theme section to Settings page (dedicated toggle + preview) | LOW -- Navbar toggle covers it | Small (30min) | LOW |
| 6 | System preference as default when no stored preference | LOW -- dark default is fine for MTG aesthetic | Small (30min) | LOW |
| 7 | Create shared chart theme config (Recharts colors for dark/light) | MEDIUM -- prevents one-off CSS hacks | Medium (1-2hr) | MEDIUM |
| 8 | Extract color tokens to CSS custom properties for easier theming | LOW -- Tailwind handles this well enough | Large (4-8hr) | LOW |

## Recommended Top Pick

**Fix #1 + #2 + #3 as a single small change** (estimated ~2 hours total):

1. **Login.tsx dark mode** -- highest priority because it's a fully broken page. Every element needs dark: variants added. The loading state spinner section also needs fixing.

2. **InsightComparisonRenderer fix** -- trivial fix, just remove the `@media (prefers-color-scheme: dark)` wrapper and keep the `.dark` class selector only.

3. **Cross-tab StorageEvent sync** -- add a `useEffect` in ThemeProvider that listens for `storage` events on the `deckdex-theme` key and calls `setThemeState` + `applyTheme` when another tab changes it. ~10 lines of code.

These three together close all the real bugs and bring the theme system to full spec compliance. The remaining items (#4-#8) are polish/enhancement and can be deferred.

## Key Files
- `/Users/javi/repos/deckdex_mtg/frontend/src/contexts/ThemeContext.tsx` -- theme provider
- `/Users/javi/repos/deckdex_mtg/frontend/src/components/ThemeToggle.tsx` -- toggle button
- `/Users/javi/repos/deckdex_mtg/frontend/src/main.tsx` -- flash prevention
- `/Users/javi/repos/deckdex_mtg/frontend/src/index.css` -- dark mode variant + body colors
- `/Users/javi/repos/deckdex_mtg/frontend/src/pages/Login.tsx` -- BUG: zero dark mode
- `/Users/javi/repos/deckdex_mtg/frontend/src/components/insights/InsightComparisonRenderer.tsx` -- BUG: wrong dark detection
- `/Users/javi/repos/deckdex_mtg/frontend/index.html` -- no initial dark class
- `/Users/javi/repos/deckdex_mtg/frontend/tailwind.config.js` -- no darkMode config (handled via CSS @custom-variant)
