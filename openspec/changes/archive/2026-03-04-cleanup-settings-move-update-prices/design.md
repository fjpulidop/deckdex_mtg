## Context

The CardTable toolbar already has "Add card" (green, primary) and "Import list" (indigo outline, secondary). We're adding "Update Prices" as a tertiary action and cleaning up Settings by removing redundant/obsolete sections.

## Goals / Non-Goals

**Goals:**
- Remove "Go to import" button from Settings (keep Quick Import)
- Remove entire Deck Actions section from Settings
- Add "Update Prices" as a tertiary button in CardTable toolbar

**Non-Goals:**
- Deleting the ActionButtons component file
- Changing any backend behavior

## Decisions

### 1. Update Prices button styling: slate outline (tertiary)
Use `border border-gray-400 text-gray-600 bg-transparent hover:bg-gray-50` (dark: `dark:border-gray-500 dark:text-gray-400 dark:hover:bg-gray-800`). This creates a clear 3-tier visual hierarchy: green solid → indigo outline → slate outline.

### 2. CardTable receives `onUpdatePrices` + `updatingPrices` props
The `onUpdatePrices` callback triggers the price update. A separate `updatingPrices` boolean controls the disabled/loading state of the button. This follows the prop-driven pattern already used for `onAdd` and `onImport`.

### 3. Dashboard uses `useTriggerPriceUpdate` hook directly
Dashboard calls the hook, wires the mutate function and isPending state to CardTable. On success, registers the job via `addJob` from `useActiveJobs`. This avoids importing ActionButtons and keeps the logic minimal.

### 4. Settings cleanup: promote Quick Import
Remove the "Go to import" button and the wrapping `<details>` for Quick Import. The Quick Import file input becomes the direct content of the Import Collection section with its existing description.

## Risks / Trade-offs

- [Low risk] Removing Deck Actions from Settings means users must use the dashboard for Update Prices. This is the intended UX improvement.
