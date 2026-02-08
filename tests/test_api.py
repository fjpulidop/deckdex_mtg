"""
API tests for DeckDex MTG backend.
Uses FastAPI TestClient with mocked get_cached_collection so no DB or Google Sheets required.
Requires httpx<0.28 for TestClient compatibility (see requirements.txt).
"""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

# Import app after potential path setup; run tests from repo root
from backend.api.main import app

client = TestClient(app)

# Shared fixture: cards with parseable prices for stats and filter tests
SAMPLE_CARDS = [
    {"name": "Lightning Bolt", "rarity": "common", "type": "Instant", "set_name": "M10", "price": "0.5"},
    {"name": "Black Lotus", "rarity": "mythic rare", "type": "Artifact", "set_name": "LEA", "price": "25000"},
    {"name": "Counterspell", "rarity": "common", "type": "Instant", "set_name": "M10", "price": "1.2"},
]


# ---------------------------------------------------------------------------
# Health (no mocks)
# ---------------------------------------------------------------------------
class TestHealth(unittest.TestCase):
    def test_health_returns_200(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)

    def test_health_body_has_service_version_status(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("service", data)
        self.assertIn("version", data)
        self.assertIn("status", data)
        self.assertEqual(data["service"], "DeckDex MTG API")
        self.assertEqual(data["version"], "0.1.0")
        self.assertEqual(data["status"], "healthy")


# ---------------------------------------------------------------------------
# Stats (patch get_cached_collection in backend.api.routes.stats)
# ---------------------------------------------------------------------------
class TestStats(unittest.TestCase):
    def setUp(self):
        from backend.api.routes.stats import clear_stats_cache
        clear_stats_cache()

    def test_stats_empty_collection_returns_200_and_zeros(self):
        with patch("backend.api.routes.stats.get_cached_collection", return_value=[]):
            response = client.get("/api/stats/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["total_cards"], 0)
            self.assertEqual(data["total_value"], 0.0)
            self.assertEqual(data["average_price"], 0.0)
            self.assertIn("last_updated", data)
            self.assertIsInstance(data["last_updated"], str)

    def test_stats_non_empty_collection_returns_aggregates(self):
        with patch("backend.api.routes.stats.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/stats/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["total_cards"], 3)
            self.assertAlmostEqual(data["total_value"], 25001.7, places=1)
            self.assertAlmostEqual(data["average_price"], 8333.9, places=1)
            self.assertIn("last_updated", data)

    def test_stats_with_filter_returns_filtered_subset(self):
        with patch("backend.api.routes.stats.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/stats/", params={"rarity": "common"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["total_cards"], 2)  # Lightning Bolt, Counterspell
            self.assertAlmostEqual(data["total_value"], 1.7, places=1)  # 0.5 + 1.2


# ---------------------------------------------------------------------------
# Cards list (patch get_cached_collection in backend.api.routes.cards)
# ---------------------------------------------------------------------------
class TestCardsList(unittest.TestCase):
    def test_cards_empty_collection_returns_200_empty_array(self):
        with patch("backend.api.routes.cards.get_cached_collection", return_value=[]):
            response = client.get("/api/cards/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

    def test_cards_non_empty_collection_returns_cards(self):
        with patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/cards/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 3)
            names = [c.get("name") for c in data]
            self.assertIn("Lightning Bolt", names)
            self.assertIn("Black Lotus", names)
            self.assertIn("Counterspell", names)

    def test_cards_limit_offset_pagination(self):
        with patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/cards/", params={"limit": 2, "offset": 1})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data), 2)
            # Second and third card (offset 1, limit 2): Black Lotus, Counterspell
            names = [c.get("name") for c in data]
            self.assertEqual(names, ["Black Lotus", "Counterspell"])

    def test_cards_with_filter_returns_only_matching(self):
        with patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/cards/", params={"set_name": "M10"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data), 2)  # Lightning Bolt, Counterspell
            for c in data:
                self.assertEqual(c.get("set_name"), "M10")
