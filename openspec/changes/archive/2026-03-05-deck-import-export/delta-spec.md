## Target spec: `openspec/specs/decks/spec.md`

### ADDED Requirement: Import deck from text

The system SHALL expose `POST /api/decks/{id}/import` (JSON body: `{ "text": string }`). The endpoint SHALL parse the text as MTGO-style deck list (lines: `<qty> <name>`; lines starting with `//` treated as section headers or skipped; blank lines skipped). Cards under a `//Commander` section header SHALL be flagged as commander. Each parsed card name SHALL be resolved against the authenticated user's collection via case-insensitive exact match. Matched cards SHALL be added to the deck (quantity and is_commander preserved). Unmatched cards SHALL NOT be added. The response SHALL include `imported_count`, `skipped_count`, a `skipped` list (name, quantity, reason), and the full updated deck (`DeckWithCards`). The endpoint SHALL require authentication and scope resolution to the authenticated user's collection. It SHALL return 404 if the deck does not exist or does not belong to the user. It SHALL return 501 if Postgres is not configured.

#### Scenario: Import matched cards

- **WHEN** the user calls `POST /api/decks/{id}/import` with text containing card names that exist in their collection
- **THEN** those cards are added to the deck, `imported_count` equals the number added, `skipped_count` is 0, and the updated deck is returned

#### Scenario: Import with unmatched cards

- **WHEN** the user calls `POST /api/decks/{id}/import` with text containing card names not in their collection
- **THEN** matched cards are added; unmatched cards appear in `skipped` with `reason: "not_in_collection"`; `skipped_count` reflects the number skipped

#### Scenario: Import with Commander section

- **WHEN** the text contains a `//Commander` section header followed by a card line
- **THEN** that card is added to the deck with `is_commander=true` (if it exists in the collection)

#### Scenario: Import to non-existent deck

- **WHEN** the user calls `POST /api/decks/{id}/import` with a deck id that does not exist or belongs to another user
- **THEN** the API returns HTTP 404

---

## Target spec: `openspec/specs/deck-builder-ui/spec.md`

### ADDED Requirement: Export deck to clipboard

The deck detail modal SHALL provide an "Export" button in the header action row. When clicked, the system SHALL serialize the current deck to MTGO-style plain text (one line per card: `<qty> <name>`; sections prefixed with `//Commander` and `//Mainboard`) and copy it to the clipboard. After a successful copy, the button SHALL briefly display a "Copied!" label (approximately 2 seconds) as feedback before reverting.

#### Scenario: Export copies to clipboard

- **WHEN** the user clicks the Export button in the deck detail modal
- **THEN** the deck list is formatted as MTGO-style text and copied to the clipboard, and the button briefly shows "Copied!" feedback

### ADDED Requirement: Import deck from text modal

The deck detail modal SHALL provide an "Import" button in the header action row. When clicked, a modal opens with a textarea where the user can paste a deck list (MTGO/Arena text format). The user SHALL be able to submit the pasted text to import matched cards into the current deck. After import, the modal SHALL display a result summary: number of cards imported, and a list of any card names that were skipped (not found in collection). The user SHALL be able to close the import modal without importing (Cancel or Escape).

#### Scenario: Open import modal

- **WHEN** the user clicks the Import button in the deck detail modal
- **THEN** the import modal opens with an empty textarea and an Import button

#### Scenario: Successful import with skipped cards

- **WHEN** the user pastes a deck list and submits
- **THEN** matched cards (found in user's collection) are added to the deck, skipped cards (not in collection) are shown by name with a "not in collection" note, and the import count is displayed

#### Scenario: Cancel import

- **WHEN** the user closes the import modal without submitting (Cancel or Escape)
- **THEN** no cards are added and the deck detail modal remains open unchanged
