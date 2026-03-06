## Why

The current import flow resolves card names during the background import job. Users only discover unrecognized cards after the import completes, with no way to correct them. Typos, alternate names, and format mismatches result in silently skipped cards. This is especially painful for large imports where re-importing after fixing a spreadsheet is tedious.

## What Changes

- **New resolve endpoint**: `POST /api/import/resolve` — takes a file or pasted text, parses it, and resolves each card name against the local catalog (fuzzy ILIKE) and Scryfall autocomplete. Returns per-card status: `matched`, `suggested`, or `not_found`, with up to 3 suggestions for unresolved cards.
- **New Review step in wizard UI**: Between upload and mode selection, a review screen shows matched vs. unresolved cards. For each unresolved card, the user can accept a suggestion, type a name manually (with autocomplete dropdown), or skip the card.
- **Corrected card list sent to existing import**: The frontend collects the user's corrections and sends the final clean `ParsedCard[]` list to the existing `/api/import/external` endpoint. No backend import logic changes.

## Non-goals

- Async/streaming resolve — sync with 30s timeout is sufficient for MVP.
- Column mapping UI — auto-detect remains as-is.
- Import history/undo.
- New file format support.

## Capabilities

### New Capabilities
- `import-resolve-review`: Card name resolution with user review before import. Covers the `/api/import/resolve` endpoint and the Review step UI in the import wizard.

### Modified Capabilities
- `web-api-backend`: New route `POST /api/import/resolve` added to the import router.
- `web-dashboard-ui`: Import page wizard gains a new Review step between upload and mode selection.

## Impact

- **Backend**: New route in `backend/api/routes/import_routes.py`. New service or helper for resolve logic (catalog + Scryfall). Dependencies: `deckdex/catalog/repository.py`, `deckdex/card_fetcher.py`.
- **Frontend**: `frontend/src/pages/Import.tsx` wizard restructured (6 steps). New API client methods for resolve endpoint. New autocomplete input component for manual correction.
- **No DB schema changes**. No breaking changes to existing endpoints.
