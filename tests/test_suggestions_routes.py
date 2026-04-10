"""Tests for suggestions API routes (backend/api/routes/suggestions.py).

Mocks require_suggestion_repo, require_deck_repo (suggestions module), and
get_current_user_id so no real database is needed. All fixtures use scope="function".
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app
from backend.api.routes.suggestions import require_deck_repo, require_suggestion_repo
from deckdex.storage.deck_repository import DeckRepository
from deckdex.storage.suggestion_repository import SuggestionRepository

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_DECK = {
    "id": 42,
    "name": "Commander Deck",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
    "card_count": 99,
    "commander_card_id": None,
}

SAMPLE_SUGGESTION_ROW = {
    "id": 1,
    "deck_id": 42,
    "user_id": 1,
    "set_code": "OTJ",
    "scryfall_id": "abc-123",
    "card_name": "Test Card",
    "mana_cost": "{2}{B}",
    "cmc": 3.0,
    "type_line": "Creature — Human",
    "color_identity": "B",
    "oracle_text": "When this enters the battlefield, draw a card.",
    "reason": "Creature that fits your mana curve (median CMC 3.0)",
    "score": 0.85,
    "image_uri": "https://cards.scryfall.io/normal/abc-123.jpg",
    "created_at": "2026-04-01T00:00:00",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def suggestion_client():
    """TestClient with mocked SuggestionRepository, DeckRepository, and auth.

    Yields (client, mock_suggestion_repo, mock_deck_repo).
    """
    mock_suggestion_repo = MagicMock(spec=SuggestionRepository)
    mock_deck_repo = MagicMock(spec=DeckRepository)

    app.dependency_overrides[require_suggestion_repo] = lambda: mock_suggestion_repo
    app.dependency_overrides[require_deck_repo] = lambda: mock_deck_repo
    app.dependency_overrides[get_current_user_id] = lambda: 1

    # Ensure app.state has new_set_poller for refresh tests
    if not hasattr(app.state, "new_set_poller"):
        app.state.new_set_poller = MagicMock()
        app.state.new_set_poller.run_once = MagicMock(return_value=[])

    client = TestClient(app, raise_server_exceptions=False)
    yield client, mock_suggestion_repo, mock_deck_repo

    app.dependency_overrides.pop(require_suggestion_repo, None)
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture(scope="function")
def no_postgres_client():
    """TestClient with no suggestion repo (simulates Postgres not configured)."""
    app.dependency_overrides[require_suggestion_repo] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=501, detail="Deck suggestions require Postgres.")
    )
    app.dependency_overrides[get_current_user_id] = lambda: 1

    client = TestClient(app, raise_server_exceptions=False)
    yield client

    app.dependency_overrides.pop(require_suggestion_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture(scope="function")
def no_auth_client():
    """TestClient with mocked repos but NO auth override (returns 401).

    Auth check runs before repo resolution so 401 should be returned even when
    repos are properly configured.
    """
    mock_suggestion_repo = MagicMock(spec=SuggestionRepository)
    mock_deck_repo = MagicMock(spec=DeckRepository)

    app.dependency_overrides[require_suggestion_repo] = lambda: mock_suggestion_repo
    app.dependency_overrides[require_deck_repo] = lambda: mock_deck_repo
    # Intentionally do NOT override get_current_user_id so auth fails
    app.dependency_overrides.pop(get_current_user_id, None)

    client = TestClient(app, raise_server_exceptions=False)
    yield client

    app.dependency_overrides.pop(require_suggestion_repo, None)
    app.dependency_overrides.pop(require_deck_repo, None)


# ---------------------------------------------------------------------------
# Test: GET /api/decks/{id}/suggestions
# ---------------------------------------------------------------------------


def test_get_deck_suggestions_empty_list(suggestion_client):
    """Returns 200 with empty suggestions list when no suggestions exist."""
    client, mock_suggestion_repo, mock_deck_repo = suggestion_client
    mock_deck_repo.get_by_id.return_value = SAMPLE_DECK
    mock_suggestion_repo.get_suggestions_for_deck.return_value = []

    response = client.get("/api/decks/42/suggestions")

    assert response.status_code == 200
    data = response.json()
    assert data["deck_id"] == 42
    assert data["suggestions"] == []


def test_get_deck_suggestions_with_data(suggestion_client):
    """Returns 200 with suggestion data when rows exist."""
    client, mock_suggestion_repo, mock_deck_repo = suggestion_client
    mock_deck_repo.get_by_id.return_value = SAMPLE_DECK
    mock_suggestion_repo.get_suggestions_for_deck.return_value = [SAMPLE_SUGGESTION_ROW]

    response = client.get("/api/decks/42/suggestions")

    assert response.status_code == 200
    data = response.json()
    assert data["deck_id"] == 42
    assert len(data["suggestions"]) == 1
    s = data["suggestions"][0]
    assert s["scryfall_id"] == "abc-123"
    assert s["card_name"] == "Test Card"
    assert s["score"] == pytest.approx(0.85)
    assert data["set_code"] == "OTJ"


def test_get_deck_suggestions_deck_not_found(suggestion_client):
    """Returns 404 when deck belongs to another user."""
    client, mock_suggestion_repo, mock_deck_repo = suggestion_client
    mock_deck_repo.get_by_id.return_value = None

    response = client.get("/api/decks/99/suggestions")

    assert response.status_code == 404


def test_get_deck_suggestions_no_auth(no_auth_client):
    """Returns 401 when no auth cookie is present."""
    response = no_auth_client.get("/api/decks/42/suggestions")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test: DELETE /api/decks/{id}/suggestions/{scryfall_id}
# ---------------------------------------------------------------------------


def test_dismiss_suggestion_success(suggestion_client):
    """Returns 204 on successful dismissal."""
    client, mock_suggestion_repo, _ = suggestion_client
    mock_suggestion_repo.delete_suggestion.return_value = True

    response = client.delete("/api/decks/42/suggestions/abc-123")

    assert response.status_code == 204


def test_dismiss_suggestion_not_found(suggestion_client):
    """Returns 404 when suggestion not found."""
    client, mock_suggestion_repo, _ = suggestion_client
    mock_suggestion_repo.delete_suggestion.return_value = False

    response = client.delete("/api/decks/42/suggestions/nonexistent-id")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Test: POST /api/suggestions/refresh
# ---------------------------------------------------------------------------


def test_refresh_suggestions_returns_202(suggestion_client):
    """Returns 202 with message field when poller is available."""
    client, _, _ = suggestion_client

    response = client.post("/api/suggestions/refresh")

    assert response.status_code == 202
    data = response.json()
    assert "message" in data
    assert "refresh" in data["message"].lower() or "started" in data["message"].lower()


# ---------------------------------------------------------------------------
# Test: 501 when Postgres not configured
# ---------------------------------------------------------------------------


def test_get_deck_suggestions_postgres_not_configured(no_postgres_client):
    """Returns 501 when Postgres is not configured."""
    response = no_postgres_client.get("/api/decks/42/suggestions")
    assert response.status_code == 501
