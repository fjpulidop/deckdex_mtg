"""Integration tests for Scryfall credentials settings routes.

Tests both endpoints via FastAPI TestClient:
- GET /api/settings/scryfall-credentials
- PUT /api/settings/scryfall-credentials

Patches:
- get_scryfall_credentials at the settings_routes module level (bound name)
- set_scryfall_credentials at the settings_routes module level (bound name)
- get_current_user_id via app.dependency_overrides
"""

from unittest.mock import MagicMock, call, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def creds_client():
    """TestClient with auth override for scryfall-credentials routes.

    Yields a TestClient. Each test patches the store functions as needed.
    """
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


# ---------------------------------------------------------------------------
# Task 2.2 — GET /api/settings/scryfall-credentials — credentials configured
# ---------------------------------------------------------------------------


def test_get_scryfall_credentials_configured_true(creds_client):
    """GET returns 200 with configured=true when credentials exist."""
    with patch(
        "backend.api.routes.settings_routes.get_scryfall_credentials",
        return_value={"key": "val"},
    ):
        response = creds_client.get("/api/settings/scryfall-credentials")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True


# ---------------------------------------------------------------------------
# Task 2.3 — GET /api/settings/scryfall-credentials — not configured
# ---------------------------------------------------------------------------


def test_get_scryfall_credentials_not_configured(creds_client):
    """GET returns 200 with configured=false when credentials are None."""
    with patch(
        "backend.api.routes.settings_routes.get_scryfall_credentials",
        return_value=None,
    ):
        response = creds_client.get("/api/settings/scryfall-credentials")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False


# ---------------------------------------------------------------------------
# Task 2.4 — PUT /api/settings/scryfall-credentials — store credentials
# ---------------------------------------------------------------------------


def test_put_scryfall_credentials_stores_and_returns_true(creds_client):
    """PUT with a credentials dict stores them and returns configured=true."""
    mock_set = MagicMock()

    with (
        patch("backend.api.routes.settings_routes.set_scryfall_credentials", mock_set),
        patch(
            "backend.api.routes.settings_routes.get_scryfall_credentials",
            return_value={"api_key": "abc"},
        ),
    ):
        response = creds_client.put(
            "/api/settings/scryfall-credentials",
            json={"credentials": {"api_key": "abc"}},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    mock_set.assert_called_once()


# ---------------------------------------------------------------------------
# Task 2.5 — PUT /api/settings/scryfall-credentials — clear credentials
# ---------------------------------------------------------------------------


def test_put_scryfall_credentials_null_clears_and_returns_false(creds_client):
    """PUT with credentials=null clears them and returns configured=false."""
    mock_set = MagicMock()

    with (
        patch("backend.api.routes.settings_routes.set_scryfall_credentials", mock_set),
        patch(
            "backend.api.routes.settings_routes.get_scryfall_credentials",
            return_value=None,
        ),
    ):
        response = creds_client.put(
            "/api/settings/scryfall-credentials",
            json={"credentials": None},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    mock_set.assert_called_once_with(None)
