## Why

Three theme-related bugs degrade the user experience on the web dashboard:

1. **Login page is blinding white in dark mode.** `Login.tsx` uses hardcoded light-mode Tailwind classes (`bg-white`, `bg-gray-100`, `text-gray-800`) with zero `dark:` variants. When the user has dark mode active (the default), they are greeted with a jarring white page before being redirected to the dark dashboard.

2. **`InsightComparisonRenderer` uses the wrong dark-mode detection mechanism.** The component applies dark overrides via `@media (prefers-color-scheme: dark)` CSS inside a `<style>` tag. DeckDex uses **class-based** dark mode (`dark` class on `<html>`), not the OS media query. The media query fires based on OS preference, not the user's in-app theme toggle, causing the comparison cards to show wrong backgrounds when the two diverge.

3. **No cross-tab theme synchronization.** `ThemeContext` writes the theme to `localStorage` but never listens for `StorageEvent`. Opening the app in two tabs and switching theme in one leaves the other tab stale. The spec (`theme-preference/spec.md`) explicitly requires theme to be restored "across tabs."

## What Changes

- **`Login.tsx`**: Add `dark:` Tailwind variants to every hardcoded light-mode element (page background, card container, headings, text, button, error banner). Match the visual style of the rest of the authenticated app.
- **`InsightComparisonRenderer.tsx`**: Remove the `@media (prefers-color-scheme: dark)` CSS block. Instead, apply class-specific dark background colors inline by reading `document.documentElement.classList.contains('dark')` through the `useTheme()` hook, or via Tailwind `dark:` classes on the wrapper elements.
- **`ThemeContext.tsx`**: Add a `StorageEvent` listener (`window.addEventListener('storage', ...)`) inside the `ThemeProvider` `useEffect`. When another tab writes `deckdex-theme`, sync `themeState` and call `applyTheme()` so the DOM reflects the updated class.

## Capabilities

### Modified Capabilities
- `theme-preference`: Add requirement that cross-tab sync is achieved via `StorageEvent`, and that all pages (including Login) must apply `dark:` variants — no fixed light/dark islands.

## Non-goals

- Changing the default theme (stays dark).
- Adding a system-preference (`prefers-color-scheme`) auto-detection mode.
- Modifying any other component beyond the three files listed above.
- Backend changes.

## Impact

- `frontend/src/pages/Login.tsx` — styling-only changes
- `frontend/src/components/insights/InsightComparisonRenderer.tsx` — dark mode detection fix
- `frontend/src/contexts/ThemeContext.tsx` — cross-tab sync via StorageEvent
