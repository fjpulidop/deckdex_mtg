# Theme preference

User-selectable dark/light for web dashboard; default dark; persisted in browser.

### Requirements (compact)

- **Default:** No/invalid stored preference → dark theme.
- **Switch:** Control in nav (Dashboard + Settings); switch to light or dark immediately.
- **Persist:** Choice in localStorage; restored on reload and across tabs; store on change.
- **Consistency:** Same theme for layout, nav, tables, filters, modals, buttons, errors (no fixed light/dark islands).
