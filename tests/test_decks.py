"""Tests for deck API routes (backend/api/routes/decks.py).

Mocks require_deck_repo (FastAPI dependency) and get_current_user_id so no
real database is needed. All tests are pytest functions, not unittest.TestCase.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app
from backend.api.routes.decks import require_deck_repo
from deckdex.storage.deck_repository import DeckRepository

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_DECK = {
    "id": 1,
    "name": "Test Deck",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
    "card_count": 2,
    "commander_card_id": None,
}

SAMPLE_DECK_WITH_CARDS = {
    **SAMPLE_DECK,
    "cards": [
        {"id": 10, "name": "Lightning Bolt", "quantity": 1, "is_commander": False, "type": "Instant"},
        {"id": 20, "name": "Sol Ring", "quantity": 1, "is_commander": True, "type": "Artifact"},
    ],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def deck_client():
    """TestClient with mocked DeckRepository and auth.

    Yields (client, mock_repo). Each test is responsible for configuring
    mock_repo return values for its specific scenario.
    """
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[require_deck_repo] = lambda: mock_repo
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client, mock_repo
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)


# ---------------------------------------------------------------------------
# List / Create
# ---------------------------------------------------------------------------


def test_list_decks_returns_list(deck_client):
    client, mock_repo = deck_client
    mock_repo.list_all.return_value = [SAMPLE_DECK]

    response = client.get("/api/decks/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Test Deck"


def test_list_decks_empty(deck_client):
    client, mock_repo = deck_client
    mock_repo.list_all.return_value = []

    response = client.get("/api/decks/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_deck_returns_201(deck_client):
    client, mock_repo = deck_client
    mock_repo.create.return_value = SAMPLE_DECK

    response = client.post("/api/decks/", json={"name": "My Deck"})

    assert response.status_code == 201
    mock_repo.create.assert_called_with(name="My Deck", user_id=1)


def test_create_deck_default_name(deck_client):
    client, mock_repo = deck_client
    mock_repo.create.return_value = {**SAMPLE_DECK, "name": "Unnamed Deck"}

    response = client.post("/api/decks/", json={})

    assert response.status_code == 201
    mock_repo.create.assert_called_with(name="Unnamed Deck", user_id=1)


# ---------------------------------------------------------------------------
# Get / Update / Delete
# ---------------------------------------------------------------------------


def test_get_deck_returns_with_cards(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.get("/api/decks/1")

    assert response.status_code == 200
    data = response.json()
    assert "cards" in data
    assert len(data["cards"]) == 2


def test_get_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_deck_with_cards.return_value = None

    response = client.get("/api/decks/999")

    assert response.status_code == 404


def test_update_deck_name(deck_client):
    client, mock_repo = deck_client
    mock_repo.update_name.return_value = {**SAMPLE_DECK, "name": "Renamed Deck"}

    response = client.patch("/api/decks/1", json={"name": "Renamed Deck"})

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Deck"


def test_update_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.update_name.return_value = None

    response = client.patch("/api/decks/999", json={"name": "Ghost Deck"})

    assert response.status_code == 404


def test_delete_deck_returns_204(deck_client):
    client, mock_repo = deck_client
    mock_repo.delete.return_value = True

    response = client.delete("/api/decks/1")

    assert response.status_code == 204


def test_delete_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.delete.return_value = False

    response = client.delete("/api/decks/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Card management
# ---------------------------------------------------------------------------


def test_add_card_to_deck_returns_201(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.add_card.return_value = True
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/cards", json={"card_id": 10})

    assert response.status_code == 201
    data = response.json()
    assert "cards" in data


def test_add_card_not_in_collection_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.add_card.return_value = False

    response = client.post("/api/decks/1/cards", json={"card_id": 999})

    assert response.status_code == 404
    assert "collection" in response.json()["detail"].lower()


def test_add_card_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = None

    response = client.post("/api/decks/999/cards", json={"card_id": 10})

    assert response.status_code == 404


def test_set_commander_updates_deck(deck_client):
    client, mock_repo = deck_client
    mock_repo.set_commander.return_value = True
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.patch("/api/decks/1/cards/20", json={"is_commander": True})

    assert response.status_code == 200
    data = response.json()
    assert "cards" in data


def test_set_commander_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.set_commander.return_value = False

    response = client.patch("/api/decks/1/cards/999", json={"is_commander": True})

    assert response.status_code == 404


def test_remove_card_returns_204(deck_client):
    client, mock_repo = deck_client
    mock_repo.remove_card.return_value = True

    response = client.delete("/api/decks/1/cards/10")

    assert response.status_code == 204


def test_remove_card_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.remove_card.return_value = False

    response = client.delete("/api/decks/1/cards/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Batch card add
# ---------------------------------------------------------------------------


def test_batch_add_cards_returns_200(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.add_cards_batch.return_value = {"added": [10, 20], "not_found": []}
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/cards/batch", json={"card_ids": [10, 20]})

    assert response.status_code == 200
    data = response.json()
    assert data["added"] == [10, 20]
    assert data["not_found"] == []
    assert "cards" in data["deck"]


def test_batch_add_partial_not_found_returns_200(deck_client):
    """When some card_ids are not in the collection, returns 200 with not_found populated."""
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.add_cards_batch.return_value = {"added": [10], "not_found": [999]}
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/cards/batch", json={"card_ids": [10, 999]})

    assert response.status_code == 200
    data = response.json()
    assert data["added"] == [10]
    assert data["not_found"] == [999]


def test_batch_add_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = None

    response = client.post("/api/decks/999/cards/batch", json={"card_ids": [10]})

    assert response.status_code == 404


def test_batch_add_empty_card_ids_returns_current_deck(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/cards/batch", json={"card_ids": []})

    assert response.status_code == 200
    data = response.json()
    assert data["added"] == []
    assert data["not_found"] == []
    assert "cards" in data["deck"]
    mock_repo.add_cards_batch.assert_not_called()


# ---------------------------------------------------------------------------
# Import deck text
# ---------------------------------------------------------------------------


def test_import_deck_matched_cards(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.find_card_ids_by_names.return_value = {"lightning bolt": 10}
    mock_repo.add_card.return_value = True
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post(
        "/api/decks/1/import",
        json={"text": "1 Lightning Bolt"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 1
    assert data["skipped_count"] == 0
    assert data["skipped"] == []
    assert "cards" in data["deck"]


def test_import_deck_unmatched_cards_skipped(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    # No matching card found
    mock_repo.find_card_ids_by_names.return_value = {}
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post(
        "/api/decks/1/import",
        json={"text": "1 Nonexistent Card"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 0
    assert data["skipped_count"] == 1
    assert data["skipped"][0]["name"] == "Nonexistent Card"
    assert data["skipped"][0]["reason"] == "not_in_collection"


def test_import_deck_not_found_returns_404(deck_client):
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = None

    response = client.post(
        "/api/decks/999/import",
        json={"text": "1 Lightning Bolt"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 501 without PostgreSQL
# ---------------------------------------------------------------------------


def test_import_deck_commander_section(deck_client):
    """Cards under //Commander are passed to the repository with is_commander=True."""
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.find_card_ids_by_names.return_value = {
        "atraxa, praetors' voice": 42,
        "lightning bolt": 10,
    }
    mock_repo.add_card.return_value = True
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post(
        "/api/decks/1/import",
        json={"text": "//Commander\n1 Atraxa, Praetors' Voice\n//Mainboard\n4 Lightning Bolt"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 2
    assert data["skipped_count"] == 0

    # Capture the add_card calls and verify commander status.
    # Route signature: repo.add_card(deck_id, card_id, quantity=..., is_commander=..., user_id=...)
    calls = mock_repo.add_card.call_args_list
    assert len(calls) == 2

    # Find the call for Atraxa (card_id=42) — must have is_commander=True
    atraxa_call = next(c for c in calls if c.args[1] == 42)
    assert atraxa_call.kwargs["is_commander"] is True

    # Find the call for Lightning Bolt (card_id=10) — must have is_commander=False
    bolt_call = next(c for c in calls if c.args[1] == 10)
    assert bolt_call.kwargs["is_commander"] is False


def test_501_when_no_postgres():
    """When require_deck_repo raises 501, all deck endpoints return 501."""
    # Temporarily replace the require_deck_repo override with one that raises 501,
    # simulating the real behaviour when get_deck_repo() returns None.
    original_overrides = dict(app.dependency_overrides)

    def _raise_501():
        raise HTTPException(
            status_code=501,
            detail="Decks require Postgres. Set DATABASE_URL to use the deck builder.",
        )

    app.dependency_overrides[require_deck_repo] = _raise_501
    app.dependency_overrides[get_current_user_id] = lambda: 1

    try:
        client = TestClient(app)
        response = client.get("/api/decks/")
        assert response.status_code == 501
        assert "Postgres" in response.json()["detail"]
    finally:
        # Restore whatever was there before
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
