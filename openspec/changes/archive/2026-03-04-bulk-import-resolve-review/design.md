## Context

The import wizard (`/import`) currently parses uploaded files/pasted text and sends cards directly to a background import job. Card name resolution (catalog lookup → Scryfall fallback) happens inside `ImporterService._run_import()`, coupled with DB writes. Users see unresolved cards only after the job completes, with no ability to correct them.

Existing infrastructure:
- `deckdex/catalog/repository.py` — `search_by_name(query)` does `ILIKE '%query%'` against `catalog_cards`
- `deckdex/card_fetcher.py` — `autocomplete(q)` calls Scryfall `/cards/autocomplete`, `_fuzzy_match_search()` calls `/cards/named?fuzzy=`
- `deckdex/importers/` — parsers for Moxfield, TappedOut, MTGO, generic CSV → `ParsedCard(name, set_name, quantity)`
- `backend/api/routes/import_routes.py` — `/preview` (parse + sample), `/external` (parse + background import)
- `frontend/src/pages/Import.tsx` — 5-step wizard: upload → preview → mode → progress → result

## Goals / Non-Goals

**Goals:**
- Decouple name resolution from DB writes so users can review and correct before importing
- Provide suggestions for unresolved cards (fuzzy catalog match + Scryfall autocomplete)
- Keep the resolve step synchronous and stateless for MVP simplicity

**Non-Goals:**
- Streaming/async resolve (sync with timeout is fine for typical collection sizes)
- Changing the import/enrichment job itself — the corrected card list feeds into the existing `/external` endpoint
- Column mapping UI or new format support

## Decisions

### 1. New endpoint `POST /api/import/resolve` in the import router

**Why a new endpoint instead of extending `/preview`**: Preview is lightweight (format + count + 5 samples). Resolve does catalog + Scryfall lookups per card — different cost profile and response shape. Keeping them separate avoids breaking the existing preview flow.

**Request**: Same as `/preview` — accepts `file` (UploadFile) or `text` (Form field).

**Response shape**:
```json
{
  "format": "moxfield",
  "total": 500,
  "matched_count": 488,
  "unresolved_count": 12,
  "cards": [
    {
      "original_name": "Lightning Bolt",
      "quantity": 4,
      "set_name": "M21",
      "status": "matched",
      "resolved_name": "Lightning Bolt",
      "suggestions": []
    },
    {
      "original_name": "Ligthning Bolt",
      "quantity": 2,
      "set_name": null,
      "status": "suggested",
      "resolved_name": null,
      "suggestions": ["Lightning Bolt", "Lightning Helix", "Lightning Strike"]
    },
    {
      "original_name": "Xyzzy Card",
      "quantity": 1,
      "set_name": null,
      "status": "not_found",
      "resolved_name": null,
      "suggestions": []
    }
  ]
}
```

**Alternative considered**: Return only unresolved cards (smaller payload). Rejected because the frontend needs the full list to build the final corrected `ParsedCard[]` for import.

### 2. Resolution logic lives in a new service: `backend/api/services/resolve_service.py`

**Layer**: Backend service (not core `deckdex/`). Uses `catalog_repo.search_by_name()` and `CardFetcher.autocomplete()` from core.

**Resolution algorithm per card**:
1. **Exact match**: `catalog_repo.search_by_name(name, limit=1)` — if result name matches exactly (case-insensitive) → `status: "matched"`
2. **Fuzzy catalog**: same `search_by_name` returns partial matches → take top 3 as suggestions → `status: "suggested"`
3. **Scryfall autocomplete** (if enabled and catalog gave no suggestions): `card_fetcher.autocomplete(name)` → top 3 → `status: "suggested"`
4. **Nothing** → `status: "not_found"`, empty suggestions

**Why not Scryfall fuzzy (`/cards/named?fuzzy=`)?** That endpoint returns full card data (heavy). We only need name suggestions at this stage. `autocomplete` is lighter and not rate-limited as aggressively.

### 3. Frontend wizard restructured: 6 steps

```
upload → resolve (loading) → review → mode → progress → result
```

The `preview` step is absorbed into `resolve` — the resolve response includes format and count (everything preview had plus resolution data). The step indicator updates from 5 to 6 circles.

**Review step UI**:
- Summary bar: "488 matched, 12 need attention"
- Matched cards section (collapsed by default, expandable)
- Unresolved cards section: each card shows original name, suggestions as radio buttons, manual input with autocomplete dropdown, and skip option
- Bulk actions: "Accept all suggestions" / "Skip all unresolved"

**Manual name input**: Uses existing `GET /api/cards/suggest?q=` endpoint (already wired to catalog autocomplete) for real-time suggestions as the user types. Debounced at 300ms.

### 4. Import flow after review

The frontend builds a corrected `ParsedCard[]` array:
- Matched cards: use `resolved_name`
- User-corrected cards: use the name the user selected/typed
- Skipped cards: excluded from the list

This array is sent to `POST /api/import/external` via a new API client method that accepts a pre-parsed card list (JSON body) instead of file/text. This requires a small backend addition: accept a JSON body with `cards[]` + `mode` as an alternative to file upload.

**Alternative considered**: Re-send the file with corrections encoded somehow. Rejected — unnecessarily complex. A JSON body of corrected cards is cleaner.

### 5. Rate limiting and timeout

- Resolve endpoint: `5/minute` rate limit (same as other import endpoints)
- Sync execution with 30s timeout via FastAPI/uvicorn defaults
- Scryfall calls only for unresolved cards (typically a small subset), so unlikely to hit Scryfall rate limits

## Risks / Trade-offs

- **Large imports with many unresolved cards**: If someone imports 5000 cards and 500 are unresolved, Scryfall autocomplete for 500 names could take ~50s (rate limit ~10/s). **Mitigation**: For MVP, cap Scryfall lookups at 50 unresolved cards; beyond that, mark remaining as `not_found` without suggestions. User can still type manually.
- **Catalog not populated**: If the catalog table is empty, all resolution falls to Scryfall or fails. **Mitigation**: This is an existing limitation. The resolve step makes it more visible, which is actually a UX improvement.
- **Payload size**: Returning all 500+ cards in the resolve response could be large. **Mitigation**: Typical collection imports are <2000 cards. At ~200 bytes per card entry, that's ~400KB — acceptable for sync JSON response.
