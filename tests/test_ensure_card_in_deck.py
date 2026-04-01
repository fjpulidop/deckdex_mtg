"""Unit tests for DeckRepository.ensure_card_in_deck.

All fixtures use scope="function" to prevent cross-test mock pollution.
No real database is used — SQLAlchemy engine is mocked with MagicMock.

Scenarios covered:
  - Happy path: deck + card exist → True returned, INSERT + commit called
  - Idempotent: ON CONFLICT DO NOTHING means a second call also returns True
  - Deck not found (with user_id filter) → False returned, no INSERT
  - Card not in collection → False returned, no INSERT
  - user_id=None skips deck ownership check entirely
  - Deck params include user_id when provided
  - Card params include user_id when provided
  - Deck params omit user_id when not provided
  - Card params omit user_id when not provided
  - commit is always called on success
  - updated_at is always refreshed on success
"""

from typing import Any, Dict
from unittest.mock import MagicMock, call

from deckdex.storage.deck_repository import DeckRepository


# ---------------------------------------------------------------------------
# Helpers — identical pattern to test_deck_repository.py
# ---------------------------------------------------------------------------


def _make_repo() -> DeckRepository:
    """Instantiate DeckRepository without calling __init__ (avoids URL validation)."""
    repo = DeckRepository.__new__(DeckRepository)
    repo._url = "postgresql://fake"
    return repo


def _make_engine(deck_check_row=None, card_check_row=None):
    """Build a mock SQLAlchemy engine.

    Calls to conn.execute() are answered in order:
      1st call  → deck ownership check (fetchone returns deck_check_row)
      2nd call  → card existence check (fetchone returns card_check_row)
      3rd call  → INSERT deck_cards (no meaningful return)
      4th call  → UPDATE decks.updated_at (no meaningful return)

    When deck_check_row is the sentinel NO_DECK_CHECK, skip the first call
    (simulates user_id=None path where deck check is not executed).
    """
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value = mock_conn
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)

    # Side-effect list drives successive execute() calls
    def _make_result(fetchone_return):
        r = MagicMock()
        r.fetchone.return_value = fetchone_return
        return r

    mock_conn.execute.side_effect = [
        _make_result(deck_check_row),   # deck ownership SELECT
        _make_result(card_check_row),   # card existence SELECT
        MagicMock(),                    # INSERT deck_cards
        MagicMock(),                    # UPDATE decks.updated_at
    ]

    return mock_engine, mock_conn


def _make_engine_no_deck_check(card_check_row=None):
    """Engine for the user_id=None path (no deck ownership check performed)."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value = mock_conn
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)

    def _make_result(fetchone_return):
        r = MagicMock()
        r.fetchone.return_value = fetchone_return
        return r

    mock_conn.execute.side_effect = [
        _make_result(card_check_row),   # card existence SELECT (1st call, deck check skipped)
        MagicMock(),                    # INSERT deck_cards
        MagicMock(),                    # UPDATE decks.updated_at
    ]

    return mock_engine, mock_conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEnsureCardInDeck:
    # -----------------------------------------------------------------------
    # Happy path
    # -----------------------------------------------------------------------

    def test_returns_true_when_deck_and_card_exist(self):
        """Deck belongs to user and card is in collection → True."""
        repo = _make_repo()
        engine, _ = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        result = repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        assert result is True

    def test_commit_called_on_success(self):
        """Transaction is committed when deck + card both exist."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        conn.commit.assert_called_once()

    def test_updated_at_refreshed_on_success(self):
        """UPDATE decks.updated_at is executed on success."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        # At least one execute call should reference "updated_at"
        sql_calls = [str(c.args[0]) for c in conn.execute.call_args_list]
        assert any("updated_at" in sql for sql in sql_calls), (
            "No UPDATE decks.updated_at found in execute calls"
        )

    def test_insert_uses_on_conflict_do_nothing(self):
        """The INSERT statement includes ON CONFLICT DO NOTHING."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        sql_calls = [str(c.args[0]) for c in conn.execute.call_args_list]
        assert any("DO NOTHING" in sql for sql in sql_calls), (
            "INSERT must use ON CONFLICT DO NOTHING"
        )

    def test_idempotent_second_call_also_returns_true(self):
        """Calling twice when the row already exists still returns True."""
        repo = _make_repo()

        # First call — row not yet present (INSERT actually inserts)
        engine1, _ = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine1
        result1 = repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        # Second call — row already present (INSERT is a no-op via DO NOTHING)
        engine2, _ = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine2
        result2 = repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        assert result1 is True
        assert result2 is True

    # -----------------------------------------------------------------------
    # Deck not found
    # -----------------------------------------------------------------------

    def test_returns_false_when_deck_not_found(self):
        """Deck does not belong to user → False, no INSERT."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=None, card_check_row=MagicMock())
        repo._eng = engine

        result = repo.ensure_card_in_deck(deck_id=999, card_id=42, user_id=1)

        assert result is False

    def test_no_insert_when_deck_not_found(self):
        """When deck ownership check fails, no INSERT into deck_cards is attempted."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=None, card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=999, card_id=42, user_id=1)

        # Only one execute call: the deck check SELECT — no INSERT follows
        sql_calls = [str(c.args[0]) for c in conn.execute.call_args_list]
        assert not any("INSERT" in sql for sql in sql_calls), (
            "INSERT must not be executed when deck ownership check fails"
        )

    def test_no_commit_when_deck_not_found(self):
        """No commit when deck ownership check fails."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=None, card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=999, card_id=42, user_id=1)

        conn.commit.assert_not_called()

    # -----------------------------------------------------------------------
    # Card not in collection
    # -----------------------------------------------------------------------

    def test_returns_false_when_card_not_in_collection(self):
        """Card does not exist in user's collection → False."""
        repo = _make_repo()
        engine, _ = _make_engine(deck_check_row=MagicMock(), card_check_row=None)
        repo._eng = engine

        result = repo.ensure_card_in_deck(deck_id=7, card_id=999, user_id=1)

        assert result is False

    def test_no_insert_when_card_not_in_collection(self):
        """No INSERT into deck_cards when card is not in collection."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=None)
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=999, user_id=1)

        sql_calls = [str(c.args[0]) for c in conn.execute.call_args_list]
        assert not any("INSERT" in sql for sql in sql_calls), (
            "INSERT must not be executed when card is not in collection"
        )

    def test_no_commit_when_card_not_in_collection(self):
        """No commit when card is absent from collection."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=None)
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=999, user_id=1)

        conn.commit.assert_not_called()

    # -----------------------------------------------------------------------
    # user_id=None: deck ownership check is skipped
    # -----------------------------------------------------------------------

    def test_user_id_none_skips_deck_ownership_check(self):
        """When user_id is None the deck ownership SELECT is not executed."""
        repo = _make_repo()
        engine, conn = _make_engine_no_deck_check(card_check_row=MagicMock())
        repo._eng = engine

        result = repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=None)

        assert result is True
        # No deck-ownership SELECT should contain user_id param
        for c in conn.execute.call_args_list:
            params = c.args[1] if len(c.args) > 1 else {}
            # The deck SELECT should not appear at all (only 3 calls: card check, insert, update)
            sql = str(c.args[0])
            if "decks" in sql and "WHERE" in sql and "user_id" in sql:
                raise AssertionError(
                    "Deck ownership check with user_id should be skipped when user_id=None"
                )

    def test_user_id_none_card_params_omit_user_id(self):
        """When user_id is None the card existence check omits user_id from params."""
        repo = _make_repo()
        engine, conn = _make_engine_no_deck_check(card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=None)

        # Inspect the first execute call (card check when no deck ownership check)
        first_call_params = conn.execute.call_args_list[0].args[1]
        assert "user_id" not in first_call_params

    def test_user_id_none_still_inserts_and_returns_true(self):
        """Even without user_id the method returns True and inserts the row."""
        repo = _make_repo()
        engine, conn = _make_engine_no_deck_check(card_check_row=MagicMock())
        repo._eng = engine

        result = repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=None)

        assert result is True
        sql_calls = [str(c.args[0]) for c in conn.execute.call_args_list]
        assert any("INSERT" in sql for sql in sql_calls)
        conn.commit.assert_called_once()

    # -----------------------------------------------------------------------
    # user_id provided: params include user_id in both checks
    # -----------------------------------------------------------------------

    def test_deck_check_params_include_user_id_when_provided(self):
        """Deck ownership SELECT receives user_id in params when user_id is given."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=99)

        first_call_params = conn.execute.call_args_list[0].args[1]
        assert first_call_params.get("user_id") == 99

    def test_deck_check_params_include_correct_deck_id(self):
        """Deck ownership SELECT receives the correct deck_id."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=55, card_id=42, user_id=1)

        first_call_params = conn.execute.call_args_list[0].args[1]
        assert first_call_params.get("deck_id") == 55

    def test_card_check_params_include_user_id_when_provided(self):
        """Card existence SELECT receives user_id in params when user_id is given."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=99)

        second_call_params = conn.execute.call_args_list[1].args[1]
        assert second_call_params.get("user_id") == 99

    def test_card_check_params_include_correct_card_id(self):
        """Card existence SELECT receives the correct card_id."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=77, user_id=1)

        second_call_params = conn.execute.call_args_list[1].args[1]
        assert second_call_params.get("card_id") == 77

    # -----------------------------------------------------------------------
    # INSERT payload correctness
    # -----------------------------------------------------------------------

    def test_insert_passes_correct_deck_id_and_card_id(self):
        """INSERT into deck_cards uses the correct deck_id and card_id."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        insert_call = conn.execute.call_args_list[2]  # 3rd call
        insert_params = insert_call.args[1]
        assert insert_params.get("deck_id") == 7
        assert insert_params.get("card_id") == 42

    def test_insert_sets_quantity_one(self):
        """INSERT hard-codes quantity=1 (not a bound param — literal in SQL text)."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        # quantity is a literal in the SQL text, not a bound parameter
        insert_call = conn.execute.call_args_list[2]
        insert_sql = str(insert_call.args[0])
        assert "1," in insert_sql or "VALUES (:deck_id, :card_id, 1," in insert_sql, (
            "INSERT SQL must specify quantity=1 as a literal value"
        )

    def test_insert_sets_is_commander_false(self):
        """Allocation hard-codes is_commander=false (literal in SQL text, not a bound param)."""
        repo = _make_repo()
        engine, conn = _make_engine(deck_check_row=MagicMock(), card_check_row=MagicMock())
        repo._eng = engine

        repo.ensure_card_in_deck(deck_id=7, card_id=42, user_id=1)

        insert_call = conn.execute.call_args_list[2]
        insert_sql = str(insert_call.args[0])
        assert "false" in insert_sql.lower(), (
            "INSERT SQL must specify is_commander=false as a literal value"
        )

    # -----------------------------------------------------------------------
    # Constructor validation
    # -----------------------------------------------------------------------

    def test_constructor_rejects_empty_database_url(self):
        """DeckRepository raises ValueError for empty/non-postgres URL."""
        import pytest

        with pytest.raises(ValueError):
            DeckRepository(database_url="sqlite:///dev.db")

    def test_constructor_rejects_blank_database_url(self):
        """DeckRepository raises ValueError for blank string."""
        import pytest

        with pytest.raises(ValueError):
            DeckRepository(database_url="   ")

    def test_constructor_accepts_postgresql_url(self):
        """DeckRepository accepts postgresql:// URL (with injected engine to avoid real conn)."""
        engine = MagicMock()
        repo = DeckRepository(database_url="postgresql://user:pass@localhost/db", engine=engine)
        assert repo._eng is engine
