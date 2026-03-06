# Delta Spec: Deck API Route Tests

Target spec file: `openspec/specs/api-tests/spec.md`

## Additions

### Requirement: Deck CRUD endpoint tests

The test suite SHALL include tests for all deck management endpoints using mocked DeckRepository (no real database). Tests SHALL use pytest fixtures from `tests/conftest.py` pattern (not unittest.TestCase).

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
