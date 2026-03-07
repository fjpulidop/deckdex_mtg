"""
Tests for card ownership validation in single-card price update endpoint.
"""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app


class TestSingleCardPriceUpdateOwnership(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user_id, None)

    @patch("backend.api.routes.process.get_collection_repo")
    def test_returns_404_when_card_belongs_to_another_user(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_repo.get_card_by_id.return_value = None
        mock_get_repo.return_value = mock_repo

        response = self.client.post("/api/prices/update/42")

        self.assertEqual(response.status_code, 404)
        mock_repo.get_card_by_id.assert_called_once_with(42, user_id=1)

    @patch("backend.api.routes.process.get_collection_repo")
    def test_passes_user_id_to_get_card_by_id(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_repo.get_card_by_id.return_value = {
            "id": 42,
            "name": "Lightning Bolt",
            "user_id": 1,
        }
        mock_get_repo.return_value = mock_repo

        response = self.client.post("/api/prices/update/42")

        mock_repo.get_card_by_id.assert_called_once_with(42, user_id=1)
