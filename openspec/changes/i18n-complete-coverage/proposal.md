## Why

The previous i18n coverage sweep (archived 2026-03-07) wired 8 components and fixed 2 locale bugs, but a second audit reveals 6 additional locations with hardcoded English strings that were missed. These include user-visible empty-state messages in insight renderer components, error fallback strings in catch blocks, and the `ErrorBoundary` class component which cannot use hooks and requires a different approach. The i18n spec requirement states that every user-visible string in `frontend/src/` must use a `t()` call — this change closes the remaining gaps.

## What Changes

- **InsightListRenderer.tsx**: Add `useTranslation()` and replace `'No items to display'` with a new key `insights.list.noItems`.
- **InsightTimelineRenderer.tsx**: Add `useTranslation()` and replace `'No timeline data available'` with `insights.timeline.noData`, and `'{count} cards'` inline string with `insights.timeline.cardCount`.
- **InsightComparisonRenderer.tsx**: Add `useTranslation()` and replace `aria-label` values `'Present'` / `'Missing'` with `insights.comparison.present` / `insights.comparison.missing`.
- **ErrorBoundary.tsx**: Convert to a functional component using `useTranslation()` and replace 3 hardcoded strings (`'Something went wrong'`, description text, `'Refresh Page'`) with new keys under `errorBoundary.*`.
- **Admin.tsx**: Replace fallback string `'Sync encountered an error'` and `'Failed to start sync'` in catch blocks with new keys `admin.syncEncounteredError` and `admin.failedToStartSync`.
- **DeckImportModal.tsx**: Replace `'Import failed'` fallback with `deckImport.importFailed` key.
- **Settings.tsx** and **SettingsModal.tsx**: Replace 4 catch-block fallback strings with new keys under `settings.errors.*`: `settings.errors.failedToSave`, `settings.errors.importFailed`, `settings.errors.failedToClear`, `settings.errors.failedToUpdate`.

All new keys are added to both `en.json` and `es.json`.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `i18n`: Closes remaining coverage gaps discovered by a second audit. The existing requirement "All hardcoded UI strings replaced with t() calls" is not yet fully met. This change brings coverage to 100% for all user-visible strings in `frontend/src/` components.

## Impact

- `frontend/src/components/insights/InsightListRenderer.tsx`
- `frontend/src/components/insights/InsightTimelineRenderer.tsx`
- `frontend/src/components/insights/InsightComparisonRenderer.tsx`
- `frontend/src/components/ErrorBoundary.tsx` (functional component rewrite)
- `frontend/src/pages/Admin.tsx`
- `frontend/src/components/DeckImportModal.tsx`
- `frontend/src/pages/Settings.tsx`
- `frontend/src/components/SettingsModal.tsx`
- `frontend/src/locales/en.json`
- `frontend/src/locales/es.json`

No API changes. No backend changes. No new dependencies.

## Non-goals

- Translating backend API error strings (explicitly excluded by the i18n spec).
- Adding new languages beyond en/es.
- Translating dynamic card data (card names, set names) from Scryfall.
- Translating `console.error()` log messages (developer-only, not user-visible).
