## Why

The Import wizard is only accessible from Settings, making it hard to discover. Users managing their collection in the dashboard should have a direct shortcut to bulk-import cards right next to the "Add card" button, where the action is contextually relevant.

## What Changes

- Add an "Import list" outline button next to "Add card" in the CardTable component
- Style it as secondary (indigo outline/ghost) so it doesn't compete with the primary green "Add card" button
- Button navigates to `/import` (existing Import wizard page)
- Add i18n keys for English ("Import list") and Spanish ("Importar lista")

## Non-goals

- No changes to the Import wizard itself
- No removal of the existing "Go to import" button in Settings

## Capabilities

### New Capabilities

_(none — this is a small UI addition to existing capabilities)_

### Modified Capabilities

- `web-dashboard-ui`: Adding a navigation shortcut button to the CardTable toolbar

## Impact

- `frontend/src/components/CardTable.tsx` — new button in toolbar
- `frontend/src/locales/en.json` — new i18n key
- `frontend/src/locales/es.json` — new i18n key
