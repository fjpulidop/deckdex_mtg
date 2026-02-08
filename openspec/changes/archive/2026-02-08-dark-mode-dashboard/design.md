# Design: Dark mode dashboard

## Context

The web dashboard (React, Vite, Tailwind v4) currently uses a fixed light palette: `body` and layout use `bg-gray-100`, `bg-white`, and gray/blue text. There is no theme abstraction or persistence. This change adds a user-selectable dark/light theme with dark as the default and the choice persisted client-side.

## Goals / Non-Goals

**Goals:**

- Apply a single theme (dark or light) consistently across the whole app (Dashboard, Settings, modals, error states).
- Default to dark theme when the user has no stored preference.
- Persist the user's choice so it is restored on the next visit.
- Expose a clear control (e.g. in the nav) to switch between dark and light.

**Non-Goals:**

- Following system preference (e.g. `prefers-color-scheme`) as the only source of truth; we default to dark and persist explicit choice. (System preference can be a future enhancement.)
- Backend or account-based theme storage; client-only (localStorage) is sufficient for this change.
- Per-page or per-section themes; one global theme for the app.

## Decisions

1. **Where to persist:** localStorage with a single key (e.g. `deckdex-theme`), values `dark` | `light`. No backend, no cookies. Rationale: simple, no auth required, survives reload and new tabs on same origin.

2. **How to apply theme:** Class on the document root (`<html>`). When theme is dark, set `class="dark"` (or equivalent); when light, remove it (or set `class="light"` if we want explicit light). Tailwind dark mode uses **class** strategy so that `dark:*` variants apply when the class is present. Rationale: standard Tailwind approach, no duplicate CSS, easy to toggle from React.

3. **Default when no preference:** Treat missing or invalid localStorage as **dark**. Rationale: aligns with "dark as default" and avoids a flash of light before JS runs if we later add an inline script that sets the class before paint.

4. **Where to put the theme control:** In the shared navigation (Dashboard and Settings). Same control on both pages so the user can switch theme from anywhere. Rationale: single place, consistent UX.

5. **Initialization and flash:** Read localStorage and set the class in React (e.g. in a provider or root effect) on mount. If we observe a visible flash of wrong theme, we can add a small inline script in `index.html` that runs before body paint and sets the class from localStorage. For this change we rely on React-only init unless testing shows a noticeable flash.

6. **Tailwind config:** Enable dark mode with `darkMode: 'class'` (or the v4 equivalent in the project's config). No new dependencies; use Tailwind's built-in dark variant.

## Risks / Trade-offs

- **Flash of wrong theme:** If the class is applied only after React hydrates, the first paint might use light (e.g. from `index.css` or no `dark` class). Mitigation: use neutral/default background in CSS if needed; optionally add a blocking script in `<head>` that sets the class from localStorage before first paint.
- **Tailwind v4:** Confirm in the project how to set `darkMode: 'class'` (or equivalent) so `dark:` variants are respected.
- **Coverage:** Every component that sets background or text color may need `dark:` variants. Mitigation: systematic pass over layout, nav, cards, tables, modals, buttons, and error/toast UI; rely on Tailwind's dark palette for consistency.

## Migration Plan

- Frontend-only change: no API or DB changes. Deploy new frontend build; existing users get dark by default until they set light and persist.
- No rollback beyond reverting the frontend deploy; localStorage keys remain harmless if we change or remove them later.

## Open Questions

- None for MVP. Optional follow-up: respect `prefers-color-scheme` when there is no stored preference (e.g. default to dark only when no preference and no system preference, or use system as default and store overrides).
