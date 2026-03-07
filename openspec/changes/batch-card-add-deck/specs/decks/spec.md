# Delta spec: Decks — Batch Card Add

Base spec: `openspec/specs/decks/spec.md`

## ADDED Requirement: Batch add cards to a deck

The system SHALL expose `POST /api/decks/{id}/cards/batch` (JSON body: `{ "card_ids": [int, ...] }`). The endpoint SHALL:

- Accept a list of card IDs (integers) in a single request.
- Validate each ID against the authenticated user's collection in a single DB query.
- Add all valid cards to the deck in a single Postgres transaction (quantity=1, is_commander=false), using `ON CONFLICT DO UPDATE SET quantity = quantity + 1` when a card is already present.
- Return HTTP 200 with a response containing:
  - `added`: list of card IDs successfully added.
  - `not_found`: list of card IDs absent from the user's collection (not added).
  - `deck`: the full updated deck with cards (same shape as `GET /api/decks/{id}`).
- Return HTTP 404 if the deck does not exist or does not belong to the authenticated user.
- Return HTTP 501 if Postgres is not configured (same as all other deck endpoints).
- An empty `card_ids` list SHALL return 200 with the current deck state and no DB writes.
- The endpoint SHALL NOT return 404 for individual missing card IDs — those are reported in `not_found`.

### Scenario: Batch add all valid cards

- **WHEN** the client calls `POST /api/decks/{id}/cards/batch` with a list of card IDs all present in the user's collection
- **THEN** all cards are added (or their quantity incremented), the response contains `added` = all provided IDs, `not_found` = [], and the updated deck

### Scenario: Batch add with some invalid cards

- **WHEN** the client calls `POST /api/decks/{id}/cards/batch` with a mix of valid and invalid (not in collection) card IDs
- **THEN** only the valid cards are added, `added` contains only the valid IDs, `not_found` contains the invalid IDs, and the response is HTTP 200 (not 404)

### Scenario: Batch add to non-existent deck

- **WHEN** the client calls `POST /api/decks/{id}/cards/batch` with a deck ID that does not exist or belongs to another user
- **THEN** the API returns HTTP 404 and no cards are added

### Scenario: Batch add with empty card_ids

- **WHEN** the client calls `POST /api/decks/{id}/cards/batch` with `{ "card_ids": [] }`
- **THEN** the API returns HTTP 200 with the current deck state and `added` = [], `not_found` = [], with no DB writes

## CHANGED Behaviour: Single-card picker uses batch endpoint

The deck card picker UI (multi-select from collection) SHALL call the batch endpoint in a single HTTP request rather than N sequential single-add requests. The existing `POST /api/decks/{id}/cards` single-card endpoint is unchanged and remains available.
