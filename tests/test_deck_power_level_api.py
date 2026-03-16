"""Integration-style tests for GET /api/decks/{deck_id}/power-level.

All fixtures use scope="function". DeckRepository is mocked — no real DB connections.
"""

from unittest.mock import MagicMock, patch

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

SAMPLE_DECK_WITH_CARDS = {
    "id": 1,
    "name": "Test Deck",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
    "cards": [
        {
            "id": 10,
            "name": "Sol Ring",
            "description": "",
            "type": "Artifact",
            "cmc": 1.0,
            "edhrec_rank": 1,
            "quantity": 1,
            "is_commander": False,
        },
        {
            "id": 20,
            "name": "Demonic Tutor",
            "description": "Search your library for a card",
            "type": "Sorcery",
            "cmc": 2.0,
            "edhrec_rank": 10,
            "quantity": 1,
            "is_commander": False,
        },
        {
            "id": 30,
            "name": "Swamp",
            "description": "",
            "type": "Basic Land — Swamp",
            "cmc": 0.0,
            "edhrec_rank": 999,
            "quantity": 30,
            "is_commander": False,
        },
    ],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def power_level_client():
    """TestClient with mocked DeckRepository and auth.

    Yields (client, mock_repo). Dependency overrides are cleaned up after each test.
    """
    mock_repo = MagicMock(spec=DeckRepository)
    app.dependency_overrides[require_deck_repo] = lambda: mock_repo
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client, mock_repo
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture(scope="function")
def no_repo_client():
    """TestClient where require_deck_repo raises 501 (no Postgres configured)."""
    app.dependency_overrides[require_deck_repo] = lambda: (_ for _ in ()).throw(
        HTTPException(status_code=501, detail="Decks require Postgres. Set DATABASE_URL to use the deck builder.")
    )
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.pop(require_deck_repo, None)
    app.dependency_overrides.pop(get_current_user_id, None)


# ---------------------------------------------------------------------------
# Tests: 200 success
# ---------------------------------------------------------------------------


def test_power_level_200_for_existing_deck(power_level_client):
    """Endpoint returns 200 with correct response shape when deck exists."""
    client, mock_repo = power_level_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.get("/api/decks/1/power-level")

    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "bracket" in data
    assert "summary" in data
    assert "breakdown" in data
    breakdown = data["breakdown"]
    assert set(breakdown.keys()) == {"fast_mana", "tutors", "combo_pieces", "avg_cmc", "land_quality", "staple_density"}


def test_power_level_score_in_valid_range(power_level_client):
    """Response score is within [1.0, 10.0]."""
    client, mock_repo = power_level_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.get("/api/decks/1/power-level")

    assert response.status_code == 200
    score = response.json()["score"]
    assert 1.0 <= score <= 10.0


def test_power_level_bracket_in_valid_range(power_level_client):
    """Response bracket is within {1, 2, 3, 4}."""
    client, mock_repo = power_level_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.get("/api/decks/1/power-level")

    assert response.status_code == 200
    bracket = response.json()["bracket"]
    assert bracket in {1, 2, 3, 4}


def test_power_level_summary_is_non_empty_string(power_level_client):
    """Summary field is a non-empty string."""
    client, mock_repo = power_level_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.get("/api/decks/1/power-level")

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_power_level_breakdown_values_in_range(power_level_client):
    """All breakdown factor values are in [0.0, 1.0]."""
    client, mock_repo = power_level_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    response = client.get("/api/decks/1/power-level")

    assert response.status_code == 200
    breakdown = response.json()["breakdown"]
    for key, value in breakdown.items():
        assert 0.0 <= value <= 1.0, f"Breakdown factor '{key}' out of range: {value}"


# ---------------------------------------------------------------------------
# Tests: 404 not found
# ---------------------------------------------------------------------------


def test_power_level_404_when_deck_not_found(power_level_client):
    """Returns 404 when get_power_level returns None (deck not found)."""
    client, mock_repo = power_level_client
    mock_repo.get_deck_with_cards.return_value = None

    response = client.get("/api/decks/9999/power-level")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tests: 501 no Postgres
# ---------------------------------------------------------------------------


def test_power_level_501_when_no_postgres(no_repo_client):
    """Returns 501 when require_deck_repo raises HTTPException 501."""
    response = no_repo_client.get("/api/decks/1/power-level")

    assert response.status_code == 501


# ---------------------------------------------------------------------------
# Tests: caching behaviour
# ---------------------------------------------------------------------------


def test_power_level_cache_hit_single_estimate_call(power_level_client):
    """Two consecutive calls with unchanged deck produce exactly one estimate_power_level call."""
    client, mock_repo = power_level_client
    mock_repo.get_deck_with_cards.return_value = SAMPLE_DECK_WITH_CARDS

    # Clear the module-level cache first to avoid pollution from other tests
    import backend.api.services.power_level_service as svc

    svc._cache.clear()

    with patch("backend.api.services.power_level_service.estimate_power_level", wraps=None) as mock_est:
        from deckdex.services.power_level import FactorBreakdown, PowerLevelResult

        mock_est.return_value = PowerLevelResult(
            score=5.0,
            bracket=2,
            summary="5 — mid-power deck",
            breakdown=FactorBreakdown(
                fast_mana=0.25,
                tutors=0.4,
                combo_pieces=0.0,
                avg_cmc=0.55,
                land_quality=0.0,
                staple_density=0.2,
            ),
        )
        client.get("/api/decks/1/power-level")
        client.get("/api/decks/1/power-level")
        assert mock_est.call_count == 1
