## Why

The Deck Builder has no way to move deck lists in or out of DeckDex. Users build decks externally (Moxfield, MTGO, Arena, text editors) and want to bring them in. They also want to share or back up their decks in the universal text format every MTG tool understands. Without import/export, the deck builder is an island.

## What Changes

- **Export**: A button in DeckDetailModal copies the current deck to the clipboard as plain text (MTGO/Arena format): one line per card entry (`<qty> <name>`), grouped by section with `//Commander`, `//Mainboard`, `//Sideboard` headers. No backend required — pure client-side serialization.
- **Import**: An "Import deck" button in DeckDetailModal opens a textarea modal where the user pastes a deck list. The frontend sends the raw text to a new backend endpoint `POST /api/decks/{id}/import`, which parses the text, resolves card names against the user's own collection (not the global catalog), and returns matched and unmatched results. The UI shows the results: matched cards are added to the deck; unmatched cards are flagged with the names so the user knows what was skipped.
- **Backend endpoint**: `POST /api/decks/{id}/import` — accepts `{ text: string }`, parses MTGO-style text (quantity + name per line, optional `//Section` headers), resolves each name against the user's collection via case-insensitive exact match, adds matched cards to the deck, and returns a summary with matched/unmatched lists.

## Non-goals

- Fuzzy name resolution or Scryfall lookups — resolution is strictly against the user's own collection (cards they own). Cards not in the collection are flagged, not auto-added.
- Support for CSV, Moxfield CSV, TappedOut formats — text/MTGO format only for MVP.
- Sideboard as a separate tracked entity — sideboard cards can be imported but are treated as regular mainboard cards (no separate sideboard concept in the current data model).
- Undo/rollback — import adds cards atomically; user can remove them individually if needed.
- Async/job-based import — collection sizes in decks are small (<100 cards); sync is fine.

## Capabilities

### Modified Capabilities
- `decks`: New endpoint `POST /api/decks/{id}/import` added to the deck router.
- `deck-builder-ui`: DeckDetailModal gains Export (clipboard) and Import (modal + textarea) actions.
- `web-api-backend`: Import endpoint added under `/api/decks`.

## Impact

- **Core (`deckdex/`)**: New parser `deckdex/importers/deck_text.py` for deck list text format (MTGO-style with optional section headers). No changes to existing importers.
- **Backend**: New route in `backend/api/routes/decks.py`. New Pydantic models for request/response. Resolution logic directly in the route (thin — no separate service needed given the simplicity of exact-match-against-collection).
- **Frontend**: `DeckDetailModal` gains two new buttons and a new `DeckImportModal` component. New API client methods for the import endpoint.
- **No DB schema changes**. No migrations required.
