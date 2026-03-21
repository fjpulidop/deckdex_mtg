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
    """Cards under //Commander are passed to add_cards_from_import with is_commander=True."""
    client, mock_repo = deck_client
    mock_repo.get_by_id.return_value = SAMPLE_DECK
    mock_repo.find_card_ids_by_names.return_value = {
        "atraxa, praetors' voice": 42,
        "lightning bolt": 10,
    }
    mock_repo.add_cards_from_import.return_value = None
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post(
        "/api/decks/1/import",
        json={"text": "//Commander\n1 Atraxa, Praetors' Voice\n//Mainboard\n4 Lightning Bolt"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 2
    assert data["skipped_count"] == 0

    # Import now calls add_cards_from_import once with all cards in a single transaction.
    assert mock_repo.add_cards_from_import.call_count == 1
    call_args = mock_repo.add_cards_from_import.call_args
    cards_imported = call_args.args[1] if call_args.args else call_args.kwargs.get("cards", [])

    # Verify Atraxa was passed with is_commander=True
    atraxa_entry = next((c for c in cards_imported if c["card_id"] == 42), None)
    assert atraxa_entry is not None
    assert atraxa_entry["is_commander"] is True

    # Verify Lightning Bolt was passed with is_commander=False
    bolt_entry = next((c for c in cards_imported if c["card_id"] == 10), None)
    assert bolt_entry is not None
    assert bolt_entry["is_commander"] is False


# ---------------------------------------------------------------------------
# Deck history
# ---------------------------------------------------------------------------

SAMPLE_SNAPSHOT = {
    "id": 5,
    "created_at": "2026-01-15T10:00:00",
    "created_by": 1,
    "change_summary": "Added 1x Sol Ring",
    "diff": {
        "added": [{"card_id": 20, "name": "Sol Ring", "quantity": 1}],
        "removed": [],
        "quantity_changed": [],
        "commander_changed": None,
    },
}


def test_get_deck_history_returns_snapshots(deck_client):
    """GET /decks/{id}/history returns DeckHistoryResponse with snapshots list."""
    client, mock_repo = deck_client
    mock_repo.get_history.return_value = [SAMPLE_SNAPSHOT]

    response = client.get("/api/decks/1/history")

    assert response.status_code == 200
    data = response.json()
    assert data["deck_id"] == 1
    assert len(data["snapshots"]) == 1
    snap = data["snapshots"][0]
    assert snap["id"] == 5
    assert snap["change_summary"] == "Added 1x Sol Ring"
    assert "diff" in snap
    mock_repo.get_history.assert_called_once_with(1, user_id=1, limit=50)


def test_get_deck_history_empty(deck_client):
    """GET /decks/{id}/history returns empty snapshots list when deck has no history."""
    client, mock_repo = deck_client
    mock_repo.get_history.return_value = []

    response = client.get("/api/decks/1/history")

    assert response.status_code == 200
    data = response.json()
    assert data["deck_id"] == 1
    assert data["snapshots"] == []


def test_get_deck_history_not_found_returns_404(deck_client):
    """GET /decks/{id}/history returns 404 when repo returns None (deck missing or wrong owner)."""
    client, mock_repo = deck_client
    mock_repo.get_history.return_value = None

    response = client.get("/api/decks/999/history")

    assert response.status_code == 404
    assert response.json()["detail"] == "Deck not found"


def test_get_deck_history_limit_param_passed(deck_client):
    """GET /decks/{id}/history?limit=10 passes limit to repo."""
    client, mock_repo = deck_client
    mock_repo.get_history.return_value = []

    response = client.get("/api/decks/1/history?limit=10")

    assert response.status_code == 200
    mock_repo.get_history.assert_called_once_with(1, user_id=1, limit=10)


def test_get_deck_history_limit_too_small_returns_400(deck_client):
    """GET /decks/{id}/history?limit=0 — below minimum (ge=1) returns 400."""
    client, mock_repo = deck_client

    response = client.get("/api/decks/1/history?limit=0")

    # Query param validation: Pydantic coerces ge=1 constraint → custom handler returns 400
    assert response.status_code == 400


def test_get_deck_history_limit_too_large_returns_400(deck_client):
    """GET /decks/{id}/history?limit=201 — above maximum (le=200) returns 400."""
    client, mock_repo = deck_client

    response = client.get("/api/decks/1/history?limit=201")

    assert response.status_code == 400


def test_get_deck_history_multiple_snapshots(deck_client):
    """History with multiple snapshots preserves order and all fields."""
    client, mock_repo = deck_client
    snap2 = {
        "id": 6,
        "created_at": "2026-01-16T12:00:00",
        "created_by": 1,
        "change_summary": "Removed Lightning Bolt",
        "diff": {
            "added": [],
            "removed": [{"card_id": 10, "name": "Lightning Bolt", "quantity": 1}],
            "quantity_changed": [],
            "commander_changed": None,
        },
    }
    mock_repo.get_history.return_value = [snap2, SAMPLE_SNAPSHOT]

    response = client.get("/api/decks/1/history")

    assert response.status_code == 200
    snapshots = response.json()["snapshots"]
    assert len(snapshots) == 2
    assert snapshots[0]["id"] == 6
    assert snapshots[1]["id"] == 5


# ---------------------------------------------------------------------------
# Revert to snapshot
# ---------------------------------------------------------------------------


def test_revert_deck_to_snapshot_success(deck_client):
    """POST /decks/{id}/revert/{snapshot_id} returns reverted deck on success."""
    client, mock_repo = deck_client
    mock_repo.revert_to_snapshot.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.post("/api/decks/1/revert/5")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "cards" in data
    mock_repo.revert_to_snapshot.assert_called_once_with(1, 5, user_id=1)


def test_revert_deck_not_found_returns_404(deck_client):
    """POST /decks/{id}/revert/{snapshot_id} returns 404 when deck does not exist."""
    client, mock_repo = deck_client
    mock_repo.revert_to_snapshot.return_value = None

    response = client.post("/api/decks/999/revert/5")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_revert_snapshot_not_found_returns_404(deck_client):
    """POST /decks/{id}/revert/{snapshot_id} returns 404 when snapshot does not belong to deck."""
    client, mock_repo = deck_client
    mock_repo.revert_to_snapshot.return_value = None

    response = client.post("/api/decks/1/revert/9999")

    assert response.status_code == 404


def test_revert_card_missing_returns_409(deck_client):
    """POST revert returns 409 when a card in the snapshot no longer exists in the collection."""
    client, mock_repo = deck_client
    mock_repo.revert_to_snapshot.side_effect = ValueError("Card 'Sol Ring' (id=20) no longer exists in collection")

    response = client.post("/api/decks/1/revert/5")

    assert response.status_code == 409
    assert "no longer exists" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Compare endpoint — sample data
# ---------------------------------------------------------------------------

_SAMPLE_CARD_BOLT = {
    "id": 10,
    "name": "Lightning Bolt",
    "type": "Instant",
    "mana_cost": "{R}",
    "cmc": 1.0,
    "color_identity": "R",
    "price": "0.35",
    "quantity": 1,
    "is_commander": False,
}
_SAMPLE_CARD_SOLRING = {
    "id": 20,
    "name": "Sol Ring",
    "type": "Artifact",
    "mana_cost": "{1}",
    "cmc": 1.0,
    "color_identity": "",
    "price": "1.20",
    "quantity": 1,
    "is_commander": False,
}
_COMPARE_DECK_1 = {"id": 1, "name": "Deck A", "cards": [_SAMPLE_CARD_BOLT, _SAMPLE_CARD_SOLRING]}
_COMPARE_DECK_2 = {"id": 2, "name": "Deck B", "cards": [_SAMPLE_CARD_BOLT]}
_COMPARE_DECK_3 = {"id": 3, "name": "Deck C", "cards": [_SAMPLE_CARD_SOLRING]}


# ---------------------------------------------------------------------------
# Compare endpoint — fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def compare_client():
    """TestClient with mocked DeckRepository and auth for compare tests."""
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[require_deck_repo] = lambda: mock_repo
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client, mock_repo
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)


# ---------------------------------------------------------------------------
# Compare endpoint — tests
# ---------------------------------------------------------------------------


def test_compare_decks_returns_200(compare_client):
    client, mock_repo = compare_client
    mock_repo.get_deck_with_cards.side_effect = lambda deck_id, user_id: (
        _COMPARE_DECK_1 if deck_id == 1 else _COMPARE_DECK_2
    )

    r = client.get("/api/decks/compare?ids=1,2")

    assert r.status_code == 200
    data = r.json()
    assert len(data["decks"]) == 2
    assert "overlap_cards" in data


def test_compare_decks_too_few_ids(compare_client):
    client, _mock_repo = compare_client

    r = client.get("/api/decks/compare?ids=1")

    assert r.status_code == 400


def test_compare_decks_too_many_ids(compare_client):
    client, _mock_repo = compare_client

    r = client.get("/api/decks/compare?ids=1,2,3,4,5")

    assert r.status_code == 400


def test_compare_decks_non_integer_ids(compare_client):
    client, _mock_repo = compare_client

    r = client.get("/api/decks/compare?ids=1,foo")

    assert r.status_code == 400


def test_compare_decks_deck_not_found(compare_client):
    client, mock_repo = compare_client

    def side_effect(deck_id, user_id):
        if deck_id == 1:
            return _COMPARE_DECK_1
        return None

    mock_repo.get_deck_with_cards.side_effect = side_effect

    r = client.get("/api/decks/compare?ids=1,999")

    assert r.status_code == 404


def test_compare_decks_overlap_detection(compare_client):
    client, mock_repo = compare_client
    mock_repo.get_deck_with_cards.side_effect = lambda deck_id, user_id: (
        _COMPARE_DECK_1 if deck_id == 1 else _COMPARE_DECK_2
    )

    r = client.get("/api/decks/compare?ids=1,2")

    assert r.status_code == 200
    data = r.json()
    overlap = data["overlap_cards"]
    assert len(overlap) == 1
    assert overlap[0]["name"] == "Lightning Bolt"
    assert len(overlap[0]["deck_ids"]) == 2


def test_compare_decks_no_overlap(compare_client):
    client, mock_repo = compare_client
    # Deck 1 has Bolt+SolRing, Deck 3 has only SolRing — wait, they share SolRing
    # Use a deck with a card not in the other
    unique_deck = {
        "id": 4,
        "name": "Deck D",
        "cards": [
            {
                "id": 99,
                "name": "Counterspell",
                "type": "Instant",
                "mana_cost": "{U}{U}",
                "cmc": 2.0,
                "color_identity": "U",
                "price": "1.00",
                "quantity": 1,
                "is_commander": False,
            }
        ],
    }
    no_overlap_deck = {
        "id": 5,
        "name": "Deck E",
        "cards": [
            {
                "id": 98,
                "name": "Giant Growth",
                "type": "Instant",
                "mana_cost": "{G}",
                "cmc": 1.0,
                "color_identity": "G",
                "price": "0.10",
                "quantity": 1,
                "is_commander": False,
            }
        ],
    }
    mock_repo.get_deck_with_cards.side_effect = lambda deck_id, user_id: (
        unique_deck if deck_id == 4 else no_overlap_deck
    )

    r = client.get("/api/decks/compare?ids=4,5")

    assert r.status_code == 200
    data = r.json()
    assert data["overlap_cards"] == []


def test_compare_decks_requires_auth():
    """Without auth override, the compare route should not return 200."""
    # Remove any existing overrides for get_current_user_id to simulate no auth
    original_overrides = dict(app.dependency_overrides)
    # Keep require_deck_repo mock but remove user id override
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[require_deck_repo] = lambda: mock_repo

    # Remove get_current_user_id if it was set
    app.dependency_overrides.pop(get_current_user_id, None)

    try:
        client = TestClient(app)
        # Without get_current_user_id override, FastAPI will use the real dependency
        # which requires a valid JWT cookie — without it, the request returns non-200
        r = client.get("/api/decks/compare?ids=1,2")
        assert r.status_code != 200
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)


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
