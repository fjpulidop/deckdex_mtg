"""Tests for GET /api/cards/allocations endpoint."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app
from backend.api.routes.cards import _require_deck_repo_for_allocations
from deckdex.storage.deck_repository import DeckRepository  # noqa: F401 — used in MagicMock(spec=...)

# ---------------------------------------------------------------------------
# Fixtures — all scope="function" to prevent cross-test mock pollution
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def auth_client():
    """TestClient with authenticated user (user_id=1). No deck repo override."""
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture(scope="function")
def allocation_client():
    """TestClient with both auth and a mocked DeckRepository.

    Yields (client, mock_repo). Configure mock_repo return values per test.
    """
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[get_current_user_id] = lambda: 1
    app.dependency_overrides[_require_deck_repo_for_allocations] = lambda: mock_repo
    client = TestClient(app)
    yield client, mock_repo
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(_require_deck_repo_for_allocations, None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_allocations_unauthenticated():
    """Unauthenticated request returns 401."""
    client = TestClient(app)
    response = client.get("/api/cards/allocations")
    assert response.status_code == 401


def test_allocations_no_postgres(auth_client):
    """Returns 501 when Postgres is not configured (deck repo unavailable)."""
    # Override: repo guard returns None → 501
    app.dependency_overrides[_require_deck_repo_for_allocations] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=501, detail="Allocations require Postgres.")
    )
    try:
        response = auth_client.get("/api/cards/allocations")
        assert response.status_code == 501
    finally:
        app.dependency_overrides.pop(_require_deck_repo_for_allocations, None)


def test_allocations_empty_collection(allocation_client):
    """Returns empty cards list when user has no cards."""
    client, mock_repo = allocation_client
    mock_repo.get_all_card_allocations.return_value = []

    response = client.get("/api/cards/allocations")

    assert response.status_code == 200
    assert response.json() == {"cards": []}


def test_allocations_card_in_no_deck(allocation_client):
    """Card with deck_id=None appears with empty decks array."""
    client, mock_repo = allocation_client
    mock_repo.get_all_card_allocations.return_value = [
        {
            "card_id": 1,
            "card_name": "Lightning Bolt",
            "image_url": None,
            "type_line": "Instant",
            "mana_cost": "{R}",
            "quantity": 1,
            "deck_id": None,
            "deck_name": None,
        },
    ]

    response = client.get("/api/cards/allocations")

    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 1
    assert data["cards"][0]["card_name"] == "Lightning Bolt"
    assert data["cards"][0]["decks"] == []


def test_allocations_card_in_one_deck(allocation_client):
    """Card in one deck has one entry in decks array."""
    client, mock_repo = allocation_client
    mock_repo.get_all_card_allocations.return_value = [
        {
            "card_id": 2,
            "card_name": "Sol Ring",
            "image_url": None,
            "type_line": "Artifact",
            "mana_cost": "{1}",
            "quantity": 1,
            "deck_id": 10,
            "deck_name": "My Commander",
        },
    ]

    response = client.get("/api/cards/allocations")

    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 1
    assert len(data["cards"][0]["decks"]) == 1
    assert data["cards"][0]["decks"][0]["deck_id"] == 10
    assert data["cards"][0]["decks"][0]["deck_name"] == "My Commander"


def test_allocations_card_in_multiple_decks(allocation_client):
    """Card in two decks appears once in response with two entries in decks array."""
    client, mock_repo = allocation_client
    mock_repo.get_all_card_allocations.return_value = [
        {
            "card_id": 3,
            "card_name": "Island",
            "image_url": None,
            "type_line": "Basic Land",
            "mana_cost": None,
            "quantity": 4,
            "deck_id": 10,
            "deck_name": "Deck A",
        },
        {
            "card_id": 3,
            "card_name": "Island",
            "image_url": None,
            "type_line": "Basic Land",
            "mana_cost": None,
            "quantity": 4,
            "deck_id": 11,
            "deck_name": "Deck B",
        },
    ]

    response = client.get("/api/cards/allocations")

    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 1  # deduplicated by card_id
    assert len(data["cards"][0]["decks"]) == 2
    deck_ids = {d["deck_id"] for d in data["cards"][0]["decks"]}
    assert deck_ids == {10, 11}


def test_allocations_multiple_cards(allocation_client):
    """Multiple cards with mixed deck assignments aggregate correctly."""
    client, mock_repo = allocation_client
    mock_repo.get_all_card_allocations.return_value = [
        # Card 1: in no deck
        {
            "card_id": 1,
            "card_name": "Forest",
            "image_url": None,
            "type_line": "Basic Land",
            "mana_cost": None,
            "quantity": 10,
            "deck_id": None,
            "deck_name": None,
        },
        # Card 2: in one deck
        {
            "card_id": 2,
            "card_name": "Sol Ring",
            "image_url": None,
            "type_line": "Artifact",
            "mana_cost": "{1}",
            "quantity": 1,
            "deck_id": 5,
            "deck_name": "Atraxa",
        },
    ]

    response = client.get("/api/cards/allocations")

    assert response.status_code == 200
    data = response.json()
    cards = {c["card_id"]: c for c in data["cards"]}
    assert len(cards) == 2
    assert cards[1]["decks"] == []
    assert len(cards[2]["decks"]) == 1
    assert cards[2]["decks"][0]["deck_name"] == "Atraxa"
