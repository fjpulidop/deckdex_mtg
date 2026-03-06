## 1. Core — Deck text parser

- [ ] 1.1 Create `deckdex/importers/deck_text.py`. Export a function `parse_deck_text(text: str) -> List[DeckParsedCard]` where `DeckParsedCard` is a TypedDict with `name: str`, `quantity: int`, `is_commander: bool`. Parse MTGO-style lines (`<qty> <name>`). Track `//Commander` section headers to set `is_commander=True` on subsequent cards. Skip blank lines and unrecognized `//` headers. Reuse the `_LINE_RE` pattern from `deckdex/importers/mtgo.py`.
  - Files: `deckdex/importers/deck_text.py`
  - Acceptance: `parse_deck_text("//Commander\n1 Atraxa, Praetors' Voice\n//Mainboard\n4 Lightning Bolt")` returns two entries, first with `is_commander=True`, second with `is_commander=False`.

## 2. Core — DeckRepository name lookup

- [ ] 2.1 Add `find_card_ids_by_names(names: List[str], user_id: int) -> Dict[str, int]` to `DeckRepository` in `deckdex/storage/deck_repository.py`. Execute a single query: `SELECT id, name FROM cards WHERE user_id = :user_id AND LOWER(name) = ANY(:names)`. Return dict mapping lowercase name → card_id. When `user_id` is None, omit the user filter (fallback for legacy usage). If multiple rows match the same lowercase name, take the first by id.
  - Files: `deckdex/storage/deck_repository.py`
  - Acceptance: Given a user with "Lightning Bolt" in their collection, `find_card_ids_by_names(["lightning bolt"], user_id)` returns `{"lightning bolt": <card_id>}`.

## 3. Backend — Import endpoint

- [ ] 3.1 Add Pydantic models to `backend/api/routes/decks.py`: `DeckImportBody(text: str)`, `DeckImportSkippedCard(name: str, quantity: int, reason: str)`, `DeckImportResponse(imported_count: int, skipped_count: int, skipped: List[DeckImportSkippedCard], deck: dict)`.
  - Files: `backend/api/routes/decks.py`

- [ ] 3.2 Add route `POST /api/decks/{deck_id}/import` in `backend/api/routes/decks.py`. Steps: (a) verify deck exists and belongs to user (404 otherwise); (b) parse `body.text` with `parse_deck_text()`; (c) call `repo.find_card_ids_by_names()` with all unique names, lowercased; (d) for each parsed card: if name found in result dict, call `repo.add_card()` with quantity and is_commander, accumulate to `imported_count`; else append to `skipped`; (e) if any card had `is_commander=True` and was matched, call `repo.set_commander()` for that card; (f) fetch updated deck via `repo.get_deck_with_cards()` and return `DeckImportResponse`.
  - Files: `backend/api/routes/decks.py`
  - Acceptance: POST with `{"text": "1 Lightning Bolt"}` to a deck where the user owns Lightning Bolt returns `imported_count: 1`, `skipped_count: 0`, and an updated deck containing Lightning Bolt.

## 4. Frontend — API client

- [ ] 4.1 Add `importDeckText(deckId: number, text: string): Promise<DeckImportResponse>` to `api/client.ts`. POST JSON body `{ text }` to `/api/decks/{deckId}/import`. Define `DeckImportSkippedCard` and `DeckImportResponse` interfaces.
  - Files: `frontend/src/api/client.ts`
  - Acceptance: TypeScript compiles with no errors. `DeckImportResponse` has `imported_count`, `skipped_count`, `skipped: DeckImportSkippedCard[]`, `deck: DeckWithCards`.

## 5. Frontend — DeckImportModal component

- [ ] 5.1 Create `frontend/src/components/DeckImportModal.tsx`. Props: `deckId: number`, `onClose: () => void`, `onImported: (result: DeckImportResponse) => void`. States: `idle` (textarea input), `loading` (spinner, disabled form), `result` (show summary + skipped list). Use `useMutation` from TanStack Query wrapping `api.importDeckText`. On success, call `onImported(result)`. On error, show error message inline. Textarea placeholder: `"1 Lightning Bolt\n2 Counterspell\n//Commander\n1 Atraxa, Praetors' Voice"`. Cancel button always visible (calls `onClose`). Close on Escape key.
  - Files: `frontend/src/components/DeckImportModal.tsx`
  - Acceptance: Component renders a textarea, Import and Cancel buttons. On submit, calls `api.importDeckText`. On result, shows `"{n} cards imported"` and scrollable list of skipped names if any.

## 6. Frontend — DeckDetailModal: Export and Import buttons

- [ ] 6.1 Add export logic to `DeckDetailModal`. Add `copyFeedback` boolean state (default false). Add `handleExport` callback that serializes `deck.cards` into MTGO text (Commander section first if any `is_commander` card exists, then `//Mainboard` for remaining cards, lines formatted as `"<qty> <name>"`), calls `navigator.clipboard.writeText()`, sets `copyFeedback(true)`, and resets to false after 2000ms via `setTimeout`. Add "Export" button to the header action row (before "Add card"), label switches to `t('deckDetail.copied')` when `copyFeedback` is true.
  - Files: `frontend/src/components/DeckDetailModal.tsx`
  - Acceptance: Clicking Export writes the deck list to clipboard. Button label shows "Copied!" for ~2 seconds.

- [ ] 6.2 Add import flow to `DeckDetailModal`. Add `importOpen` boolean state. Add "Import" button to header action row (between Export and "Add card"). When clicked, sets `importOpen(true)`. Render `<DeckImportModal>` when `importOpen` is true. On `onImported` callback: update the `['deck', deckId]` query cache with the returned deck (`queryClient.setQueryData`), call `queryClient.invalidateQueries({ queryKey: ['decks'] })` to refresh the deck list tile counts, set `importOpen(false)`.
  - Files: `frontend/src/components/DeckDetailModal.tsx`
  - Acceptance: Clicking Import opens the modal. After a successful import, the deck detail list updates without a separate refetch round-trip.

## 7. i18n

- [ ] 7.1 Add translation keys to `frontend/src/locales/en.json` and `frontend/src/locales/es.json`:
  - `deckDetail.export`: "Export"
  - `deckDetail.copied`: "Copied!"
  - `deckDetail.import`: "Import"
  - `deckImport.title`: "Import Deck List"
  - `deckImport.placeholder`: "Paste your deck list here...\n1 Lightning Bolt\n2 Counterspell"
  - `deckImport.submit`: "Import"
  - `deckImport.cancel`: "Cancel"
  - `deckImport.loading`: "Importing..."
  - `deckImport.success`: "{{count}} cards imported"
  - `deckImport.skippedTitle`: "Not in your collection ({{count}}):"
  - `deckImport.done`: "Done"
  - `deckImport.notInCollection`: "not in collection"
  - Files: `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

## 8. Tests

- [ ] 8.1 Add unit test for `parse_deck_text()` in `tests/` covering: standard lines, Commander section, mixed sections, blank lines, comment-only lines, quantity > 1.
  - Files: `tests/test_deck_text_parser.py`

- [ ] 8.2 Add unit test for `DeckRepository.find_card_ids_by_names()` using an in-memory SQLite fixture or mocked engine. Verify case-insensitive match and multi-name batching.
  - Files: `tests/test_deck_repository.py` (new or extend existing)
