## 1. ThemeContext cross-tab sync

- [x] 1.1 In `frontend/src/contexts/ThemeContext.tsx`, add a second `useEffect` (or extend the existing one) that registers a `storage` event listener on `window`. The handler must: check `event.key === 'deckdex-theme'`, validate `event.newValue` is `'dark'` or `'light'`, then call `setThemeState(event.newValue)` and `applyTheme(event.newValue)`. The effect must return a cleanup function that calls `window.removeEventListener`.
- [x] 1.2 Verify that the listener does NOT call `window.localStorage.setItem` (the event fires in the non-writing tab — writing again would create a redundant loop). Only state and DOM update.

## 2. InsightComparisonRenderer dark mode fix

- [x] 2.1 In `frontend/src/components/insights/InsightComparisonRenderer.tsx`, import `useTheme` from `../../contexts/ThemeContext` and call it at the top of the component to get `theme`.
- [x] 2.2 Derive `const isDark = theme === 'dark'` and update the inline `style` prop on each comparison card's `div` to use conditional background colors: present+dark = `rgb(20 83 45 / 0.3)`, present+light = `rgb(240 253 244 / 0.5)`, absent+dark = `rgb(127 29 29 / 0.3)`, absent+light = `rgb(254 242 242 / 0.5)`.
- [x] 2.3 Remove the `@media (prefers-color-scheme: dark)` CSS block from the `<style>` tag. Keep the `@keyframes scaleBounce` block — it is still needed for the entrance animation.
- [x] 2.4 Confirm TypeScript compiles with no `any` violations and the component still renders correctly for both theme values.

## 3. Login.tsx dark mode styling

- [x] 3.1 In `frontend/src/pages/Login.tsx`, update the loading state outer `div` from `bg-gray-100` to `bg-gray-100 dark:bg-gray-900`. Update the loading paragraph from `text-gray-600` to `text-gray-600 dark:text-gray-400`.
- [x] 3.2 Update the card container `div` from `bg-white rounded-lg shadow-2xl` to `bg-white dark:bg-gray-800 rounded-lg shadow-2xl`.
- [x] 3.3 Update the `<h1>` from `text-gray-800` to `text-gray-800 dark:text-gray-100`.
- [x] 3.4 Update the error banner `div` from `bg-red-50 border-red-200` to `bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700`. Update the error `<p>` from `text-red-700` to `text-red-700 dark:text-red-400`.
- [x] 3.5 Update the Google login `<button>` classes: add `dark:bg-gray-700 dark:border-gray-500 dark:text-gray-200 dark:hover:bg-gray-600` alongside the existing light-mode classes.
- [x] 3.6 Update both footer `<p>` elements from `text-gray-600` / `text-xs` to include `dark:text-gray-400`.
- [x] 3.7 Change all four Google SVG `<path>` elements from `fill="#1F2937"` to `fill="currentColor"` so the icon color inherits the button's text color and adapts to both themes.
- [x] 3.8 Verify the page renders correctly in both dark and light mode by toggling ThemeToggle (or manually setting `deckdex-theme` in DevTools localStorage and reloading `/login`).

## 4. Verification

- [x] 4.1 Run `npm run lint` in `frontend/` and confirm zero new ESLint errors introduced by these changes.
- [x] 4.2 Run `npm run build` in `frontend/` and confirm it compiles successfully with no TypeScript errors.
- [ ] 4.3 Manual smoke test — open the app in two browser tabs; toggle theme in one tab; confirm the second tab updates without reload.
- [ ] 4.4 Manual smoke test — navigate to `/login` with dark mode active; confirm no white/light elements are visible; navigate to `/login` with light mode active; confirm appropriate light-mode styling.
- [ ] 4.5 Manual smoke test — open a Collection Insights panel, trigger a comparison-type insight response, toggle between dark and light mode; confirm the comparison cards' background colors update immediately to match the active theme.
