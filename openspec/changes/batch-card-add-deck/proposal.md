# Proposal: Batch Card Add for Decks + Currency Fix

## What

Add a batch card-add endpoint (`POST /api/decks/{id}/cards/batch`) that accepts a list of card IDs in a single HTTP request, and update the frontend card picker to use it. Additionally fix two small but related UI defects: the hardcoded EUR currency in `DeckDetailModal` and the zero test coverage on the deck import endpoint.

## Why

### N+1 sequential request pattern in DeckCardPickerModal

`DeckCardPickerModal.tsx` lines 86–88 iterate over selected card IDs and fire one HTTP `POST /api/decks/{id}/cards` per card, sequentially (`await` inside a `for` loop). A user who selects 10 cards from the picker produces 10 round trips to the backend, each requiring its own TCP/TLS overhead and a separate Postgres transaction. For realistic deck sizes (20–60 card selections at a time), this creates noticeable latency and hammers the DB with unnecessary transactions. A single batch endpoint collapses N round trips into 1.

### Hardcoded EUR currency in DeckDetailModal

`DeckDetailModal.tsx` line 22 hard-codes `currency: 'EUR'` in the `formatDeckCurrency` function regardless of user settings. This is inconsistent with the rest of the app, which stores and respects user currency preferences through the settings system.

### Zero test coverage on POST /api/decks/{id}/import

The import endpoint is the most complex deck endpoint (text parsing, name resolution, partial-match logic) yet has no tests in `tests/test_decks.py`. This is a coverage gap that should be closed alongside the batch work.

## Scope

**In scope:**
- New repository method `add_cards_batch()` in `deckdex/storage/deck_repository.py`
- New route `POST /api/decks/{id}/cards/batch` in `backend/api/routes/decks.py`
- New API client method `addCardsToDeckBatch()` in `frontend/src/api/client.ts`
- Updated `handleAdd` in `DeckCardPickerModal.tsx` to use the batch method
- Fix `formatDeckCurrency` in `DeckDetailModal.tsx` to use user-configured currency
- Backend tests for the batch endpoint in `tests/test_decks.py`
- Backend tests for the import endpoint in `tests/test_decks.py`

**Out of scope:**
- Changing quantity or is_commander semantics in the batch endpoint (defaults apply: qty=1, is_commander=false)
- Changing the single-card endpoint (kept for backward compat and direct use)
- Frontend unit tests (no React testing framework is set up)
- Any changes to the import endpoint logic

## Success criteria

1. Selecting 10 cards in the picker and clicking "Add to Deck" produces exactly 1 HTTP request (not 10).
2. The batch endpoint returns the full updated deck (same shape as single-card endpoint) on success.
3. Cards that do not exist in the user's collection are reported individually in the response; the endpoint does not 404 on the first failure but processes all IDs.
4. The deck total value in `DeckDetailModal` displays in the user's configured currency.
5. The import endpoint has at least 3 new tests covering: successful import, import with unmatched cards, and 404 on unknown deck.
6. All existing 19 tests in `tests/test_decks.py` and 7 tests in `tests/test_deck_repository.py` continue to pass.
