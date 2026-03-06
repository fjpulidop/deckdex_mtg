# Design: Deck API Route Tests

## Mock Strategy

Override FastAPI dependency `require_deck_repo` (not `get_deck_repo`) to inject a mock `DeckRepository`. This bypasses the PostgreSQL check entirely.

```python
from unittest.mock import MagicMock
from backend.api.routes.decks import require_deck_repo

mock_repo = MagicMock(spec=DeckRepository)
app.dependency_overrides[require_deck_repo] = lambda: mock_repo
```

## Test Data

Sample deck and card fixtures:

```python
SAMPLE_DECK = {"id": 1, "name": "Test Deck", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z", "card_count": 2, "commander_card_id": None}
SAMPLE_DECK_WITH_CARDS = {**SAMPLE_DECK, "cards": [
    {"id": 10, "name": "Lightning Bolt", "quantity": 1, "is_commander": False, "type": "Instant"},
    {"id": 20, "name": "Sol Ring", "quantity": 1, "is_commander": True, "type": "Artifact"},
]}
```

## Test Structure

Use pytest functions (not unittest.TestCase). Group by endpoint with descriptive names:

```
test_list_decks_returns_list
test_list_decks_empty
test_create_deck_returns_201
test_create_deck_default_name
test_get_deck_returns_with_cards
test_get_deck_not_found_returns_404
test_update_deck_name
test_update_deck_not_found_returns_404
test_delete_deck_returns_204
test_delete_deck_not_found_returns_404
test_add_card_to_deck_returns_201
test_add_card_not_in_collection_returns_404
test_add_card_deck_not_found_returns_404
test_set_commander_updates_deck
test_set_commander_not_found_returns_404
test_remove_card_returns_204
test_remove_card_not_found_returns_404
test_501_when_no_postgres (override require_deck_repo to raise HTTPException 501)
```

## Fixture: deck_client

Module-scoped fixture that creates TestClient with both auth and deck_repo overrides:

```python
@pytest.fixture(scope="module")
def deck_client():
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[require_deck_repo] = lambda: mock_repo
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client, mock_repo
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)
```

Each test configures mock_repo return values for its specific scenario.
