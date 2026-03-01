"""Tests for CatalogConfig and CatalogSyncJob parsing logic."""

import json
import unittest

from deckdex.config import CatalogConfig


class TestCatalogConfig(unittest.TestCase):
    """Test CatalogConfig dataclass validation."""

    def test_defaults(self):
        cfg = CatalogConfig()
        self.assertEqual(cfg.image_dir, "data/images")
        self.assertEqual(cfg.image_size, "normal")

    def test_valid_sizes(self):
        for size in ("small", "normal", "large"):
            cfg = CatalogConfig(image_size=size)
            self.assertEqual(cfg.image_size, size)

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            CatalogConfig(image_size="huge")


class TestScryfallCardParsing(unittest.TestCase):
    """Test the _parse_scryfall_card method of CatalogSyncJob."""

    def _parse(self, card_dict):
        """Helper to call the parser without a full job instance."""
        from deckdex.catalog.sync_job import CatalogSyncJob
        # Create a minimal instance (repos won't be used)
        job = CatalogSyncJob.__new__(CatalogSyncJob)
        return job._parse_scryfall_card(card_dict)

    def test_basic_card(self):
        card = {
            "id": "abc-123",
            "oracle_id": "oracle-1",
            "name": "Lightning Bolt",
            "type_line": "Instant",
            "oracle_text": "Lightning Bolt deals 3 damage to any target.",
            "mana_cost": "{R}",
            "cmc": 1.0,
            "colors": ["R"],
            "color_identity": ["R"],
            "power": None,
            "toughness": None,
            "rarity": "common",
            "set": "m10",
            "set_name": "Magic 2010",
            "collector_number": "146",
            "released_at": "2009-07-17",
            "image_uris": {
                "small": "https://example.com/small.jpg",
                "normal": "https://example.com/normal.jpg",
                "large": "https://example.com/large.jpg",
            },
            "prices": {"eur": "1.50", "usd": "2.00", "usd_foil": "5.00"},
            "edhrec_rank": 5,
            "keywords": ["Damage"],
            "legalities": {"standard": "not_legal", "modern": "legal"},
            "scryfall_uri": "https://scryfall.com/card/m10/146",
        }
        result = self._parse(card)
        self.assertIsNotNone(result)
        self.assertEqual(result["scryfall_id"], "abc-123")
        self.assertEqual(result["name"], "Lightning Bolt")
        self.assertEqual(result["colors"], "R")
        self.assertEqual(result["color_identity"], "R")
        self.assertEqual(result["image_uri_normal"], "https://example.com/normal.jpg")
        self.assertEqual(result["prices_eur"], "1.50")
        self.assertEqual(result["edhrec_rank"], 5)
        self.assertEqual(result["keywords"], "Damage")
        # legalities stored as JSON string
        legalities = json.loads(result["legalities"])
        self.assertEqual(legalities["modern"], "legal")

    def test_double_faced_card(self):
        card = {
            "id": "dfc-456",
            "name": "Delver of Secrets // Insectile Aberration",
            "image_uris": None,
            "card_faces": [
                {
                    "name": "Delver of Secrets",
                    "image_uris": {
                        "normal": "https://example.com/front.jpg",
                        "small": "https://example.com/front-small.jpg",
                    },
                },
                {
                    "name": "Insectile Aberration",
                    "image_uris": {
                        "normal": "https://example.com/back.jpg",
                    },
                },
            ],
            "type_line": "Creature — Human Wizard // Creature — Human Insect",
            "colors": ["U"],
            "color_identity": ["U"],
        }
        result = self._parse(card)
        self.assertIsNotNone(result)
        # Should use first face's image URIs
        self.assertEqual(result["image_uri_normal"], "https://example.com/front.jpg")

    def test_missing_id_returns_none(self):
        self.assertIsNone(self._parse({"name": "No ID"}))

    def test_missing_name_returns_none(self):
        self.assertIsNone(self._parse({"id": "no-name"}))

    def test_empty_card(self):
        self.assertIsNone(self._parse({}))


if __name__ == "__main__":
    unittest.main()
