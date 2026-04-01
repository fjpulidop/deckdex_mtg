"""Tests for PostgresCollectionRepository variant-related methods:
- get_distinct_card_names
- get_cards_by_name

All tests mock the SQLAlchemy engine so no real database is required.
"""

import unittest
from unittest.mock import MagicMock, patch

from deckdex.storage.repository import PostgresCollectionRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo() -> PostgresCollectionRepository:
    """Create a PostgresCollectionRepository with a MagicMock engine injected.

    Bypasses the constructor URL validation by providing engine directly.
    """
    repo = PostgresCollectionRepository(database_url="", engine=MagicMock())
    return repo


def _setup_conn(repo: PostgresCollectionRepository):
    """Return mock connection context manager hooked to repo._eng.connect()."""
    mock_conn = MagicMock()
    repo._eng.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    repo._eng.connect.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn


# ---------------------------------------------------------------------------
# get_distinct_card_names
# ---------------------------------------------------------------------------


class TestGetDistinctCardNames(unittest.TestCase):
    """Tests for PostgresCollectionRepository.get_distinct_card_names."""

    def test_returns_names_and_total(self):
        """Returns a tuple of (list_of_names, total_count)."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)

        # First execute call → count, second → names
        count_result = MagicMock()
        count_result.scalar.return_value = 2

        name_row1, name_row2 = MagicMock(), MagicMock()
        name_row1.__getitem__ = MagicMock(side_effect=lambda i: "Lightning Bolt")
        name_row2.__getitem__ = MagicMock(side_effect=lambda i: "Counterspell")

        names_result = MagicMock()
        names_result.fetchall.return_value = [name_row1, name_row2]

        mock_conn.execute.side_effect = [count_result, names_result]

        names, total = repo.get_distinct_card_names(user_id=1)

        self.assertIsInstance(names, list)
        self.assertIsInstance(total, int)
        self.assertEqual(total, 2)
        self.assertEqual(len(names), 2)

    def test_empty_collection_returns_empty_list_and_zero(self):
        """When no cards exist, returns ([], 0)."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        names_result = MagicMock()
        names_result.fetchall.return_value = []

        mock_conn.execute.side_effect = [count_result, names_result]

        names, total = repo.get_distinct_card_names(user_id=1)

        self.assertEqual(names, [])
        self.assertEqual(total, 0)

    def test_search_filter_passed_to_query(self):
        """When search is provided, two execute calls are made (count + names)."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        name_row = MagicMock()
        name_row.__getitem__ = MagicMock(side_effect=lambda i: "Lightning Bolt")
        names_result = MagicMock()
        names_result.fetchall.return_value = [name_row]

        mock_conn.execute.side_effect = [count_result, names_result]

        names, total = repo.get_distinct_card_names(user_id=1, search="bolt")

        # Both count and name queries should have been called
        self.assertEqual(mock_conn.execute.call_count, 2)

        # Search param should appear in the params passed to execute
        all_params = [call[0][1] for call in mock_conn.execute.call_args_list]
        search_values = [p.get("search") for p in all_params if "search" in p]
        self.assertTrue(any("bolt" in str(v) for v in search_values))

    def test_blank_search_ignored(self):
        """Blank or whitespace-only search string is treated as no filter."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)

        count_result = MagicMock()
        count_result.scalar.return_value = 0
        names_result = MagicMock()
        names_result.fetchall.return_value = []
        mock_conn.execute.side_effect = [count_result, names_result]

        # No error should occur for blank search
        names, total = repo.get_distinct_card_names(user_id=1, search="   ")

        # search param should NOT appear in the query params (blank is stripped)
        all_params = [call[0][1] for call in mock_conn.execute.call_args_list]
        for params in all_params:
            self.assertNotIn("search", params)

    def test_limit_and_offset_applied(self):
        """limit and offset are forwarded to the names query."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)

        count_result = MagicMock()
        count_result.scalar.return_value = 100
        names_result = MagicMock()
        names_result.fetchall.return_value = []
        mock_conn.execute.side_effect = [count_result, names_result]

        repo.get_distinct_card_names(user_id=1, limit=10, offset=30)

        # The names query params should include limit=10, offset=30
        names_call_params = mock_conn.execute.call_args_list[1][0][1]
        self.assertEqual(names_call_params["limit"], 10)
        self.assertEqual(names_call_params["offset"], 30)

    def test_user_id_included_in_both_queries(self):
        """user_id is passed as a parameter to both count and name queries."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)

        count_result = MagicMock()
        count_result.scalar.return_value = 0
        names_result = MagicMock()
        names_result.fetchall.return_value = []
        mock_conn.execute.side_effect = [count_result, names_result]

        repo.get_distinct_card_names(user_id=99)

        all_params = [call[0][1] for call in mock_conn.execute.call_args_list]
        for params in all_params:
            self.assertEqual(params["user_id"], 99)

    def test_none_count_returns_zero_total(self):
        """If scalar() returns None (edge case), total is coerced to 0."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)

        count_result = MagicMock()
        count_result.scalar.return_value = None
        names_result = MagicMock()
        names_result.fetchall.return_value = []
        mock_conn.execute.side_effect = [count_result, names_result]

        names, total = repo.get_distinct_card_names(user_id=1)

        self.assertEqual(total, 0)


# ---------------------------------------------------------------------------
# get_cards_by_name
# ---------------------------------------------------------------------------


class TestGetCardsByName(unittest.TestCase):
    """Tests for PostgresCollectionRepository.get_cards_by_name."""

    def _make_db_row(self, **kwargs):
        """Return a dict simulating a DB row mapping."""
        defaults = {
            "id": 1,
            "name": "Lightning Bolt",
            "type_line": "Instant",
            "set_name": "M10",
            "finish": "nonfoil",
            "variant_label": None,
            "condition": "NM",
            "quantity": 1,
            "price_eur": "0.50",
            "created_at": None,
            "scryfall_uri": None,
            "promo_types": None,
            "frame_effects": None,
            "border_color": None,
        }
        defaults.update(kwargs)
        return defaults

    def _setup_cards_result(self, repo, rows):
        """Hook a list of dict rows into the mappings().fetchall() chain."""
        mock_conn = _setup_conn(repo)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = rows
        return mock_conn

    def test_returns_list_of_cards(self):
        """Returns a list of dicts when matching rows exist."""
        repo = _make_repo()
        self._setup_cards_result(repo, [self._make_db_row()])

        results = repo.get_cards_by_name(user_id=1, card_name="Lightning Bolt")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

    def test_empty_result_returns_empty_list(self):
        """Returns empty list when no cards match the name."""
        repo = _make_repo()
        self._setup_cards_result(repo, [])

        results = repo.get_cards_by_name(user_id=1, card_name="Nonexistent")

        self.assertEqual(results, [])

    def test_user_id_passed_in_query_params(self):
        """user_id is included in the SQL parameters."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = []

        repo.get_cards_by_name(user_id=42, card_name="Counterspell")

        call_params = mock_conn.execute.call_args[0][1]
        self.assertEqual(call_params["user_id"], 42)

    def test_card_name_passed_in_query_params(self):
        """card_name is included in the SQL parameters."""
        repo = _make_repo()
        mock_conn = _setup_conn(repo)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = []

        repo.get_cards_by_name(user_id=1, card_name="Black Lotus")

        call_params = mock_conn.execute.call_args[0][1]
        self.assertEqual(call_params["name"], "Black Lotus")

    def test_multiple_owned_copies_returned(self):
        """Returns one entry per DB row (multiple copies of same name)."""
        repo = _make_repo()
        self._setup_cards_result(
            repo,
            [
                self._make_db_row(id=1, finish="nonfoil"),
                self._make_db_row(id=2, finish="foil"),
            ],
        )

        results = repo.get_cards_by_name(user_id=1, card_name="Lightning Bolt")

        self.assertEqual(len(results), 2)

    def test_result_contains_finish_field(self):
        """Returned dicts include the 'finish' field from _row_to_card mapping."""
        repo = _make_repo()
        self._setup_cards_result(repo, [self._make_db_row(finish="foil")])

        results = repo.get_cards_by_name(user_id=1, card_name="Lightning Bolt")

        self.assertIn("finish", results[0])
        self.assertEqual(results[0]["finish"], "foil")

    def test_result_contains_id_field(self):
        """Returned dicts include the 'id' field."""
        repo = _make_repo()
        self._setup_cards_result(repo, [self._make_db_row(id=77)])

        results = repo.get_cards_by_name(user_id=1, card_name="Lightning Bolt")

        self.assertEqual(results[0]["id"], 77)

    def test_variant_label_included_when_set(self):
        """variant_label is included in returned card dict when present in DB."""
        repo = _make_repo()
        self._setup_cards_result(
            repo, [self._make_db_row(variant_label="Showcase")]
        )

        results = repo.get_cards_by_name(user_id=1, card_name="Lightning Bolt")

        self.assertEqual(results[0].get("variant_label"), "Showcase")


if __name__ == "__main__":
    unittest.main()
