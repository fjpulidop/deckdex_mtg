## Context

The "Add card" button in `CardTable.tsx` is currently the only action in the table toolbar. The Import wizard (`/import`) is only reachable from the Settings modal. Users who want to bulk-import cards while browsing their collection have no direct path.

## Goals / Non-Goals

**Goals:**
- Add a secondary "Import list" button next to "Add card" in CardTable
- Navigate to `/import` on click
- Visually communicate secondary importance via outline/ghost styling

**Non-Goals:**
- Modifying the Import wizard itself
- Removing the Settings → Import link
- Adding any backend changes

## Decisions

### 1. Button placement: same toolbar row as "Add card"
Place the new button inside the same `div` that wraps "Add card", using a flex layout with a gap. This keeps both actions together and contextually grouped.

**Alternative considered:** Separate row or floating action button — rejected as over-engineered for a simple navigation shortcut.

### 2. Styling: indigo outline/ghost
Use `border border-indigo-600 text-indigo-600 bg-transparent hover:bg-indigo-50` (dark mode: `dark:border-indigo-400 dark:text-indigo-400 dark:hover:bg-indigo-950`). This creates clear visual hierarchy — green solid primary vs indigo outline secondary.

**Alternative considered:** Blue solid button — rejected because two solid colored buttons compete for attention.

### 3. Navigation via React Router
Use `useNavigate` from react-router-dom (already used in the codebase, e.g., SettingsModal). Pass `navigate` as a callback prop (`onImport`) from Dashboard to CardTable, following the same pattern as `onAdd`.

### 4. Prop-driven visibility
The button only renders when `onImport` callback is provided, mirroring the `onAdd` pattern. This keeps CardTable reusable.

## Risks / Trade-offs

- [Minimal risk] Two buttons in toolbar on small screens → mitigated by using `flex-wrap` and compact button sizing.
