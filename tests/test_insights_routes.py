"""Integration tests for Insights API routes (backend/api/routes/insights.py).

Tests all three endpoints via FastAPI TestClient:
- GET  /api/insights/catalog
- POST /api/insights/{insight_id}
- GET  /api/insights/suggestions

Patches:
- get_cached_collection at the route module level (bound name)
- InsightsService at the route module level
- InsightsSuggestionEngine at the route module level
- get_current_user_id via app.dependency_overrides
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app
from backend.api.services.insights_service import INSIGHTS_CATALOG

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_INSIGHT_ENVELOPE = {
    "insight_id": "total_cards",
    "question": "How many cards do I have?",
    "answer_text": "You have 42 cards in your collection.",
    "response_type": "value",
    "data": {"value": 42, "unit": "cards"},
}

SAMPLE_SUGGESTIONS = [
    {"id": "total_cards", "label": "How many cards do I have?"},
    {"id": "total_value", "label": "How much is my collection worth?"},
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def insights_client():
    """TestClient with auth override for insights routes.

    Yields a TestClient. Each test patches module-level callables as needed.
    """
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


# ---------------------------------------------------------------------------
# Task 1.2 — GET /api/insights/catalog
# ---------------------------------------------------------------------------


def test_insights_catalog_returns_list(insights_client):
    """Catalog endpoint returns 200 with a non-empty list; each entry has id and label."""
    response = insights_client.get("/api/insights/catalog")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for entry in data:
        assert "id" in entry
        assert "label" in entry


def test_insights_catalog_matches_constant(insights_client):
    """Catalog endpoint returns exactly the INSIGHTS_CATALOG constant."""
    response = insights_client.get("/api/insights/catalog")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(INSIGHTS_CATALOG)
    ids_returned = {entry["id"] for entry in data}
    ids_expected = {entry["id"] for entry in INSIGHTS_CATALOG}
    assert ids_returned == ids_expected


# ---------------------------------------------------------------------------
# Task 1.3 — POST /api/insights/{insight_id} — success
# ---------------------------------------------------------------------------


def test_execute_insight_success(insights_client):
    """POST /api/insights/total_cards returns 200 with all expected envelope keys."""
    mock_service_instance = MagicMock()
    mock_service_instance.execute.return_value = SAMPLE_INSIGHT_ENVELOPE

    mock_service_cls = MagicMock(return_value=mock_service_instance)

    with (
        patch("backend.api.routes.insights.get_cached_collection", return_value=[]),
        patch("backend.api.routes.insights.InsightsService", mock_service_cls),
    ):
        response = insights_client.post("/api/insights/total_cards")

    assert response.status_code == 200
    data = response.json()
    assert "insight_id" in data
    assert "question" in data
    assert "answer_text" in data
    assert "response_type" in data
    assert "data" in data


# ---------------------------------------------------------------------------
# Task 1.4 — POST /api/insights/{insight_id} — 404 on ValueError
# ---------------------------------------------------------------------------


def test_execute_insight_not_found_returns_404(insights_client):
    """POST /api/insights/bad_id returns 404 when InsightsService.execute raises ValueError."""
    mock_service_instance = MagicMock()
    mock_service_instance.execute.side_effect = ValueError("Unknown insight ID: bad_id")

    mock_service_cls = MagicMock(return_value=mock_service_instance)

    with (
        patch("backend.api.routes.insights.get_cached_collection", return_value=[]),
        patch("backend.api.routes.insights.InsightsService", mock_service_cls),
    ):
        response = insights_client.post("/api/insights/bad_id")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Task 1.5 — POST /api/insights/{insight_id} — 501 on NotImplementedError
# ---------------------------------------------------------------------------


def test_execute_insight_not_implemented_returns_501(insights_client):
    """POST /api/insights/some_id returns 501 when InsightsService.execute raises NotImplementedError."""
    mock_service_instance = MagicMock()
    mock_service_instance.execute.side_effect = NotImplementedError("Insight not implemented")

    mock_service_cls = MagicMock(return_value=mock_service_instance)

    with (
        patch("backend.api.routes.insights.get_cached_collection", return_value=[]),
        patch("backend.api.routes.insights.InsightsService", mock_service_cls),
    ):
        response = insights_client.post("/api/insights/some_id")

    assert response.status_code == 501


# ---------------------------------------------------------------------------
# Task 1.6 — POST /api/insights/{insight_id} — 500 on unexpected error
# ---------------------------------------------------------------------------


def test_execute_insight_unexpected_error_returns_500(insights_client):
    """POST /api/insights/some_id returns 500 when InsightsService.execute raises an unexpected Exception."""
    mock_service_instance = MagicMock()
    mock_service_instance.execute.side_effect = Exception("boom")

    mock_service_cls = MagicMock(return_value=mock_service_instance)

    with (
        patch("backend.api.routes.insights.get_cached_collection", return_value=[]),
        patch("backend.api.routes.insights.InsightsService", mock_service_cls),
    ):
        response = insights_client.post("/api/insights/some_id")

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Task 1.7 — GET /api/insights/suggestions — success
# ---------------------------------------------------------------------------


def test_insights_suggestions_success(insights_client):
    """GET /api/insights/suggestions returns 200 with a list of dicts having id and label."""
    mock_engine_instance = MagicMock()
    mock_engine_instance.get_suggestions.return_value = SAMPLE_SUGGESTIONS

    mock_engine_cls = MagicMock(return_value=mock_engine_instance)

    with (
        patch("backend.api.routes.insights.get_cached_collection", return_value=[]),
        patch("backend.api.routes.insights.InsightsSuggestionEngine", mock_engine_cls),
    ):
        response = insights_client.get("/api/insights/suggestions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for entry in data:
        assert "id" in entry
        assert "label" in entry


# ---------------------------------------------------------------------------
# Task 1.8 — GET /api/insights/suggestions — 500 on error
# ---------------------------------------------------------------------------


def test_insights_suggestions_error_returns_500(insights_client):
    """GET /api/insights/suggestions returns 500 when InsightsSuggestionEngine raises an error."""
    mock_engine_cls = MagicMock(side_effect=Exception("engine failure"))

    with (
        patch("backend.api.routes.insights.get_cached_collection", return_value=[]),
        patch("backend.api.routes.insights.InsightsSuggestionEngine", mock_engine_cls),
    ):
        response = insights_client.get("/api/insights/suggestions")

    assert response.status_code == 500
