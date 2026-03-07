"""
Extended API tests for DeckDex MTG backend.
Covers: jobs list, analytics/rarity, analytics/sets, analytics/color-identity,
analytics/cmc, analytics/type, cards/price-history, and cards color_identity filter.
Uses the same TestClient + mock approach as test_api.py.
"""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import backend.api.routes.analytics as _analytics_mod
from backend.api.dependencies import get_current_user_id
from backend.api.main import app

SAMPLE_CARDS = [
    {
        "name": "Lightning Bolt",
        "rarity": "common",
        "type": "Instant",
        "set_name": "M10",
        "price": "0.5",
        "color_identity": "R",
    },
    {
        "name": "Counterspell",
        "rarity": "common",
        "type": "Instant",
        "set_name": "M10",
        "price": "1.2",
        "color_identity": "U",
    },
    {
        "name": "Black Lotus",
        "rarity": "rare",
        "type": "Artifact",
        "set_name": "LEA",
        "price": "25000",
        "color_identity": "",
    },
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
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def test_jobs_returns_200(self):
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)

    def test_jobs_returns_list(self):
        response = self.client.get("/api/jobs")
        self.assertIsInstance(response.json(), list)


# ---------------------------------------------------------------------------
# Analytics — rarity
# ---------------------------------------------------------------------------
class TestAnalyticsRarity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def test_rarity_returns_200(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=[]),
        ):
            response = self.client.get("/api/analytics/rarity")
        self.assertEqual(response.status_code, 200)

    def test_rarity_returns_list(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/analytics/rarity")
        self.assertIsInstance(response.json(), list)

    def test_rarity_aggregates_correctly(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=RARITY_CARDS),
        ):
            response = self.client.get("/api/analytics/rarity")
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
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def test_sets_returns_200(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/analytics/sets")
        self.assertEqual(response.status_code, 200)

    def test_sets_contains_set_name_key(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/analytics/sets")
        data = response.json()
        self.assertTrue(len(data) > 0)
        self.assertIn("set_name", data[0])
        self.assertIn("count", data[0])

    def test_sets_aggregates_correctly(self):
        # Two cards from M10, one from LEA
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/analytics/sets")
        by_set = {item["set_name"]: item["count"] for item in response.json()}
        self.assertEqual(by_set.get("M10"), 2)
        self.assertEqual(by_set.get("LEA"), 1)


# ---------------------------------------------------------------------------
# Cards — color_identity filter
# GET /api/cards/ now returns { items, total, limit, offset }
# ---------------------------------------------------------------------------
class TestCardsColorFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def test_cards_color_identity_filter(self):
        with (
            patch("backend.api.routes.cards.get_collection_repo", return_value=None),
            patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/cards?color_identity=U")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        items = data["items"]
        # Only Counterspell has color_identity "U"
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "Counterspell")

    def test_cards_color_identity_excludes_colorless(self):
        with (
            patch("backend.api.routes.cards.get_collection_repo", return_value=None),
            patch("backend.api.routes.cards.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/cards?color_identity=R")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        items = data["items"]
        names = [c["name"] for c in items]
        self.assertIn("Lightning Bolt", names)
        self.assertNotIn("Counterspell", names)
        self.assertNotIn("Black Lotus", names)


# ---------------------------------------------------------------------------
# Type-specific fixture cards
# ---------------------------------------------------------------------------
TYPE_CARDS = [
    {"name": "Goblin Guide", "type": "Creature — Goblin Scout", "rarity": "rare", "set_name": "ZEN", "price": "5"},
    {"name": "Sol Ring", "type": "Artifact", "rarity": "uncommon", "set_name": "C21", "price": "2"},
    {"name": "Swords to Plowshares", "type": "Instant", "rarity": "uncommon", "set_name": "EMA", "price": "3"},
    {"name": "Unknown Card", "type": "", "rarity": "common", "set_name": "M10", "price": "0.1"},
    {
        "name": "Golem Artisan",
        "type": "Artifact Creature — Golem",
        "rarity": "uncommon",
        "set_name": "SOM",
        "price": "1",
    },
]


# ---------------------------------------------------------------------------
# Analytics — color-identity
# ---------------------------------------------------------------------------
class TestAnalyticsColorIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def setUp(self):
        _analytics_mod._analytics_cache.clear()

    def test_color_identity_returns_200(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=[]),
        ):
            response = self.client.get("/api/analytics/color-identity")
        self.assertEqual(response.status_code, 200)

    def test_color_identity_response_shape(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/analytics/color-identity")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        for item in data:
            self.assertIn("color_identity", item)
            self.assertIn("count", item)
            self.assertIsInstance(item["color_identity"], str)
            self.assertIsInstance(item["count"], int)

    def test_color_identity_aggregates_correctly(self):
        fixture = [
            {"name": "Lightning Bolt", "color_identity": "R", "rarity": "common", "set_name": "M10", "price": "1"},
            {"name": "Chain Lightning", "color_identity": "R", "rarity": "common", "set_name": "LEA", "price": "1"},
            {"name": "Counterspell", "color_identity": "U", "rarity": "common", "set_name": "M10", "price": "1"},
        ]
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=fixture),
        ):
            response = self.client.get("/api/analytics/color-identity")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        by_identity = {item["color_identity"]: item["count"] for item in data}
        # "R" normalizes to "R" (Monocolor Red)
        self.assertEqual(by_identity.get("R"), 2)
        self.assertEqual(by_identity.get("U"), 1)


# ---------------------------------------------------------------------------
# Analytics — cmc
# ---------------------------------------------------------------------------
class TestAnalyticsCmc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def setUp(self):
        _analytics_mod._analytics_cache.clear()

    def test_cmc_returns_200(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=[]),
        ):
            response = self.client.get("/api/analytics/cmc")
        self.assertEqual(response.status_code, 200)

    def test_cmc_response_shape(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=SAMPLE_CARDS),
        ):
            response = self.client.get("/api/analytics/cmc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        for item in data:
            self.assertIn("cmc", item)
            self.assertIn("count", item)
            self.assertIsInstance(item["cmc"], str)
            self.assertIsInstance(item["count"], int)

    def test_cmc_null_maps_to_unknown(self):
        fixture = [{"name": "Token", "cmc": None, "rarity": "common", "set_name": "M10", "price": "0"}]
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=fixture),
        ):
            response = self.client.get("/api/analytics/cmc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        cmc_values = [item["cmc"] for item in data]
        self.assertIn("Unknown", cmc_values)

    def test_cmc_seven_plus_bucket(self):
        fixture = [{"name": "Emrakul", "cmc": 8, "rarity": "mythic", "set_name": "ROE", "price": "5"}]
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=fixture),
        ):
            response = self.client.get("/api/analytics/cmc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        cmc_values = [item["cmc"] for item in data]
        self.assertIn("7+", cmc_values)

    def test_cmc_bucket_ordering(self):
        fixture = [
            {"name": "A", "cmc": 0, "rarity": "common", "set_name": "M10", "price": "0"},
            {"name": "B", "cmc": 3, "rarity": "common", "set_name": "M10", "price": "0"},
            {"name": "C", "cmc": 8, "rarity": "common", "set_name": "M10", "price": "0"},
            {"name": "D", "cmc": None, "rarity": "common", "set_name": "M10", "price": "0"},
        ]
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=fixture),
        ):
            response = self.client.get("/api/analytics/cmc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        cmc_order = [item["cmc"] for item in data]
        self.assertEqual(cmc_order, ["0", "3", "7+", "Unknown"])


# ---------------------------------------------------------------------------
# Analytics — type
# ---------------------------------------------------------------------------
class TestAnalyticsType(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def setUp(self):
        _analytics_mod._analytics_cache.clear()

    def test_type_returns_200(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=[]),
        ):
            response = self.client.get("/api/analytics/type")
        self.assertEqual(response.status_code, 200)

    def test_type_response_shape(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=TYPE_CARDS),
        ):
            response = self.client.get("/api/analytics/type")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        for item in data:
            self.assertIn("type_line", item)
            self.assertIn("count", item)
            self.assertIsInstance(item["type_line"], str)
            self.assertIsInstance(item["count"], int)

    def test_type_creature_extraction(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=TYPE_CARDS),
        ):
            response = self.client.get("/api/analytics/type")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        by_type = {item["type_line"]: item["count"] for item in data}
        # Goblin Guide ("Creature — Goblin Scout") and Golem Artisan ("Artifact Creature — Golem") both map to Creature
        self.assertEqual(by_type.get("Creature"), 2)

    def test_type_other_for_empty_type(self):
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=TYPE_CARDS),
        ):
            response = self.client.get("/api/analytics/type")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        by_type = {item["type_line"]: item["count"] for item in data}
        # "Unknown Card" with type="" maps to "Other"
        self.assertEqual(by_type.get("Other"), 1)

    def test_type_priority_creature_over_artifact(self):
        fixture = [
            {
                "name": "Golem Artisan",
                "type": "Artifact Creature — Golem",
                "rarity": "uncommon",
                "set_name": "SOM",
                "price": "1",
            }
        ]
        with (
            patch("backend.api.routes.analytics.get_collection_repo", return_value=None),
            patch("backend.api.routes.analytics.get_cached_collection", return_value=fixture),
        ):
            response = self.client.get("/api/analytics/type")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["type_line"], "Creature")


