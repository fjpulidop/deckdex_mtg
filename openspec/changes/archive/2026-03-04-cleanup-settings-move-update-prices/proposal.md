## Why

Settings has accumulated actions that belong closer to the data they affect. The "Go to import" button is now redundant (Import List modal exists in the dashboard toolbar). Process Cards is no longer needed as the collection workflow has changed. Update Prices is more discoverable in the dashboard toolbar where users actively manage their collection.

## What Changes

- **Settings: Remove "Go to import" button** from Import Collection section. Keep the Quick Import (CSV/JSON) as the section's direct content.
- **Settings: Remove entire Deck Actions section** (Process Cards + Update Prices). The section heading and `ActionButtons` component are removed from SettingsModal.
- **Dashboard: Add "Update Prices" button** to CardTable toolbar as a tertiary action (slate/gray outline). Uses `useTriggerPriceUpdate()` hook and registers job via `useActiveJobs`. Shows "Starting..." while pending.
- Add i18n key `cardTable.updatePrices` for en/es.

## Non-goals

- Removing the ActionButtons component itself (may still be used elsewhere or can be cleaned up later)
- Changing the Quick Import functionality
- Modifying the Update Prices backend behavior

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `web-dashboard-ui`: Update Prices button added to CardTable toolbar; Settings sections reorganized

## Impact

- `frontend/src/components/SettingsModal.tsx` — remove "Go to import" button and Deck Actions section
- `frontend/src/components/CardTable.tsx` — add `onUpdatePrices` prop + tertiary button
- `frontend/src/pages/Dashboard.tsx` — wire Update Prices handler with `useTriggerPriceUpdate`
- `frontend/src/locales/en.json`, `es.json` — new i18n key
