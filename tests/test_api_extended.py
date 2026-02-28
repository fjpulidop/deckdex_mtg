"""
Extended API tests for DeckDex MTG backend.
Covers: jobs list, analytics/rarity, analytics/sets, and cards color_identity filter.
Uses the same TestClient + mock approach as test_api.py.
"""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies import get_current_user_id

app.dependency_overrides[get_current_user_id] = lambda: 1

client = TestClient(app)

SAMPLE_CARDS = [
    {"name": "Lightning Bolt", "rarity": "common", "type": "Instant", "set_name": "M10",
     "price": "0.5", "color_identity": "R"},
    {"name": "Counterspell", "rarity": "common", "type": "Instant", "set_name": "M10",
     "price": "1.2", "color_identity": "U"},
    {"name": "Black Lotus", "rarity": "rare", "type": "Artifact", "set_name": "LEA",
     "price": "25000", "color_identity": ""},
]

# Two commons, one rare — for rarity aggregation assertions
RARITY_CARDS = [
    {"name": "A", "rarity": "common", "type": "Instant", "set_name": "M10", "price": "1"},
    {"name": "B", "rarity": "common", "type": "Creature", "set_name": "M10", "price": "2"},
    {"name": "C", "rarity": "rare", "type": "Artifact", "set_name": "LEA", "price": "10"},
]


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
class TestJobs(unittest.TestCase):
    def test_jobs_returns_200(self):
        response = client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)

    def test_jobs_returns_list(self):
        response = client.get("/api/jobs")
        self.assertIsInstance(response.json(), list)


# ---------------------------------------------------------------------------
# Analytics — rarity
# ---------------------------------------------------------------------------
class TestAnalyticsRarity(unittest.TestCase):
    def test_rarity_returns_200(self):
        with patch("backend.api.routes.analytics.get_cached_collection", return_value=[]):
            response = client.get("/api/analytics/rarity")
        self.assertEqual(response.status_code, 200)

    def test_rarity_returns_list(self):
        with patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/analytics/rarity")
        self.assertIsInstance(response.json(), list)

    def test_rarity_aggregates_correctly(self):
        with patch("backend.api.routes.analytics.get_cached_collection", return_value=RARITY_CARDS):
            response = client.get("/api/analytics/rarity")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Build a dict for easy lookup
        by_rarity = {item["rarity"]: item["count"] for item in data}
        self.assertEqual(by_rarity.get("common"), 2)
        self.assertEqual(by_rarity.get("rare"), 1)


# ---------------------------------------------------------------------------
# Analytics — sets
# ---------------------------------------------------------------------------
class TestAnalyticsSets(unittest.TestCase):
    def test_sets_returns_200(self):
        with patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/analytics/sets")
        self.assertEqual(response.status_code, 200)

    def test_sets_contains_set_name_key(self):
        with patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/analytics/sets")
        data = response.json()
        self.assertTrue(len(data) > 0)
        self.assertIn("set_name", data[0])
        self.assertIn("count", data[0])

    def test_sets_aggregates_correctly(self):
        # Two cards from M10, one from LEA
        with patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/analytics/sets")
        by_set = {item["set_name"]: item["count"] for item in response.json()}
        self.assertEqual(by_set.get("M10"), 2)
        self.assertEqual(by_set.get("LEA"), 1)


# ---------------------------------------------------------------------------
# Cards — color_identity filter
# ---------------------------------------------------------------------------
class TestCardsColorFilter(unittest.TestCase):
    def test_cards_color_identity_filter(self):
        with patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/cards?color_identity=U")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Only Counterspell has color_identity "U"
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Counterspell")

    def test_cards_color_identity_excludes_colorless(self):
        with patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS):
            response = client.get("/api/cards?color_identity=R")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        names = [c["name"] for c in data]
        self.assertIn("Lightning Bolt", names)
        self.assertNotIn("Counterspell", names)
        self.assertNotIn("Black Lotus", names)
