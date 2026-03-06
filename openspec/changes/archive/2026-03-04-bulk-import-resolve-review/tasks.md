## 1. Backend — Resolve Service

- [x] 1.1 Create `backend/api/services/resolve_service.py` with `ResolveService` class: takes parsed cards, resolves each against catalog (exact → fuzzy) then Scryfall autocomplete fallback. Returns list of `ResolvedCard` dicts with `original_name`, `quantity`, `set_name`, `status`, `resolved_name`, `suggestions`. Cap Scryfall lookups at 50 unresolved cards.
- [x] 1.2 Add Pydantic response models for the resolve endpoint in `import_routes.py` or a shared models file: `ResolvedCardItem` and `ResolveResponse` (format, total, matched_count, unresolved_count, cards).

## 2. Backend — Resolve Endpoint

- [x] 2.1 Add `POST /api/import/resolve` route in `import_routes.py`. Accept file (UploadFile) or text (Form). Parse using existing `_parse_file` / MTGO parser. Call `ResolveService`. Return `ResolveResponse`. Rate limit: 5/minute.
- [x] 2.2 Extend `POST /api/import/external` to accept a JSON body with `cards` array + `mode` as an alternative to file/text upload. Parse JSON cards into `ParsedCard` list and proceed with existing import flow.

## 3. Frontend — API Client

- [x] 3.1 Add `importResolve(file?: File, text?: string)` method to `api/client.ts` that calls `POST /api/import/resolve` and returns the resolve response.
- [x] 3.2 Add `importExternalFromCards(cards: ParsedCard[], mode: string)` method to `api/client.ts` that sends corrected card list as JSON body to `POST /api/import/external`.

## 4. Frontend — Review Step UI

- [x] 4.1 Restructure `Import.tsx` wizard from 5 steps to 6: upload → resolve → review → mode → progress → result. Update step type, step indicator, and navigation logic. Replace preview step with resolve.
- [x] 4.2 Build the review step UI: summary bar (matched count / unresolved count), collapsed matched cards section, unresolved cards section with per-card suggestion radio buttons, manual input field, and skip option.
- [x] 4.3 Add manual name input with autocomplete dropdown using existing `GET /api/cards/suggest?q=` endpoint, debounced at 300ms.
- [x] 4.4 Add bulk actions: "Accept all suggestions" (uses first suggestion for each) and "Skip all unresolved" buttons.
- [x] 4.5 Wire the "Continue" button to build corrected `ParsedCard[]` from review state and pass it to the import step via `importExternalFromCards`.

## 5. i18n

- [x] 5.1 Add translation keys for the review step: summary text, suggestion labels, manual input placeholder, skip/accept buttons, bulk action buttons.
