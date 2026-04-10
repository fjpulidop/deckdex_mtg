"""Integration tests for GET /api/collection/variants endpoints.

All fixtures use scope="function" to prevent cross-test mock pollution.
Validation errors return HTTP 400 (not 422) via custom handler.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app

# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------

_SAMPLE_COPY = {
    "id": 1,
    "finish": "nonfoil",
    "variant_label": "Regular",
    "condition": "NM",
    "quantity": 1,
    "price": "0.50",
    "promo_types": None,
    "frame_effects": None,
    "border_color": None,
    "created_at": "2026-01-01T00:00:00",
}

_SAMPLE_SLOT = {
    "variant_label": "Regular",
    "finish": "nonfoil",
    "owned": True,
    "copies": [_SAMPLE_COPY],
    "scryfall_image_uri": None,
}

_SAMPLE_GROUP = {
    "card_name": "Lightning Bolt",
    "total_known_variants": 1,
    "owned_variant_count": 1,
    "slots": [_SAMPLE_SLOT],
}

_SAMPLE_COLLECTION_RESPONSE = {
    "groups": [_SAMPLE_GROUP],
    "total_cards": 1,
}


# ---------------------------------------------------------------------------
# Fixtures — all scope="function" to prevent cross-test pollution
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def auth_client():
    """TestClient with authenticated user (user_id=1)."""
    app.dependency_overrides[get_current_user_id] = lambda: 1
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture(scope="function")
def unauth_client():
    """TestClient with no auth override (unauthenticated)."""
    # Ensure no override is left from another test
    app.dependency_overrides.pop(get_current_user_id, None)
    client = TestClient(app)
    yield client


# ---------------------------------------------------------------------------
# Tests — GET /api/collection/variants
# ---------------------------------------------------------------------------


def test_list_variants_unauthenticated(unauth_client):
    """Unauthenticated request returns 401."""
    response = unauth_client.get("/api/collection/variants")
    assert response.status_code == 401


def test_list_variants_no_postgres(auth_client):
    """Returns 501 when PostgreSQL is not configured (service raises RuntimeError)."""
    with patch(
        "backend.api.routes.variants.variant_service.get_collection_variants",
        side_effect=RuntimeError("PostgreSQL required"),
    ):
        response = auth_client.get("/api/collection/variants")
    assert response.status_code == 501
    assert "PostgreSQL" in response.json()["detail"]


def test_list_variants_success(auth_client):
    """Returns 200 with valid structure when service returns data."""
    with patch(
        "backend.api.routes.variants.variant_service.get_collection_variants",
        return_value=_SAMPLE_COLLECTION_RESPONSE,
    ):
        response = auth_client.get("/api/collection/variants")
    assert response.status_code == 200
    data = response.json()
    assert "groups" in data
    assert "total_cards" in data
    assert data["total_cards"] == 1
    assert data["groups"][0]["card_name"] == "Lightning Bolt"


def test_list_variants_search_param_passed(auth_client):
    """Search query param is forwarded to the service."""
    with patch(
        "backend.api.routes.variants.variant_service.get_collection_variants",
        return_value={"groups": [], "total_cards": 0},
    ) as mock_svc:
        response = auth_client.get("/api/collection/variants?search=bolt")
    assert response.status_code == 200
    mock_svc.assert_called_once_with(
        user_id=1,
        search="bolt",
        limit=50,
        offset=0,
    )


def test_list_variants_empty_collection(auth_client):
    """Returns 200 with empty groups list when collection is empty."""
    with patch(
        "backend.api.routes.variants.variant_service.get_collection_variants",
        return_value={"groups": [], "total_cards": 0},
    ):
        response = auth_client.get("/api/collection/variants")
    assert response.status_code == 200
    assert response.json() == {"groups": [], "total_cards": 0}


def test_list_variants_invalid_limit_returns_400(auth_client):
    """limit=0 triggers validation error → HTTP 400 (custom handler)."""
    response = auth_client.get("/api/collection/variants?limit=0")
    assert response.status_code == 400


def test_list_variants_invalid_offset_returns_400(auth_client):
    """offset=-1 triggers validation error → HTTP 400 (custom handler)."""
    response = auth_client.get("/api/collection/variants?offset=-1")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Tests — GET /api/collection/variants/{card_name}
# ---------------------------------------------------------------------------


def test_get_card_variants_success(auth_client):
    """Returns 200 with valid CardVariantGroup structure for a known card."""
    with patch(
        "backend.api.routes.variants.variant_service.get_card_variants",
        return_value=_SAMPLE_GROUP,
    ):
        response = auth_client.get("/api/collection/variants/Lightning%20Bolt")
    assert response.status_code == 200
    data = response.json()
    assert data["card_name"] == "Lightning Bolt"
    assert "slots" in data
    assert len(data["slots"]) == 1


def test_get_card_variants_not_found(auth_client):
    """Returns 404 when the service raises ValueError (card not owned)."""
    with patch(
        "backend.api.routes.variants.variant_service.get_card_variants",
        side_effect=ValueError("No cards found for name: Unknown Card"),
    ):
        response = auth_client.get("/api/collection/variants/Unknown%20Card")
    assert response.status_code == 404


def test_get_card_variants_no_postgres(auth_client):
    """Returns 501 when PostgreSQL is not configured."""
    with patch(
        "backend.api.routes.variants.variant_service.get_card_variants",
        side_effect=RuntimeError("PostgreSQL required"),
    ):
        response = auth_client.get("/api/collection/variants/Lightning%20Bolt")
    assert response.status_code == 501


def test_get_card_variants_unauthenticated(unauth_client):
    """Unauthenticated request to card-level endpoint returns 401."""
    response = unauth_client.get("/api/collection/variants/Lightning%20Bolt")
    assert response.status_code == 401
