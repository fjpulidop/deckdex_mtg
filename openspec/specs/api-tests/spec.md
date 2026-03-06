# API Tests

Automated tests for backend API (health, stats, cards list) with mocked collection; no DB or Sheets. Tests SHALL be able to use shared helpers and fixtures from `tests/conftest.py` instead of duplicating boilerplate (TestClient setup, auth override, sample data).

### Requirements (compact)

- **Health:** GET /api/health → 200, body has service, version, status (e.g. "DeckDex MTG API", "0.1.0", "healthy").
- **Stats:** GET /api/stats with mocked collection: empty → total_cards 0, total_value 0, average_price 0, last_updated; non-empty → aggregates consistent with mock; with query params (rarity, set_name, etc.) → filtered subset only.
- **Cards list:** GET /api/cards with mock: empty → 200, []; non-empty → array consistent with mock; limit/offset → correct slice; filters → only matching cards (same semantics as stats).
- **Shared test infrastructure:** Existing tests pass unchanged after adding `conftest.py`. New API tests can use the `client` fixture or `make_test_client()` helper instead of repeating boilerplate.

### Requirement: Deck CRUD endpoint tests

The test suite SHALL include tests for all deck management endpoints using mocked DeckRepository (no real database). Tests SHALL use pytest fixtures with `dependency_overrides` per test class (setUp/tearDown), not module-level overrides.

#### Scenario: List decks returns array
- WHEN GET /api/decks/ is called with mocked repo returning 2 decks
- THEN response is 200 with a JSON array of 2 deck objects

#### Scenario: Create deck returns 201
- WHEN POST /api/decks/ is called with {"name": "My Deck"}
- THEN response is 201 and repo.create was called with name="My Deck"

#### Scenario: Get deck includes cards
- WHEN GET /api/decks/1 is called with mocked repo returning deck with cards
- THEN response is 200 with deck object containing cards array

#### Scenario: Get non-existent deck returns 404
- WHEN GET /api/decks/999 is called and repo returns None
- THEN response is 404

#### Scenario: Delete deck returns 204
- WHEN DELETE /api/decks/1 is called and repo.delete returns True
- THEN response is 204

### Requirement: Deck card management tests

#### Scenario: Add card to deck returns updated deck
- WHEN POST /api/decks/1/cards with {"card_id": 10} and repo.add_card returns True
- THEN response is 201 with updated deck

#### Scenario: Add card not in collection returns 404
- WHEN POST /api/decks/1/cards with {"card_id": 999} and repo.add_card returns False
- THEN response is 404 with "not found in collection" message

#### Scenario: Set commander updates deck
- WHEN PATCH /api/decks/1/cards/10 with {"is_commander": true}
- THEN repo.set_commander is called and response includes updated deck

#### Scenario: Remove card returns 204
- WHEN DELETE /api/decks/1/cards/10 and repo.remove_card returns True
- THEN response is 204

### Requirement: 501 when PostgreSQL unavailable

#### Scenario: All deck endpoints return 501 without postgres
- WHEN any deck endpoint is called and get_deck_repo returns None
- THEN response is 501 with message about Postgres requirement
