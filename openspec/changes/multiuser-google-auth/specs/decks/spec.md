## MODIFIED Requirements

### Requirement: Decks are persisted when Postgres is available
The system SHALL store decks and deck–card associations in Postgres when DATABASE_URL (or config) is set. Deck entities SHALL have at least: id, name, user_id, created_at, updated_at. Deck–card associations SHALL have: deck_id, card_id, quantity; and SHALL support an optional commander designation (e.g. is_commander flag or deck.commander_card_id). All deck queries SHALL filter by the authenticated user's `user_id`.

#### Scenario: Create deck with Postgres
- **WHEN** the backend has Postgres configured and receives a valid request to create a deck (e.g. POST with name) from an authenticated user
- **THEN** a new deck row is stored with `user_id` set to the authenticated user's ID and the API returns the created deck (id, name, created_at, updated_at)

#### Scenario: Decks unavailable without Postgres
- **WHEN** the backend has no Postgres (e.g. collection from Sheets only) and a deck endpoint is called
- **THEN** the API SHALL return an error (e.g. 501) or a clear message that deck features require Postgres

### Requirement: Deck CRUD and list API
The system SHALL expose REST endpoints under /api/decks: GET /api/decks (list all decks for the authenticated user), POST /api/decks (create deck; body: name), GET /api/decks/{id} (single deck with cards; 404 if not found or not owned by user), PATCH /api/decks/{id} (update deck e.g. name; 404 if not found or not owned), DELETE /api/decks/{id} (delete deck and its deck_cards; 404 if not found or not owned).

#### Scenario: List decks
- **WHEN** an authenticated client calls GET /api/decks
- **THEN** the API returns a list of decks belonging to that user (each with id, name, created_at, updated_at; MAY include card count or embedded cards)

#### Scenario: Get single deck with cards
- **WHEN** an authenticated client calls GET /api/decks/{id} with a valid deck id that belongs to them
- **THEN** the API returns the deck and its cards (full card payload for each deck_card so the UI can display name, type, image id, etc.)

#### Scenario: Get deck owned by another user
- **WHEN** an authenticated client calls GET /api/decks/{id} with a deck id belonging to another user
- **THEN** the API SHALL return 404

#### Scenario: Delete deck
- **WHEN** an authenticated client calls DELETE /api/decks/{id} with a valid deck id that belongs to them
- **THEN** the deck and all its deck_card rows are removed and the API returns 204 (or success)
