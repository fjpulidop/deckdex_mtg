"""Tests for PATCH /api/decks/{deck_id}/cards/{card_id}/allocate endpoint.

Mocks require_deck_repo (FastAPI dependency) and get_current_user_id so no
real database is needed. All fixtures use scope="function" to prevent
cross-test mock pollution.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app
from backend.api.routes.decks import require_deck_repo
from deckdex.storage.deck_repository import DeckRepository

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_DECK = {
    "id": 7,
    "name": "Atraxa Superfriends",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
}

SAMPLE_ALLOCATION_ROW = {
    "card_id": 42,
    "card_name": "Sol Ring",
    "deck_id": 7,
    "deck_name": "Atraxa Superfriends",
}

# ---------------------------------------------------------------------------
# Fixtures — all scope="function" to prevent cross-test mock pollution
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def allocate_client():
    """TestClient with mocked DeckRepository and authenticated user (user_id=1).

    Yields (client, mock_repo). Each test configures mock_repo for its scenario.
    """
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[require_deck_repo] = lambda: mock_repo
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client, mock_repo
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_allocate_happy_path_card_added(allocate_client):
    """Happy path: ensure_card_in_deck returns True, response is 200 with correct shape."""
    client, mock_repo = allocate_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.ensure_card_in_deck.return_value = True
    mock_repo.get_all_card_allocations.return_value = [SAMPLE_ALLOCATION_ROW]

    response = client.patch("/api/decks/7/cards/42/allocate")

    assert response.status_code == 200
    data = response.json()
    assert data["card_id"] == 42
    assert data["deck_id"] == 7
    assert data["deck_name"] == "Atraxa Superfriends"
    assert isinstance(data["decks"], list)
    assert len(data["decks"]) == 1
    assert data["decks"][0]["deck_id"] == 7
    assert data["decks"][0]["deck_name"] == "Atraxa Superfriends"


def test_allocate_idempotent_returns_200_both_times(allocate_client):
    """Idempotent: calling the endpoint twice both return 200."""
    client, mock_repo = allocate_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.ensure_card_in_deck.return_value = True
    mock_repo.get_all_card_allocations.return_value = [SAMPLE_ALLOCATION_ROW]

    response1 = client.patch("/api/decks/7/cards/42/allocate")
    response2 = client.patch("/api/decks/7/cards/42/allocate")

    assert response1.status_code == 200
    assert response2.status_code == 200


def test_allocate_deck_not_found_returns_404(allocate_client):
    """Deck not found: get_by_id returns None, response is 404."""
    client, mock_repo = allocate_client
    mock_repo.get_by_id.return_value = None

    response = client.patch("/api/decks/999/cards/42/allocate")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Deck not found"


def test_allocate_card_not_in_collection_returns_404(allocate_client):
    """Card not in collection: ensure_card_in_deck returns False, response is 404."""
    client, mock_repo = allocate_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.ensure_card_in_deck.return_value = False

    response = client.patch("/api/decks/7/cards/999/allocate")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Card not found in collection"


def test_allocate_no_postgres_returns_501():
    """No Postgres: require_deck_repo raises 501, response is 501."""
    from fastapi import HTTPException

    app.dependency_overrides[require_deck_repo] = lambda: (_ for _ in ()).throw(
        HTTPException(
            status_code=501,
            detail="Decks require Postgres. Set DATABASE_URL to use the deck builder.",
        )
    )
    app.dependency_overrides[get_current_user_id] = lambda: 1
    try:
        client = TestClient(app)
        response = client.patch("/api/decks/7/cards/42/allocate")
        assert response.status_code == 501
    finally:
        app.dependency_overrides.pop(require_deck_repo, None)
        app.dependency_overrides.pop(get_current_user_id, None)
