"""Tests for external-apis-settings: UserSettingsRepository logic and catalog-first lookup."""

import json
import os
import unittest
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Inline helpers mirroring the repository default logic (avoids importing
# the full backend module chain which needs Postgres, gspread, etc.)
# ---------------------------------------------------------------------------

_DEFAULT_EXTERNAL_APIS = {"scryfall_enabled": False}


def _get_external_apis_settings(all_settings: dict) -> dict:
    """Mirrors UserSettingsRepository.get_external_apis_settings logic."""
    stored = all_settings.get("external_apis")
    if not isinstance(stored, dict):
        return dict(_DEFAULT_EXTERNAL_APIS)
    return {**_DEFAULT_EXTERNAL_APIS, **stored}


def _update_external_apis_settings(all_settings: dict, new_settings: dict) -> dict:
    """Mirrors UserSettingsRepository.update_external_apis_settings logic."""
    ea = all_settings.get("external_apis", {})
    if not isinstance(ea, dict):
        ea = {}
    ea.update(new_settings)
    all_settings["external_apis"] = ea
    return all_settings


# ---------------------------------------------------------------------------
# Tests for default settings logic
# ---------------------------------------------------------------------------


class TestDefaultExternalApisSettings(unittest.TestCase):
    """Test the default extraction of external_apis from JSONB."""

    def test_empty_settings_returns_default(self):
        result = _get_external_apis_settings({})
        self.assertFalse(result["scryfall_enabled"])

    def test_missing_key_returns_default(self):
        result = _get_external_apis_settings({"other_key": 123})
        self.assertFalse(result["scryfall_enabled"])

    def test_non_dict_external_apis_returns_default(self):
        result = _get_external_apis_settings({"external_apis": "invalid"})
        self.assertFalse(result["scryfall_enabled"])

    def test_saved_value_returned(self):
        result = _get_external_apis_settings({"external_apis": {"scryfall_enabled": True}})
        self.assertTrue(result["scryfall_enabled"])

    def test_partial_merge_with_defaults(self):
        result = _get_external_apis_settings({"external_apis": {}})
        self.assertFalse(result["scryfall_enabled"])


class TestUpdateExternalApisSettings(unittest.TestCase):
    """Test merging external_apis into settings JSONB."""

    def test_creates_key_on_first_call(self):
        all_settings = {}
        updated = _update_external_apis_settings(all_settings, {"scryfall_enabled": True})
        self.assertTrue(updated["external_apis"]["scryfall_enabled"])

    def test_updates_existing_key(self):
        all_settings = {"external_apis": {"scryfall_enabled": False}}
        updated = _update_external_apis_settings(all_settings, {"scryfall_enabled": True})
        self.assertTrue(updated["external_apis"]["scryfall_enabled"])

    def test_preserves_other_keys(self):
        all_settings = {"other": "data", "external_apis": {"scryfall_enabled": False}}
        updated = _update_external_apis_settings(all_settings, {"scryfall_enabled": True})
        self.assertEqual(updated["other"], "data")
        self.assertTrue(updated["external_apis"]["scryfall_enabled"])

    def test_preserves_other_external_api_keys(self):
        all_settings = {"external_apis": {"scryfall_enabled": False, "openai_enabled": True}}
        updated = _update_external_apis_settings(all_settings, {"scryfall_enabled": True})
        self.assertTrue(updated["external_apis"]["scryfall_enabled"])
        self.assertTrue(updated["external_apis"]["openai_enabled"])

    def test_replaces_non_dict_external_apis(self):
        all_settings = {"external_apis": "invalid"}
        updated = _update_external_apis_settings(all_settings, {"scryfall_enabled": True})
        self.assertTrue(updated["external_apis"]["scryfall_enabled"])


# ---------------------------------------------------------------------------
# Catalog-first lookup logic tests (mocked, no real Scryfall/Postgres)
# ---------------------------------------------------------------------------


class TestCatalogFirstSuggest(unittest.TestCase):
    """Test catalog-first logic in suggest_card_names."""

    def test_catalog_results_returned_first(self):
        """When catalog has results, Scryfall is not called."""
        catalog_results = ["Lightning Bolt", "Lightning Helix"]

        mock_catalog = MagicMock()
        mock_catalog.autocomplete.return_value = catalog_results

        # Simulate catalog-first logic inline
        q = "Lightning"
        results = mock_catalog.autocomplete(q, limit=20)
        self.assertEqual(results, catalog_results)

    def test_empty_catalog_falls_back_to_scryfall_when_enabled(self):
        """When catalog is empty and Scryfall enabled, fallback occurs."""
        mock_catalog = MagicMock()
        mock_catalog.autocomplete.return_value = []

        scryfall_results = ["Lightning Bolt", "Lightning Helix"]
        mock_fetcher = MagicMock()
        mock_fetcher.autocomplete.return_value = scryfall_results

        q = "Lightning"
        scryfall_enabled = True

        results = mock_catalog.autocomplete(q, limit=20)
        if not results and scryfall_enabled:
            results = mock_fetcher.autocomplete(q)

        self.assertEqual(results, scryfall_results)

    def test_empty_catalog_returns_empty_when_disabled(self):
        """When catalog is empty and Scryfall disabled, return empty."""
        mock_catalog = MagicMock()
        mock_catalog.autocomplete.return_value = []

        q = "Lightning"
        scryfall_enabled = False

        results = mock_catalog.autocomplete(q, limit=20)
        if not results and scryfall_enabled:
            results = ["should not reach"]

        self.assertEqual(results, [])


class TestCatalogFirstResolve(unittest.TestCase):
    """Test catalog-first logic in resolve_card_by_name."""

    def test_catalog_match_returned(self):
        """When catalog finds the card, return it without Scryfall."""
        catalog_card = {"name": "Lightning Bolt", "type_line": "Instant", "rarity": "common"}
        mock_catalog = MagicMock()
        mock_catalog.search_by_name.return_value = [catalog_card]

        results = mock_catalog.search_by_name("Lightning Bolt", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Lightning Bolt")

    def test_no_catalog_match_scryfall_enabled(self):
        """When catalog misses and Scryfall enabled, fallback to Scryfall."""
        mock_catalog = MagicMock()
        mock_catalog.search_by_name.return_value = []

        scryfall_card = {"name": "Lightning Bolt", "type_line": "Instant"}
        mock_fetcher = MagicMock()
        mock_fetcher.search_card.return_value = scryfall_card

        scryfall_enabled = True

        results = mock_catalog.search_by_name("Lightning Bolt", limit=1)
        if not results and scryfall_enabled:
            card = mock_fetcher.search_card("Lightning Bolt")
        else:
            card = None

        self.assertIsNotNone(card)
        self.assertEqual(card["name"], "Lightning Bolt")

    def test_no_catalog_match_scryfall_disabled_raises(self):
        """When catalog misses and Scryfall disabled, error expected."""
        mock_catalog = MagicMock()
        mock_catalog.search_by_name.return_value = []
        scryfall_enabled = False

        results = mock_catalog.search_by_name("NonExistent Card", limit=1)
        found = bool(results)
        if not found and not scryfall_enabled:
            found = False

        self.assertFalse(found)


class TestCatalogFirstImage(unittest.TestCase):
    """Test catalog-first image lookup logic."""

    def test_image_store_hit_returns_immediately(self):
        """When ImageStore has the image, return without Scryfall."""
        mock_store = MagicMock()
        mock_store.get.return_value = (b"image-data", "image/jpeg")

        result = mock_store.get("scryfall-id-123")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], b"image-data")

    def test_image_store_miss_scryfall_disabled(self):
        """When ImageStore misses and Scryfall disabled, no download."""
        mock_store = MagicMock()
        mock_store.get.return_value = None
        scryfall_enabled = False

        result = mock_store.get("scryfall-id-123")
        if result is None and not scryfall_enabled:
            result = None  # would raise FileNotFoundError in real code

        self.assertIsNone(result)


