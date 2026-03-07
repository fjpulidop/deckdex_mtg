"""Tests for GET /api/cards/{id}/price-history endpoint.

Uses FastAPI TestClient with mocked repository so no real database is needed.
get_collection_repo is a plain function called directly in route bodies (not a
FastAPI Depends), so we patch it at the module level in backend.api.routes.cards.

Validation errors return 400 (not 422) because the app has a custom
RequestValidationError handler that returns HTTP_400_BAD_REQUEST.
"""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app

_PATCH_TARGET = "backend.api.routes.cards.get_collection_repo"

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_CARD = {
    "id": 42,
    "name": "Lightning Bolt",
    "rarity": "common",
    "type": "Instant",
    "set_name": "M10",
    "price": "0.50",
    "quantity": 1,
}

SAMPLE_HISTORY_POINTS = [
    {
        "recorded_at": "2026-01-01T12:00:00+00:00",
        "price": 0.40,
        "source": "scryfall",
        "currency": "eur",
    },
    {
        "recorded_at": "2026-01-15T12:00:00+00:00",
        "price": 0.50,
        "source": "scryfall",
        "currency": "eur",
    },
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_mock_repo(card=SAMPLE_CARD, history=None):
    """Build a mock CollectionRepository that returns the given card and history."""
    repo = MagicMock()
    repo.get_card_by_id.return_value = card
    repo.get_price_history.return_value = history if history is not None else []
    return repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetPriceHistoryEndpoint(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user_id, None)

    # --- 200 success cases ---

    def test_get_price_history_empty_returns_200_with_empty_points(self):
        """Returns 200 with empty points list when card exists but has no history."""
        mock_repo = _make_mock_repo(history=[])
        with patch(_PATCH_TARGET, return_value=mock_repo):
            response = self.client.get("/api/cards/42/price-history")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["card_id"], 42)
        self.assertEqual(data["currency"], "eur")
        self.assertEqual(data["points"], [])

    def test_get_price_history_with_data_returns_populated_points(self):
        """Returns 200 with populated points list when history exists."""
        mock_repo = _make_mock_repo(history=SAMPLE_HISTORY_POINTS)
        with patch(_PATCH_TARGET, return_value=mock_repo):
            response = self.client.get("/api/cards/42/price-history")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["points"]), 2)
        self.assertEqual(data["points"][0]["price"], 0.40)
        self.assertEqual(data["points"][1]["price"], 0.50)
        self.assertEqual(data["points"][0]["source"], "scryfall")
        self.assertEqual(data["points"][0]["currency"], "eur")

    # --- 404 case ---

    def test_get_price_history_404_for_unknown_card(self):
        """Returns 404 when card does not exist."""
        mock_repo = _make_mock_repo(card=None)
        with patch(_PATCH_TARGET, return_value=mock_repo):
            response = self.client.get("/api/cards/9999/price-history")

        self.assertEqual(response.status_code, 404)

    # --- 501 case ---

    def test_get_price_history_501_when_no_postgres(self):
        """Returns 501 when no DATABASE_URL is set (repo is None)."""
        with patch(_PATCH_TARGET, return_value=None):
            response = self.client.get("/api/cards/42/price-history")

        self.assertEqual(response.status_code, 501)
        self.assertIn("PostgreSQL", response.json()["detail"])

    # --- days query param ---

    def test_get_price_history_days_param_passed_to_repo(self):
        """?days=7 is passed to repo.get_price_history."""
        mock_repo = _make_mock_repo(history=[])
        with patch(_PATCH_TARGET, return_value=mock_repo):
            response = self.client.get("/api/cards/42/price-history?days=7")

        self.assertEqual(response.status_code, 200)
        mock_repo.get_price_history.assert_called_once_with(42, days=7)

    def test_get_price_history_default_days_is_90(self):
        """Default days parameter is 90."""
        mock_repo = _make_mock_repo(history=[])
        with patch(_PATCH_TARGET, return_value=mock_repo):
            self.client.get("/api/cards/42/price-history")

        mock_repo.get_price_history.assert_called_once_with(42, days=90)

    # --- validation (app returns 400, not 422, due to custom handler) ---

    def test_get_price_history_days_zero_returns_400(self):
        """?days=0 returns 400 (FastAPI validation ge=1; custom handler returns 400)."""
        mock_repo = _make_mock_repo(history=[])
        with patch(_PATCH_TARGET, return_value=mock_repo):
            response = self.client.get("/api/cards/42/price-history?days=0")

        self.assertEqual(response.status_code, 400)

    def test_get_price_history_days_366_returns_400(self):
        """?days=366 returns 400 (FastAPI validation le=365; custom handler returns 400)."""
        mock_repo = _make_mock_repo(history=[])
        with patch(_PATCH_TARGET, return_value=mock_repo):
            response = self.client.get("/api/cards/42/price-history?days=366")

        self.assertEqual(response.status_code, 400)

    def test_get_price_history_days_365_is_valid(self):
        """?days=365 is the maximum valid value and returns 200."""
        mock_repo = _make_mock_repo(history=[])
        with patch(_PATCH_TARGET, return_value=mock_repo):
            response = self.client.get("/api/cards/42/price-history?days=365")

        self.assertEqual(response.status_code, 200)

    # --- route ordering: does not interfere with other endpoints ---

    def test_image_endpoint_still_works(self):
        """GET /api/cards/{id}/image is not captured by price-history route."""
        mock_repo = _make_mock_repo()
        with patch(_PATCH_TARGET, return_value=mock_repo), \
             patch("backend.api.routes.cards.resolve_card_image") as mock_img:
            mock_img.return_value = (b"fake-image-data", "image/jpeg")
            response = self.client.get("/api/cards/42/image")

        # Should hit the image endpoint (not the price-history route)
        self.assertNotEqual(response.status_code, 404)
        mock_img.assert_called_once()
