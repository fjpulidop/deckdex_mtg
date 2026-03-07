## Context

DeckDex's theme system uses **class-based dark mode**: the `dark` class is toggled on `<html>` by `ThemeContext`. The initial class is applied in `main.tsx` before the first React render to prevent flash. `localStorage` key `deckdex-theme` persists the preference.

Three bugs exist in the current implementation:

1. **Login.tsx** was written without dark mode awareness. Every class is hardcoded light (`bg-white`, `bg-gray-100`, `text-gray-800`, etc.). Users with dark mode (the default) see a white flash/page on the login route before the auth redirect.

2. **`InsightComparisonRenderer.tsx`** injects a `<style>` block with `@media (prefers-color-scheme: dark)` to override background colors of comparison cards. DeckDex does not use OS-preference-based dark mode — it uses the explicit `.dark` class. The media query only fires when the OS is in dark mode, not when the user's in-app toggle is dark. This causes wrong backgrounds whenever the user's OS and in-app theme differ.

3. **`ThemeContext.tsx`** writes to `localStorage` on toggle but never reacts to external writes. The `storage` event fires in sibling tabs when `localStorage` is mutated. Without a listener, a second tab stays on its initial theme indefinitely after the user switches in another tab, violating the spec requirement "restored…across tabs."

All three bugs are frontend-only. No backend changes.

## Goals / Non-Goals

**Goals:**
- Login page is fully themed — respects both dark and light mode.
- `InsightComparisonRenderer` uses class-based dark detection consistent with the rest of the app.
- Theme change in one tab propagates to all other open tabs within a render cycle.

**Non-Goals:**
- System preference (`prefers-color-scheme`) auto-detection / "system" theme option.
- Theme animation/transitions.
- Changes to any component not named in the proposal.
- Backend changes.

## Decisions

### Decision 1: Login.tsx dark styling approach — use `dark:` Tailwind variants

**Options considered:**

A. Use `dark:` Tailwind utility variants directly on each element (same pattern as every other component in the project).
B. Read `useTheme()` and dynamically compute class names.

**Decision: Option A.**

Every other component (Navbar, Dashboard, Settings, modals) uses `dark:` variants — it is the established codebase pattern. `ThemeToggle.tsx` and `Login.tsx`'s own page background (`bg-gradient-to-br from-gray-900 to-gray-800`) already lean dark — the card container `bg-white` is what breaks. We apply `dark:bg-gray-800` / `dark:text-gray-100` etc. to every element that currently has only a light class. The loading spinner branch gets the same treatment.

**Specific class mappings for Login.tsx:**
- Loading state outer div: `bg-gray-100` → `bg-gray-100 dark:bg-gray-900`
- Loading text: `text-gray-600` → `text-gray-600 dark:text-gray-400`
- Main page wrapper: already `from-gray-900 to-gray-800` (dark gradient, acceptable for both modes; light mode gets a softer gradient)
- Card container: `bg-white` → `bg-white dark:bg-gray-800`
- Title: `text-gray-800` → `text-gray-800 dark:text-gray-100`
- Google button: `bg-white border-gray-300 text-gray-700 hover:bg-gray-50` → add `dark:bg-gray-700 dark:border-gray-500 dark:text-gray-200 dark:hover:bg-gray-600`
- Error banner: `bg-red-50 border-red-200` → add `dark:bg-red-900/30 dark:border-red-700`; `text-red-700` → add `dark:text-red-400`
- Footer text: `text-gray-600` → add `dark:text-gray-400`; `text-xs` text same treatment
- The Google SVG paths use hardcoded `fill="#1F2937"` — change to `fill="currentColor"` so it inherits text color, which will respect dark mode automatically

### Decision 2: InsightComparisonRenderer — replace `<style>` media query with Tailwind classes via `useTheme()`

**Options considered:**

A. Remove the `<style>` block; apply background colors through inline styles conditional on `useTheme().theme`.
B. Remove the `<style>` block; add Tailwind `dark:` classes to the wrapper element and reference CSS variables.
C. Keep the `<style>` block but change `@media` to `.dark &` descendant selector so it works with class-based dark mode.

**Decision: Option A (inline styles conditional on theme) for the present/absent backgrounds, with Option C as fallback.**

The component already uses inline `style` for `borderColor`, `backgroundColor`, and animation — these are already dynamic. Adding the dark-mode background color to the same inline style object (conditioned on `theme === 'dark'`) is the most consistent approach and avoids adding a class-based `<style>` dependency.

The `@keyframes scaleBounce` animation block in the `<style>` tag must stay (Tailwind cannot define keyframes inline). Only the `@media (prefers-color-scheme: dark)` block inside it is removed.

Implementation: import `useTheme`, derive `isDark = theme === 'dark'`, then compute `backgroundColor` inline:
- Present + dark: `rgb(20 83 45 / 0.3)`
- Present + light: `rgb(240 253 244 / 0.5)`
- Absent + dark: `rgb(127 29 29 / 0.3)`
- Absent + light: `rgb(254 242 242 / 0.5)`

### Decision 3: Cross-tab sync — `StorageEvent` listener in `ThemeProvider`

**Options considered:**

A. `window.addEventListener('storage', handler)` inside a `useEffect` in `ThemeProvider`.
B. Poll `localStorage` on a timer.
C. Use a `BroadcastChannel`.

**Decision: Option A.**

`StorageEvent` is the browser-native, zero-dependency mechanism for cross-tab `localStorage` sync. It fires in all tabs *except* the one that wrote — which is exactly the desired behavior (the writing tab already has the updated state). `BroadcastChannel` would also work but adds complexity for no benefit. Polling is wasteful.

Handler logic:
```
if (event.key === 'deckdex-theme' && (event.newValue === 'dark' || event.newValue === 'light')) {
  setThemeState(event.newValue);
  applyTheme(event.newValue);
}
```
The handler is added and cleaned up within the same `useEffect` to prevent leaks.

## Risks / Trade-offs

- **[Risk] Login page outer gradient is dark (`from-gray-900 to-gray-800`) in both light and dark mode** — the gradient was already dark-coded before this fix. A proper light-mode login would use a lighter gradient. The gradient is not part of the three bugs being fixed, and changing it would expand scope. Decision: keep the existing gradient, document as a known cosmetic issue for a future pass. (The task list includes a note about this.)

- **[Risk] Google SVG `fill` change** — changing `fill="#1F2937"` (dark gray) to `fill="currentColor"` means the Google logo color depends on the button text color. In light mode that's `text-gray-700` (dark enough). In dark mode that's `text-gray-200` (light gray), which may make the logo look faded compared to Google's brand colors. Alternative: use separate `dark:fill-gray-200` SVG path classes. This is a minor cosmetic tradeoff — the logo is still recognizable.

- **[Risk] StorageEvent does not fire in the same tab** — this is by spec. The writing tab relies on its React state, which is already updated. No issue.

- **[Trade-off] `useTheme()` in `InsightComparisonRenderer`** — adds a context dependency to a presentational component. Acceptable: the same pattern is already used in `ThemeToggle`, `Navbar`, and others. No architectural concern.

## Migration Plan

1. Fix `ThemeContext.tsx` first (pure behavior, no visual change, no regressions).
2. Fix `InsightComparisonRenderer.tsx` (no visual change for users whose OS and app theme match; fixes users where they diverge).
3. Fix `Login.tsx` (visual change, but only Login page, no other page affected).
4. No migrations, no backend deploys, no data changes.
5. Rollback: revert the three files. No state is persisted differently.

## Open Questions

None. All three fixes have clear, deterministic implementations.
