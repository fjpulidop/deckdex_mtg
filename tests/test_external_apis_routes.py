"""Integration tests for external-apis settings routes and CardFetcher bug regression."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies import get_current_user_id, get_user_settings_repo

# Override auth for all tests
app.dependency_overrides[get_current_user_id] = lambda: 1

client = TestClient(app)


class TestGetExternalApisSettings(unittest.TestCase):
    """Test GET /api/settings/external-apis."""

    def test_returns_default_false(self):
        mock_repo = MagicMock()
        mock_repo.get_external_apis_settings.return_value = {"scryfall_enabled": False}

        with patch("backend.api.routes.settings_routes.get_user_settings_repo", return_value=mock_repo):
            response = client.get("/api/settings/external-apis")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["scryfall_enabled"])

    def test_returns_enabled_when_set(self):
        mock_repo = MagicMock()
        mock_repo.get_external_apis_settings.return_value = {"scryfall_enabled": True}

        with patch("backend.api.routes.settings_routes.get_user_settings_repo", return_value=mock_repo):
            response = client.get("/api/settings/external-apis")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["scryfall_enabled"])

    def test_503_when_no_postgres(self):
        with patch("backend.api.routes.settings_routes.get_user_settings_repo", return_value=None):
            response = client.get("/api/settings/external-apis")
            self.assertEqual(response.status_code, 503)


class TestPutExternalApisSettings(unittest.TestCase):
    """Test PUT /api/settings/external-apis."""

    def test_enable_scryfall(self):
        mock_repo = MagicMock()
        mock_repo.get_external_apis_settings.return_value = {"scryfall_enabled": True}

        with patch("backend.api.routes.settings_routes.get_user_settings_repo", return_value=mock_repo):
            response = client.put(
                "/api/settings/external-apis",
                json={"scryfall_enabled": True},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["scryfall_enabled"])
            mock_repo.update_external_apis_settings.assert_called_once_with(
                1, {"scryfall_enabled": True}
            )

    def test_disable_scryfall(self):
        mock_repo = MagicMock()
        mock_repo.get_external_apis_settings.return_value = {"scryfall_enabled": False}

        with patch("backend.api.routes.settings_routes.get_user_settings_repo", return_value=mock_repo):
            response = client.put(
                "/api/settings/external-apis",
                json={"scryfall_enabled": False},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["scryfall_enabled"])

    def test_missing_required_field_returns_error(self):
        mock_repo = MagicMock()
        with patch("backend.api.routes.settings_routes.get_user_settings_repo", return_value=mock_repo):
            # Send empty body — scryfall_enabled is required
            response = client.put(
                "/api/settings/external-apis",
                json={},
            )
            # App has a custom validation handler returning 400 (not default 422)
            self.assertIn(response.status_code, (400, 422))


class TestCardFetcherBugRegression(unittest.TestCase):
    """Regression test: CardFetcher must receive (config.scryfall, config.openai)."""

    def test_importer_creates_cardfetcher_with_correct_args(self):
        """Verify CardFetcher is instantiated with config.scryfall and config.openai."""
        from backend.api.services.importer_service import ImporterService

        mock_repo = MagicMock()
        service = ImporterService(repo=mock_repo, user_id=1, mode="merge")

        # Mock all external dependencies
        mock_config = MagicMock()
        mock_config.scryfall = MagicMock(name="scryfall_config")
        mock_config.openai = MagicMock(name="openai_config")

        mock_catalog_repo = MagicMock()
        mock_catalog_repo.search_by_name.return_value = [{"name": "TestCard", "type_line": "Creature"}]

        mock_settings_repo = MagicMock()
        mock_settings_repo.get_external_apis_settings.return_value = {"scryfall_enabled": True}

        # CardFetcher is imported inside _run_import via `from deckdex.card_fetcher import CardFetcher`
        # so we patch at the source module
        with patch("backend.api.services.importer_service.load_config", return_value=mock_config), \
             patch("deckdex.card_fetcher.CardFetcher") as MockCardFetcher, \
             patch("backend.api.dependencies.get_catalog_repo", return_value=mock_catalog_repo), \
             patch("backend.api.dependencies.get_user_settings_repo", return_value=mock_settings_repo):

            parsed_cards = [{"name": "TestCard", "quantity": 1}]
            service._run_import(parsed_cards)

            # Verify CardFetcher was called with config.scryfall and config.openai
            MockCardFetcher.assert_called_once_with(mock_config.scryfall, mock_config.openai)


if __name__ == "__main__":
    unittest.main()
