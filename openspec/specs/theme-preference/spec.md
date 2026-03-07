# Theme preference

User-selectable dark/light for web dashboard; default dark; persisted in browser.

### Requirements (compact)

- **Default:** No/invalid stored preference → dark theme.
- **Switch:** Control in nav (Dashboard + Settings); switch to light or dark immediately.
- **Persist:** Choice in localStorage; restored on reload and across tabs in real time (via `storage` event); store on change.
- **Consistency:** Same theme for layout, nav, tables, filters, modals, buttons, errors, login page (no fixed light/dark islands).
- **Cross-tab sync:** `ThemeProvider` listens to the `storage` event on `window`. When `key === 'deckdex-theme'` and value is `'dark'` or `'light'`, the provider updates React state and re-applies the theme class to `document.documentElement`. Invalid or unrelated storage events are ignored.
- **Login page:** The `/login` route SHALL apply the active theme — dark-themed card, text, and button in dark mode; light-themed in light mode. No bright-white elements in dark mode.
- **No OS media query for in-app dark mode:** Components SHALL NOT use `@media (prefers-color-scheme: dark)` for in-app dark mode. Use Tailwind `dark:` variants or theme-context-conditioned inline styles (class-based dark mode via `dark` on `<html>`).
