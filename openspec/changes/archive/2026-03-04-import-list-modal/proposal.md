## Why

The "Import list" button currently navigates away from the dashboard to `/import`. This breaks the user's flow — they lose their place in the collection. A modal (like "Add card") keeps the user in context and provides a quick entry point for bulk imports, with the full wizard only appearing for the review/correction steps.

## What Changes

- Replace the `onImport` navigation callback with a modal toggle (same pattern as `cardModal` / `CardFormModal`)
- Create an `ImportListModal` component with file/text tab toggle:
  - **File tab**: drag-and-drop zone + file picker (`.csv`, `.txt`)
  - **Text tab**: textarea for pasting card lists
- On submit, call `api.importResolve()` and navigate to `/import` at the review step, passing resolved data via React Router `state`
- Update the Import page to accept pre-resolved data from route state and skip upload/resolve steps
- Add i18n keys for modal UI elements (en/es)

## Non-goals

- Changing the Import wizard itself (steps 3–6 stay the same)
- Removing the direct `/import` route (it still works standalone)
- Adding new API endpoints (reuses existing `importResolve`)

## Capabilities

### New Capabilities

_(none — extends existing UI with a modal component)_

### Modified Capabilities

- `web-dashboard-ui`: Import list button opens a modal instead of navigating; Import page accepts pre-resolved data from route state

## Impact

- `frontend/src/components/ImportListModal.tsx` — new component
- `frontend/src/pages/Dashboard.tsx` — modal state + toggle
- `frontend/src/components/CardTable.tsx` — no change (already has `onImport` prop)
- `frontend/src/pages/Import.tsx` — accept route state to skip upload step
- `frontend/src/locales/en.json`, `es.json` — new i18n keys
