"""Unit tests for DeckRepository.find_card_ids_by_names.

Uses an in-memory SQLite database (via SQLAlchemy) so no real Postgres is needed.
SQLite supports LOWER() but does not support the PostgreSQL ANY() syntax, so we
exercise the method through a thin adapter that swaps the query for SQLite
compatibility. For the purposes of this test suite we mock the engine directly
to verify query dispatch and return-value shaping.
"""

from typing import Any, Dict
from unittest.mock import MagicMock

from deckdex.storage.deck_repository import DeckRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo() -> DeckRepository:
    """Return a DeckRepository instance with a fake URL (engine injected later)."""
    return DeckRepository.__new__(DeckRepository)


def _mock_engine_with_rows(rows: list[Dict[str, Any]]):
    """Build a mock SQLAlchemy engine that returns *rows* for any SELECT."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_result = MagicMock()

    # Simulate .mappings().fetchall() returning list of dict-like objects
    mock_rows = []
    for r in rows:
        m = MagicMock()
        m.__getitem__ = lambda self, key, _r=r: _r[key]
        mock_rows.append(m)

    mock_result.mappings.return_value.fetchall.return_value = mock_rows
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine.connect.return_value = mock_conn

    return mock_engine


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFindCardIdsByNames:
    def test_empty_names_returns_empty_dict(self):
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        repo._eng = MagicMock()  # should never be called

        result = repo.find_card_ids_by_names([], user_id=1)
        assert result == {}
        # Engine should not be touched at all
        repo._eng.connect.assert_not_called()

    def test_returns_lowercase_name_to_id_mapping(self):
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        rows = [
            {"id": 42, "name": "Lightning Bolt"},
            {"id": 7, "name": "Counterspell"},
        ]
        repo._eng = _mock_engine_with_rows(rows)

        result = repo.find_card_ids_by_names(["lightning bolt", "counterspell"], user_id=1)
        assert result == {"lightning bolt": 42, "counterspell": 7}

    def test_case_insensitive_match_key_is_lowercase(self):
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        # The DB stores name with mixed case; our mapper lowercases it
        rows = [{"id": 99, "name": "Sol Ring"}]
        repo._eng = _mock_engine_with_rows(rows)

        result = repo.find_card_ids_by_names(["sol ring"], user_id=None)
        assert "sol ring" in result
        assert result["sol ring"] == 99

    def test_duplicate_names_first_id_wins(self):
        """When two rows share the same lowercase name, the lowest id (first by ORDER BY id ASC) wins."""
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        # Rows returned pre-sorted by id ASC (as the query does)
        rows = [
            {"id": 1, "name": "Lightning Bolt"},
            {"id": 5, "name": "Lightning Bolt"},
        ]
        repo._eng = _mock_engine_with_rows(rows)

        result = repo.find_card_ids_by_names(["lightning bolt"], user_id=1)
        assert result["lightning bolt"] == 1  # lowest id wins

    def test_multi_name_batching_single_query(self):
        """All names are resolved in a single engine.connect() call."""
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        rows = [
            {"id": 1, "name": "Lightning Bolt"},
            {"id": 2, "name": "Counterspell"},
            {"id": 3, "name": "Sol Ring"},
        ]
        repo._eng = _mock_engine_with_rows(rows)

        result = repo.find_card_ids_by_names(
            ["lightning bolt", "counterspell", "sol ring"],
            user_id=1,
        )

        # Only one connect() call (batched)
        assert repo._eng.connect.call_count == 1
        assert len(result) == 3

    def test_no_match_returns_empty_dict(self):
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        # DB returns nothing
        repo._eng = _mock_engine_with_rows([])

        result = repo.find_card_ids_by_names(["nonexistent card"], user_id=1)
        assert result == {}

    def test_user_id_none_omits_user_filter(self):
        """When user_id is None the query must NOT include user_id in params."""
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn
        repo._eng = mock_engine

        repo.find_card_ids_by_names(["lightning bolt"], user_id=None)

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]  # second positional arg is the params dict
        assert "user_id" not in params

    def test_user_id_provided_includes_user_filter(self):
        """When user_id is given the params dict must include it."""
        repo = DeckRepository.__new__(DeckRepository)
        repo._url = "postgresql://fake"
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn
        repo._eng = mock_engine

        repo.find_card_ids_by_names(["lightning bolt"], user_id=42)

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params.get("user_id") == 42
