# Proposal: Dark mode dashboard

## Why

Users expect a dark theme option in modern web apps; offering it improves comfort and accessibility. Making dark mode the default and persisting the user's choice ensures a consistent experience across sessions without requiring backend or account support.

## What Changes

- Dashboard and Settings (and all shared UI) support a **dark theme by default** and an optional **light theme**.
- A **theme selector** (e.g. toggle or control in the nav) lets the user switch between dark and light.
- The **selected theme is persisted** in the browser (e.g. localStorage) and restored on next visit.
- Styling is applied via theme-aware classes (e.g. Tailwind dark mode) so all main surfaces, text, and controls look correct in both themes.

## Capabilities

### New Capabilities

- **theme-preference**: User-selectable UI theme (dark / light) for the web dashboard, with dark as the default and the choice persisted in localStorage (or equivalent). Covers where the control is shown, how the theme is applied (e.g. class on root), and persistence key/behavior.

### Modified Capabilities

- None. Existing `web-dashboard-ui` behavior (filters, jobs, table, etc.) is unchanged; theme is an additive concern.

## Impact

- **Frontend only**: React app under `frontend/` (App, layout/nav, and components that use background/text colors).
- **Tailwind**: Dark mode configured (e.g. class strategy) and `dark:` variants added where needed.
- **Storage**: Client-side only (localStorage); no API or backend changes.
- **Specs**: New spec `theme-preference` under this change; no edits to existing main specs required.