# ---------------------------------------------------------------------------
# Cards — price history
# ---------------------------------------------------------------------------
class TestCardPriceHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_current_user_id, None)

    def test_price_history_501_without_postgres(self):
        with patch("backend.api.routes.cards.get_collection_repo", return_value=None):
            response = self.client.get("/api/cards/1/price-history")
        self.assertEqual(response.status_code, 501)

    def test_price_history_404_card_not_found(self):
        mock_repo = MagicMock()
        mock_repo.get_card_by_id.return_value = None
        with patch("backend.api.routes.cards.get_collection_repo", return_value=mock_repo):
            response = self.client.get("/api/cards/99/price-history")
        self.assertEqual(response.status_code, 404)

    def test_price_history_200_with_data(self):
        mock_repo = MagicMock()
        mock_repo.get_card_by_id.return_value = {"id": 1, "name": "Lightning Bolt"}
        mock_repo.get_price_history.return_value = [
            {"recorded_at": "2024-01-01T00:00:00", "price": 0.5, "source": "scryfall", "currency": "eur"}
        ]
        with patch("backend.api.routes.cards.get_collection_repo", return_value=mock_repo):
            response = self.client.get("/api/cards/1/price-history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("card_id", data)
        self.assertIn("currency", data)
        self.assertIn("points", data)
        self.assertIsInstance(data["points"], list)
        self.assertEqual(len(data["points"]), 1)
        point = data["points"][0]
        self.assertIn("recorded_at", point)
        self.assertIn("price", point)
        self.assertIn("source", point)
        self.assertIn("currency", point)

    def test_price_history_200_empty_history(self):
        mock_repo = MagicMock()
        mock_repo.get_card_by_id.return_value = {"id": 1, "name": "Lightning Bolt"}
        mock_repo.get_price_history.return_value = []
        with patch("backend.api.routes.cards.get_collection_repo", return_value=mock_repo):
            response = self.client.get("/api/cards/1/price-history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["points"], [])
