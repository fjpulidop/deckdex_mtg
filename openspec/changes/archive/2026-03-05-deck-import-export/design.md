## Context

The deck builder currently supports adding cards one at a time via the card picker modal (searches the user's collection, select + confirm). There is no bulk path in or out.

Existing infrastructure this change builds on:
- `deckdex/importers/mtgo.py` — parses `"<qty> <name>"` lines, skips `//` comments and blanks. Uses `ParsedCard(name, set_name, quantity)`.
- `deckdex/importers/base.py` — `ParsedCard` TypedDict. `detect_format()` for collection importers.
- `deckdex/storage/deck_repository.py` — `add_card(deck_id, card_id, quantity, is_commander, user_id)`, `get_deck_with_cards()`. Card resolution requires knowing the `card_id` — there is no name-to-id lookup method yet.
- `backend/api/routes/decks.py` — existing CRUD, thin routes delegating to `DeckRepository`.
- `frontend/src/components/DeckDetailModal.tsx` — header row with "Add card" and "Delete Deck" buttons. Import and Export buttons go in the same row.

## Goals / Non-Goals

**Goals:**
- Export deck to clipboard as MTGO-style text, grouped by section headers, pure client-side
- Import deck from pasted text: parse → resolve against user's collection → add matched → report unmatched
- Keep the import endpoint synchronous and stateless

**Non-Goals:**
- Fuzzy matching or Scryfall resolution (out of scope — user needs the card in their collection)
- Sideboard as a separate tracked concept
- CSV or other format support
- Async job for import

## Decisions

### 1. Export is entirely client-side

The `DeckWithCards` response already contains all card data needed to produce the text format: `name`, `quantity`, `is_commander`, `type` (for section grouping). No new backend endpoint required.

Export format:
