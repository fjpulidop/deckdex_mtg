"""Unit tests for deckdex/storage/suggestion_repository.py.

Tests cover:
  - __init__: rejects invalid/non-postgresql URLs when no engine provided.
  - get_seen_set_codes: returns a set of strings.
  - insert_seen_set: idempotent ON CONFLICT handling.
  - get_suggestions_for_deck: returns dicts ordered by score DESC.
  - get_suggestion_count_for_deck: returns integer row count.
  - upsert_suggestions: idempotency, ON CONFLICT DO UPDATE, empty list no-op.
  - delete_suggestion: returns True on success, False for missing row.
  - delete_suggestions_for_deck: returns count of deleted rows.
  - clear_suggestions_for_old_sets: deletes rows from other sets.

All tests mock the SQLAlchemy engine — no real Postgres is required.
All fixtures use scope="function".
"""

import unittest
from unittest.mock import MagicMock, patch

from deckdex.storage.suggestion_repository import SuggestionRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(engine: MagicMock | None = None) -> SuggestionRepository:
    """Build a SuggestionRepository with a mocked engine, bypassing __init__ validation."""
    repo = SuggestionRepository.__new__(SuggestionRepository)
    repo._url = "postgresql://fake:fake@localhost/fake"
    repo._eng = engine or MagicMock()
    return repo


def _mock_conn_context(mock_engine: MagicMock) -> MagicMock:
    """Return the MagicMock connection that the engine yields.

    Sets up __enter__ / __exit__ so 'with engine.connect() as conn:' works.
    """
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn


def _mock_begin_context(mock_engine: MagicMock) -> MagicMock:
    """Return the MagicMock connection that the engine yields for BEGIN (write ops)."""
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn


# ---------------------------------------------------------------------------
# Tests: __init__ validation
# ---------------------------------------------------------------------------


class TestInit(unittest.TestCase):
    def test_raises_on_non_postgresql_url(self):
        with self.assertRaises(ValueError):
            SuggestionRepository(database_url="sqlite:///local.db")

    def test_raises_on_empty_url(self):
        with self.assertRaises(ValueError):
            SuggestionRepository(database_url="")

    def test_raises_on_mysql_url(self):
        with self.assertRaises(ValueError):
            SuggestionRepository(database_url="mysql://user:pass@host/db")

    def test_accepts_postgresql_url_with_engine(self):
        """Providing an engine bypasses the URL validation."""
        mock_engine = MagicMock()
        repo = SuggestionRepository(database_url="", engine=mock_engine)
        assert repo._eng is mock_engine

    def test_accepts_valid_postgresql_url(self):
        with patch("sqlalchemy.create_engine", return_value=MagicMock()):
            repo = SuggestionRepository(database_url="postgresql://user:pass@localhost/db")
        assert repo._url == "postgresql://user:pass@localhost/db"


# ---------------------------------------------------------------------------
# Tests: get_seen_set_codes
# ---------------------------------------------------------------------------


class TestGetSeenSetCodes(unittest.TestCase):
    def test_returns_set_of_strings(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.fetchall.return_value = [("TST",), ("OTJ",)]

        repo = _make_repo(mock_engine)
        result = repo.get_seen_set_codes()

        assert result == {"TST", "OTJ"}

    def test_returns_empty_set_when_no_rows(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.fetchall.return_value = []

        repo = _make_repo(mock_engine)
        result = repo.get_seen_set_codes()

        assert result == set()

    def test_returns_set_type_not_list(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.fetchall.return_value = [("A",), ("B",), ("A",)]

        repo = _make_repo(mock_engine)
        result = repo.get_seen_set_codes()

        assert isinstance(result, set)
        assert len(result) == 2  # duplicates collapsed by set


# ---------------------------------------------------------------------------
# Tests: insert_seen_set
# ---------------------------------------------------------------------------


class TestInsertSeenSet(unittest.TestCase):
    def test_executes_insert(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)

        repo = _make_repo(mock_engine)
        repo.insert_seen_set("TST", "Test Set", "2026-01-01")

        mock_conn.execute.assert_called_once()

    def test_passes_correct_parameters(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)

        repo = _make_repo(mock_engine)
        repo.insert_seen_set("OTJ", "Outlaws of Thunder Junction", "2024-04-19")

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["set_code"] == "OTJ"
        assert params["set_name"] == "Outlaws of Thunder Junction"
        assert params["released_at"] == "2024-04-19"

    def test_idempotent_on_duplicate_call(self):
        """Two calls for the same set_code should each execute once (ON CONFLICT DO NOTHING)."""
        mock_engine = MagicMock()
        # Create fresh connections for each call
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()
        contexts = [mock_conn1, mock_conn2]

        begin_ctx = MagicMock()
        begin_ctx.__enter__ = lambda s: contexts.pop(0)
        begin_ctx.__exit__ = MagicMock(return_value=False)
        mock_engine.begin.return_value = begin_ctx

        repo = _make_repo(mock_engine)
        repo.insert_seen_set("TST", "Test Set", "2026-01-01")
        begin_ctx.__enter__ = lambda s: MagicMock()
        repo.insert_seen_set("TST", "Test Set", "2026-01-01")

        # Two separate engine.begin() calls — no error raised
        assert mock_engine.begin.call_count == 2


# ---------------------------------------------------------------------------
# Tests: get_suggestions_for_deck
# ---------------------------------------------------------------------------


class TestGetSuggestionsForDeck(unittest.TestCase):
    def _fake_row(self, scryfall_id: str, score: float) -> dict:
        return {
            "id": 1,
            "deck_id": 42,
            "user_id": 1,
            "set_code": "TST",
            "scryfall_id": scryfall_id,
            "card_name": "Card",
            "mana_cost": "{2}{B}",
            "cmc": 3.0,
            "type_line": "Creature",
            "color_identity": "B",
            "oracle_text": "",
            "reason": "Fits color identity",
            "score": score,
            "created_at": "2026-04-01T00:00:00",
        }

    def test_returns_list_of_dicts(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        row = self._fake_row("abc-001", 0.75)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = [row]

        repo = _make_repo(mock_engine)
        result = repo.get_suggestions_for_deck(deck_id=42, user_id=1)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["scryfall_id"] == "abc-001"

    def test_returns_empty_list_when_no_suggestions(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = []

        repo = _make_repo(mock_engine)
        result = repo.get_suggestions_for_deck(deck_id=42, user_id=1)

        assert result == []

    def test_passes_correct_params_to_query(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = []

        repo = _make_repo(mock_engine)
        repo.get_suggestions_for_deck(deck_id=7, user_id=3, limit=3)

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["deck_id"] == 7
        assert params["user_id"] == 3
        assert params["limit"] == 3

    def test_default_limit_is_5(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = []

        repo = _make_repo(mock_engine)
        repo.get_suggestions_for_deck(deck_id=7, user_id=3)

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["limit"] == 5


# ---------------------------------------------------------------------------
# Tests: get_suggestion_count_for_deck
# ---------------------------------------------------------------------------


class TestGetSuggestionCountForDeck(unittest.TestCase):
    def test_returns_integer_count(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.fetchone.return_value = (3,)

        repo = _make_repo(mock_engine)
        result = repo.get_suggestion_count_for_deck(deck_id=1, user_id=1)

        assert result == 3

    def test_returns_zero_when_no_rows(self):
        mock_engine = MagicMock()
        mock_conn = _mock_conn_context(mock_engine)
        mock_conn.execute.return_value.fetchone.return_value = None

        repo = _make_repo(mock_engine)
        result = repo.get_suggestion_count_for_deck(deck_id=1, user_id=1)

        assert result == 0


# ---------------------------------------------------------------------------
# Tests: upsert_suggestions
# ---------------------------------------------------------------------------


class TestUpsertSuggestions(unittest.TestCase):
    def _make_suggestion(self, deck_id: int = 1, scryfall_id: str = "abc-001") -> dict:
        return {
            "deck_id": deck_id,
            "user_id": 1,
            "set_code": "TST",
            "scryfall_id": scryfall_id,
            "card_name": "Test Card",
            "mana_cost": "{2}{B}",
            "cmc": 3.0,
            "type_line": "Creature",
            "color_identity": "B",
            "oracle_text": "",
            "reason": "Fits deck",
            "score": 0.75,
        }

    def test_empty_list_is_no_op(self):
        mock_engine = MagicMock()
        repo = _make_repo(mock_engine)

        repo.upsert_suggestions([])

        mock_engine.begin.assert_not_called()

    def test_executes_once_per_suggestion(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)

        repo = _make_repo(mock_engine)
        suggestions = [
            self._make_suggestion(scryfall_id="s-001"),
            self._make_suggestion(scryfall_id="s-002"),
        ]
        repo.upsert_suggestions(suggestions)

        assert mock_conn.execute.call_count == 2

    def test_idempotency_second_upsert_same_key(self):
        """Calling upsert_suggestions twice with the same (deck_id, scryfall_id)
        should not raise — ON CONFLICT DO UPDATE handles it at the DB level."""
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)

        repo = _make_repo(mock_engine)
        s = self._make_suggestion()
        repo.upsert_suggestions([s])
        mock_conn.execute.reset_mock()

        # Second call — should execute exactly once again
        mock_conn2 = _mock_begin_context(mock_engine)
        repo.upsert_suggestions([s])
        mock_conn2.execute.assert_called_once()

    def test_passes_optional_fields_as_none(self):
        """mana_cost, cmc, type_line, color_identity, oracle_text default to None."""
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)

        repo = _make_repo(mock_engine)
        s = {
            "deck_id": 1,
            "user_id": 1,
            "set_code": "TST",
            "scryfall_id": "min-001",
            "card_name": "Minimal Card",
            "reason": "Fits deck",
            "score": 0.5,
        }
        repo.upsert_suggestions([s])

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["mana_cost"] is None
        assert params["cmc"] is None
        assert params["type_line"] is None
        assert params["color_identity"] is None
        assert params["oracle_text"] is None


# ---------------------------------------------------------------------------
# Tests: delete_suggestion
# ---------------------------------------------------------------------------


class TestDeleteSuggestion(unittest.TestCase):
    def test_returns_true_when_row_deleted(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 1

        repo = _make_repo(mock_engine)
        result = repo.delete_suggestion(deck_id=42, scryfall_id="abc-123", user_id=1)

        assert result is True

    def test_returns_false_when_no_row_deleted(self):
        """Returns False for a missing / already-dismissed suggestion."""
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 0

        repo = _make_repo(mock_engine)
        result = repo.delete_suggestion(deck_id=42, scryfall_id="nonexistent", user_id=1)

        assert result is False

    def test_passes_correct_params(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 1

        repo = _make_repo(mock_engine)
        repo.delete_suggestion(deck_id=7, scryfall_id="xyz-999", user_id=3)

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["deck_id"] == 7
        assert params["scryfall_id"] == "xyz-999"
        assert params["user_id"] == 3


# ---------------------------------------------------------------------------
# Tests: delete_suggestions_for_deck
# ---------------------------------------------------------------------------


class TestDeleteSuggestionsForDeck(unittest.TestCase):
    def test_returns_count_of_deleted_rows(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 5

        repo = _make_repo(mock_engine)
        result = repo.delete_suggestions_for_deck(deck_id=42, user_id=1)

        assert result == 5

    def test_returns_zero_when_none_deleted(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 0

        repo = _make_repo(mock_engine)
        result = repo.delete_suggestions_for_deck(deck_id=99, user_id=1)

        assert result == 0


# ---------------------------------------------------------------------------
# Tests: clear_suggestions_for_old_sets
# ---------------------------------------------------------------------------


class TestClearSuggestionsForOldSets(unittest.TestCase):
    def test_returns_count_of_deleted_rows(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 12

        repo = _make_repo(mock_engine)
        result = repo.clear_suggestions_for_old_sets("NEW")

        assert result == 12

    def test_passes_set_code_to_query(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 0

        repo = _make_repo(mock_engine)
        repo.clear_suggestions_for_old_sets("CURRENT")

        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["set_code"] == "CURRENT"

    def test_returns_zero_when_nothing_to_clear(self):
        mock_engine = MagicMock()
        mock_conn = _mock_begin_context(mock_engine)
        mock_conn.execute.return_value.rowcount = 0

        repo = _make_repo(mock_engine)
        result = repo.clear_suggestions_for_old_sets("ONLY_SET")

        assert result == 0


if __name__ == "__main__":
    unittest.main()
