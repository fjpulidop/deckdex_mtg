"""Tests for CatalogRepository: search, autocomplete, upsert, sync state (mocked DB)."""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from deckdex.catalog.repository import CatalogRepository


def _make_repo():
    """Create a CatalogRepository with a mocked engine."""
    with patch.object(CatalogRepository, "__init__", lambda self, url: None):
        repo = CatalogRepository.__new__(CatalogRepository)
        repo._url = "postgresql://fake"
        repo._eng = MagicMock()
        return repo


class TestSearchByName(unittest.TestCase):
    """Test CatalogRepository.search_by_name()."""

    def test_returns_matching_cards(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)

        fake_rows = [
            {"scryfall_id": "aaa", "name": "Lightning Bolt", "rarity": "common"},
            {"scryfall_id": "bbb", "name": "Lightning Helix", "rarity": "uncommon"},
        ]
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = fake_rows

        results = repo.search_by_name("Lightning", limit=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "Lightning Bolt")
        self.assertEqual(results[1]["name"], "Lightning Helix")

        # Verify the query was called with the right pattern
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        self.assertEqual(params["pattern"], "%Lightning%")
        self.assertEqual(params["lim"], 10)

    def test_empty_query_returns_empty(self):
        repo = _make_repo()
        self.assertEqual(repo.search_by_name(""), [])
        self.assertEqual(repo.search_by_name("  "), [])

    def test_no_matches_returns_empty(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = []

        results = repo.search_by_name("Nonexistent")
        self.assertEqual(results, [])

    def test_respects_limit(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = [
            {"scryfall_id": "aaa", "name": "Card A"},
        ]

        repo.search_by_name("Card", limit=1)
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        self.assertEqual(params["lim"], 1)


class TestAutocomplete(unittest.TestCase):
    """Test CatalogRepository.autocomplete()."""

    def test_returns_matching_names(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("Lightning Bolt",),
            ("Lightning Helix",),
        ]

        results = repo.autocomplete("Li", limit=20)
        self.assertEqual(results, ["Lightning Bolt", "Lightning Helix"])

        # Verify prefix pattern (starts with, not contains)
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        self.assertEqual(params["pattern"], "Li%")

    def test_short_query_returns_empty(self):
        repo = _make_repo()
        self.assertEqual(repo.autocomplete(""), [])
        self.assertEqual(repo.autocomplete("L"), [])

    def test_respects_limit(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = []

        repo.autocomplete("Li", limit=5)
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        self.assertEqual(params["lim"], 5)


class TestUpsertCards(unittest.TestCase):
    """Test CatalogRepository.upsert_cards()."""

    def _sample_card(self, scryfall_id="abc-123", name="Lightning Bolt"):
        return {
            "scryfall_id": scryfall_id,
            "oracle_id": "oracle-1",
            "name": name,
            "type_line": "Instant",
            "oracle_text": "Deals 3 damage.",
            "mana_cost": "{R}",
            "cmc": 1.0,
            "colors": "R",
            "color_identity": "R",
            "power": None,
            "toughness": None,
            "rarity": "common",
            "set_id": "m10",
            "set_name": "Magic 2010",
            "collector_number": "146",
            "release_date": "2009-07-17",
            "image_uri_small": "https://example.com/small.jpg",
            "image_uri_normal": "https://example.com/normal.jpg",
            "image_uri_large": "https://example.com/large.jpg",
            "prices_eur": "1.50",
            "prices_usd": "2.00",
            "prices_usd_foil": "5.00",
            "edhrec_rank": 5,
            "keywords": "Damage",
            "legalities": '{"modern": "legal"}',
            "scryfall_uri": "https://scryfall.com/card/m10/146",
        }

    def test_inserts_batch(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)

        cards = [self._sample_card("id-1", "Card A"), self._sample_card("id-2", "Card B")]
        count = repo.upsert_cards(cards)

        self.assertEqual(count, 2)
        # execute called once per card + commit
        self.assertEqual(mock_conn.execute.call_count, 2)
        mock_conn.commit.assert_called_once()

    def test_empty_batch_returns_zero(self):
        repo = _make_repo()
        self.assertEqual(repo.upsert_cards([]), 0)

    def test_upsert_sql_contains_on_conflict(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)

        repo.upsert_cards([self._sample_card()])
        call_args = mock_conn.execute.call_args
        sql_text = str(call_args[0][0])
        self.assertIn("ON CONFLICT", sql_text)
        self.assertIn("scryfall_id", sql_text)


class TestSyncState(unittest.TestCase):
    """Test CatalogRepository.get_sync_state() and update_sync_state()."""

    def test_get_sync_state_returns_row(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)

        now = datetime(2026, 3, 1, 12, 0, 0)
        mock_conn.execute.return_value.mappings.return_value.fetchone.return_value = {
            "id": 1,
            "status": "syncing_data",
            "total_cards": 1000,
            "total_images_downloaded": 500,
            "last_bulk_sync": now,
            "last_image_cursor": "abc",
            "error_message": None,
            "updated_at": now,
        }

        state = repo.get_sync_state()
        self.assertEqual(state["status"], "syncing_data")
        self.assertEqual(state["total_cards"], 1000)
        self.assertEqual(state["total_images_downloaded"], 500)
        # Datetimes serialized to ISO strings
        self.assertEqual(state["last_bulk_sync"], now.isoformat())
        self.assertEqual(state["updated_at"], now.isoformat())

    def test_get_sync_state_no_row_returns_default(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.fetchone.return_value = None

        state = repo.get_sync_state()
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["total_cards"], 0)

    def test_update_sync_state_calls_correct_sql(self):
        repo = _make_repo()
        mock_conn = MagicMock()
        repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)

        repo.update_sync_state(status="syncing_images", total_cards=5000)
        call_args = mock_conn.execute.call_args
        sql_text = str(call_args[0][0])
        self.assertIn("status", sql_text)
        self.assertIn("total_cards", sql_text)
        self.assertIn("updated_at", sql_text)
        params = call_args[0][1]
        self.assertEqual(params["status"], "syncing_images")
        self.assertEqual(params["total_cards"], 5000)
        mock_conn.commit.assert_called_once()

    def test_update_sync_state_empty_fields_noop(self):
        repo = _make_repo()
        # Should return without touching the DB
        repo.update_sync_state()
        # engine.connect() should not have been called
        repo._eng.connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
