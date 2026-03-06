# Decks (backend)

Persistence and API for decks and deck–card membership. Decks reference cards from the existing collection by card id. Optional commander designation for display.

## ADDED Requirements

### Requirement: Decks are persisted when Postgres is available

The system SHALL store decks and deck–card associations in Postgres when DATABASE_URL (or config) is set. Deck entities SHALL have at least: id, name, created_at, updated_at. Deck–card associations SHALL have: deck_id, card_id, quantity; and SHALL support an optional commander designation (e.g. is_commander flag or deck.commander_card_id).

#### Scenario: Create deck with Postgres

- **WHEN** the backend has Postgres configured and receives a valid request to create a deck (e.g. POST with name)
- **THEN** a new deck row is stored and the API returns the created deck (id, name, created_at, updated_at)

#### Scenario: Decks unavailable without Postgres

- **WHEN** the backend has no Postgres (e.g. collection from Sheets only) and a deck endpoint is called
- **THEN** the API SHALL return an error (e.g. 501) or a clear message that deck features require Postgres

### Requirement: Deck CRUD and list API

The system SHALL expose REST endpoints under /api/decks: GET /api/decks (list all decks), POST /api/decks (create deck; body: name), GET /api/decks/{id} (single deck with cards; 404 if not found), PATCH /api/decks/{id} (update deck e.g. name; 404 if not found), DELETE /api/decks/{id} (delete deck and its deck_cards; 404 if not found).

#### Scenario: List decks

- **WHEN** client calls GET /api/decks
- **THEN** the API returns a list of decks (each with id, name, created_at, updated_at; MAY include card count or embedded cards)

#### Scenario: Get single deck with cards

- **WHEN** client calls GET /api/decks/{id} with a valid deck id
- **THEN** the API returns the deck and its cards (full card payload for each deck_card so the UI can display name, type, image id, etc.)

#### Scenario: Delete deck

- **WHEN** client calls DELETE /api/decks/{id} with a valid deck id
- **THEN** the deck and all its deck_card rows are removed and the API returns 204 (or success)

### Requirement: Add and remove cards from a deck

The system SHALL expose endpoints to add and remove cards from a deck: POST /api/decks/{id}/cards (body: card_id, optional quantity, optional is_commander) and DELETE /api/decks/{id}/cards/{card_id} (or equivalent) to remove one card from the deck. Card_id SHALL refer to an existing card in the collection; otherwise 404.

#### Scenario: Add card to deck

- **WHEN** client calls POST /api/decks/{id}/cards with a valid deck id and a card_id that exists in the collection
- **THEN** the card is associated with the deck (and optional is_commander stored) and the API returns success (e.g. 201 or 200 with updated deck/cards)

#### Scenario: Add card that does not exist in collection

- **WHEN** client calls POST /api/decks/{id}/cards with a card_id that is not in the collection
- **THEN** the API returns 404 (or 400) and does not add the card

#### Scenario: Remove card from deck

- **WHEN** client calls DELETE /api/decks/{id}/cards/{card_id} (or equivalent) for a card that is in the deck
- **THEN** that deck_card association is removed and the API returns success (e.g. 204)

### Requirement: Set commander (PATCH deck card)

The system SHALL expose PATCH /api/decks/{id}/cards/{card_id} with body { is_commander?: boolean }. When is_commander is true, that deck_card SHALL be set as commander and all other deck_cards for that deck SHALL have is_commander set to false. The card_id SHALL belong to the deck; otherwise 404.

#### Scenario: Set card as commander

- **WHEN** client calls PATCH /api/decks/{id}/cards/{card_id} with body { is_commander: true } for a card that is in the deck
- **THEN** that card is marked as commander and any other commander in the deck is unset; API returns success (e.g. 200 with updated deck or 204)

### Requirement: Import deck from text

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