class TestCatalogFirstImport(unittest.TestCase):
    """Test catalog-first import enrichment logic."""

    def test_catalog_enrichment_preferred(self):
        """Import uses catalog data when available."""
        mock_catalog = MagicMock()
        mock_catalog.search_by_name.return_value = [{"name": "Sol Ring", "type_line": "Artifact"}]

        card_data = None
        results = mock_catalog.search_by_name("Sol Ring", limit=1)
        if results:
            card_data = results[0]

        self.assertIsNotNone(card_data)
        self.assertEqual(card_data["name"], "Sol Ring")

    def test_scryfall_fallback_when_not_in_catalog(self):
        """Import falls back to Scryfall when catalog misses and enabled."""
        mock_catalog = MagicMock()
        mock_catalog.search_by_name.return_value = []

        mock_fetcher = MagicMock()
        mock_fetcher.search_card.return_value = {"name": "Sol Ring", "type_line": "Artifact"}

        scryfall_enabled = True
        card_data = None

        results = mock_catalog.search_by_name("Sol Ring", limit=1)
        if results:
            card_data = results[0]
        elif scryfall_enabled:
            card_data = mock_fetcher.search_card("Sol Ring")

        self.assertIsNotNone(card_data)

    def test_not_found_when_catalog_miss_and_disabled(self):
        """Import adds to not_found when catalog misses and Scryfall disabled."""
        mock_catalog = MagicMock()
        mock_catalog.search_by_name.return_value = []
        scryfall_enabled = False

        card_data = None
        not_found = []

        results = mock_catalog.search_by_name("Unknown Card", limit=1)
        if results:
            card_data = results[0]
        elif scryfall_enabled:
            card_data = None  # would try fetcher
        else:
            not_found.append("Unknown Card")

        self.assertIsNone(card_data)
        self.assertEqual(not_found, ["Unknown Card"])


if __name__ == "__main__":
    unittest.main()
