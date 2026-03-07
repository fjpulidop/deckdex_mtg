## Why

The Settings page (`frontend/src/pages/Settings.tsx`) is currently a redirect stub that sends users back to `/dashboard`. All settings functionality exists in `SettingsModal.tsx` but is only accessible via the user dropdown in the Navbar. Users navigating directly to `/settings` get bounced away, providing a broken UX.

## What Changes

- **Convert `Settings.tsx` from redirect stub to a full page component**: Remove the `<Navigate>` redirect and implement the full settings UI as a page.
- **Inline settings content**: Extract the 3 settings sections (Scryfall credentials, External APIs toggle, Quick Import) from `SettingsModal.tsx` into the Settings page, following Dashboard.tsx layout patterns (container, header, content sections).
- **No new API endpoints**: All API calls (`getScryfallCredentials`, `setScryfallCredentials`, `getExternalApisSettings`, `updateExternalApisSettings`, `importFromFile`) already exist and work.
- **Reuse existing i18n keys**: All translation keys under `settings.*` already exist in `en.json` and `es.json`.

## Non-goals

- Modifying `SettingsModal.tsx` (it remains functional in the Navbar dropdown)
- Adding new settings sections or API endpoints
- Backend changes of any kind
- Extracting shared logic into a reusable hook (unnecessary complexity for this scope)

## Capabilities

### Modified Capabilities
- `web-dashboard-ui`: Convert Settings page from redirect stub to full page with 3 settings sections matching SettingsModal functionality.

## Impact

- **Frontend only**: No backend or core changes.
- **Modified file**: `frontend/src/pages/Settings.tsx`
- **No new files**, no new dependencies
- **No API changes**, no migration required
- **TypeScript strict**: All new code must pass `tsc --noEmit`
