"""Integration tests for catalog API routes using FastAPI TestClient."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies import get_current_user_id

# Override auth for all tests
app.dependency_overrides[get_current_user_id] = lambda: 1

client = TestClient(app)


SAMPLE_CARDS = [
    {"scryfall_id": "aaa-111", "name": "Lightning Bolt", "rarity": "common", "type_line": "Instant"},
    {"scryfall_id": "bbb-222", "name": "Lightning Helix", "rarity": "uncommon", "type_line": "Instant"},
]


class TestCatalogSearch(unittest.TestCase):
    """Test GET /api/catalog/search."""

    @patch("backend.api.routes.catalog_routes._get_catalog_repo")
    def test_search_returns_200_with_results(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_repo.search_by_name.return_value = SAMPLE_CARDS
        mock_get_repo.return_value = mock_repo

        response = client.get("/api/catalog/search?q=bolt")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    @patch("backend.api.routes.catalog_routes._get_catalog_repo")
    def test_search_empty_results(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_repo.search_by_name.return_value = []
        mock_get_repo.return_value = mock_repo

        response = client.get("/api/catalog/search?q=nonexistent")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch("backend.api.routes.catalog_routes._get_catalog_repo")
    def test_search_501_when_no_postgres(self, mock_get_repo):
        from fastapi import HTTPException
        mock_get_repo.side_effect = HTTPException(status_code=501, detail="Catalog requires PostgreSQL (DATABASE_URL)")

        response = client.get("/api/catalog/search?q=bolt")
        self.assertEqual(response.status_code, 501)


class TestCatalogAutocomplete(unittest.TestCase):
    """Test GET /api/catalog/autocomplete."""

    @patch("backend.api.routes.catalog_routes._get_catalog_repo")
    def test_autocomplete_returns_names(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_repo.autocomplete.return_value = ["Lightning Bolt", "Lightning Helix"]
        mock_get_repo.return_value = mock_repo

        # Mock the catalog_service.autocomplete call
        with patch("backend.api.services.catalog_service.autocomplete", return_value=["Lightning Bolt", "Lightning Helix"]):
            response = client.get("/api/catalog/autocomplete?q=li")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)


class TestCatalogGetCard(unittest.TestCase):
    """Test GET /api/catalog/cards/{scryfall_id}."""

    @patch("backend.api.routes.catalog_routes._get_catalog_repo")
    def test_get_card_found(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        with patch("backend.api.services.catalog_service.get_card", return_value=SAMPLE_CARDS[0]):
            response = client.get("/api/catalog/cards/aaa-111")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["name"], "Lightning Bolt")

    @patch("backend.api.routes.catalog_routes._get_catalog_repo")
    def test_get_card_not_found(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        with patch("backend.api.services.catalog_service.get_card", return_value=None):
            response = client.get("/api/catalog/cards/unknown-id")
            self.assertEqual(response.status_code, 404)


class TestCatalogSync(unittest.TestCase):
    """Test POST /api/catalog/sync."""

    @patch("backend.api.routes.catalog_routes.catalog_service")
    def test_trigger_sync_returns_job_id(self, mock_svc):
        mock_svc.start_sync.return_value = "job-123"

        with patch("backend.api.dependencies.get_catalog_repo", return_value=MagicMock()), \
             patch("backend.api.dependencies.get_image_store", return_value=MagicMock()), \
             patch("backend.api.dependencies.get_job_repo", return_value=MagicMock()), \
             patch("backend.api.routes.catalog_routes.ws_manager"):
            response = client.post("/api/catalog/sync")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("job_id", data)

    @patch("backend.api.routes.catalog_routes.catalog_service")
    def test_trigger_sync_409_already_running(self, mock_svc):
        mock_svc.start_sync.side_effect = RuntimeError("A catalog sync is already running")

        with patch("backend.api.dependencies.get_catalog_repo", return_value=MagicMock()), \
             patch("backend.api.dependencies.get_image_store", return_value=MagicMock()), \
             patch("backend.api.dependencies.get_job_repo", return_value=MagicMock()):
            response = client.post("/api/catalog/sync")
            self.assertEqual(response.status_code, 409)


class TestCatalogSyncStatus(unittest.TestCase):
    """Test GET /api/catalog/sync/status."""

    @patch("backend.api.routes.catalog_routes._get_catalog_repo")
    def test_sync_status_returns_state(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        with patch("backend.api.services.catalog_service.get_sync_status", return_value={"status": "idle", "total_cards": 0}):
            response = client.get("/api/catalog/sync/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "idle")


if __name__ == "__main__":
    unittest.main()
