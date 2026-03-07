"""Unit tests for PriceHistory repository methods on PostgresCollectionRepository.

Uses a mock SQLAlchemy engine so no real database is needed.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from deckdex.storage.repository import CollectionRepository, PostgresCollectionRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_postgres_repo() -> PostgresCollectionRepository:
    """Return a PostgresCollectionRepository with a fake URL (engine injected later)."""
    repo = PostgresCollectionRepository.__new__(PostgresCollectionRepository)
    repo._url = "postgresql://fake"
    repo._eng = None
    return repo


def _make_mock_engine():
    """Return a mock SQLAlchemy engine with a context-manager-compatible connection."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine.connect.return_value = mock_conn
    return mock_engine, mock_conn


# ---------------------------------------------------------------------------
# Base class no-op defaults
# ---------------------------------------------------------------------------


class TestBaseClassDefaults:
    def test_record_price_history_is_no_op(self):
        """Base CollectionRepository.record_price_history returns None without error."""

        class MinimalRepo(CollectionRepository):
            def get_all_cards(self, user_id=None):
                return []

            def get_cards_for_price_update(self, user_id=None):
                return []

            def get_card_by_id(self, id, user_id=None):
                return None

            def create(self, card, user_id=None):
                return card

            def update(self, id, fields, user_id=None):
                return None

            def delete(self, id, user_id=None):
                return False

            def replace_all(self, cards, user_id=None):
                return 0

        repo = MinimalRepo()
        result = repo.record_price_history(card_id=1, price=3.50)
        assert result is None

    def test_get_price_history_returns_empty_list(self):
        """Base CollectionRepository.get_price_history returns [] by default."""

        class MinimalRepo(CollectionRepository):
            def get_all_cards(self, user_id=None):
                return []

            def get_cards_for_price_update(self, user_id=None):
                return []

            def get_card_by_id(self, id, user_id=None):
                return None

            def create(self, card, user_id=None):
                return card

            def update(self, id, fields, user_id=None):
                return None

            def delete(self, id, user_id=None):
                return False

            def replace_all(self, cards, user_id=None):
                return 0

        repo = MinimalRepo()
        result = repo.get_price_history(card_id=1)
        assert result == []


# ---------------------------------------------------------------------------
# PostgresCollectionRepository — record_price_history
# ---------------------------------------------------------------------------


class TestRecordPriceHistory:
    def test_record_price_history_inserts_row(self):
        """record_price_history executes an INSERT with correct parameters."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine

        repo.record_price_history(card_id=1, price=3.50)

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["card_id"] == 1
        assert params["price"] == 3.50
        assert params["source"] == "scryfall"
        assert params["currency"] == "eur"
        mock_conn.commit.assert_called_once()

    def test_record_price_history_custom_source_and_currency(self):
        """record_price_history respects custom source and currency arguments."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine

        repo.record_price_history(card_id=42, price=9.99, source="tcgplayer", currency="usd")

        params = mock_conn.execute.call_args[0][1]
        assert params["source"] == "tcgplayer"
        assert params["currency"] == "usd"

    def test_record_price_history_commits_after_insert(self):
        """record_price_history always commits the transaction."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine

        repo.record_price_history(card_id=5, price=1.00)

        mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# PostgresCollectionRepository — get_price_history
# ---------------------------------------------------------------------------


def _make_row(recorded_at, price, source="scryfall", currency="eur"):
    """Build a mock row tuple for get_price_history fetchall results."""
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, i, _vals=(recorded_at, price, source, currency): _vals[i]
    # Indexing: row[0]=recorded_at, row[1]=price, row[2]=source, row[3]=currency
    mock_row.__iter__ = lambda self: iter((recorded_at, price, source, currency))
    # Support index access
    return (recorded_at, price, source, currency)


class TestGetPriceHistory:
    def test_get_price_history_empty_returns_empty_list(self):
        """get_price_history returns [] when no rows exist."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine
        mock_conn.execute.return_value.fetchall.return_value = []

        result = repo.get_price_history(card_id=1)

        assert result == []

    def test_get_price_history_returns_dicts_with_correct_keys(self):
        """get_price_history returns list of dicts with required keys."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine

        dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_conn.execute.return_value.fetchall.return_value = [
            (dt, Decimal("3.50"), "scryfall", "eur"),
        ]

        result = repo.get_price_history(card_id=1)

        assert len(result) == 1
        point = result[0]
        assert "recorded_at" in point
        assert "price" in point
        assert "source" in point
        assert "currency" in point
        assert point["price"] == 3.50
        assert point["source"] == "scryfall"
        assert point["currency"] == "eur"

    def test_get_price_history_returns_oldest_first(self):
        """get_price_history returns rows ordered ascending by recorded_at."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine

        dt_old = datetime(2026, 1, 1, tzinfo=timezone.utc)
        dt_new = datetime(2026, 1, 10, tzinfo=timezone.utc)
        # Simulate DB returning them oldest-first (ORDER BY recorded_at ASC)
        mock_conn.execute.return_value.fetchall.return_value = [
            (dt_old, Decimal("2.00"), "scryfall", "eur"),
            (dt_new, Decimal("4.00"), "scryfall", "eur"),
        ]

        result = repo.get_price_history(card_id=1)

        assert len(result) == 2
        assert result[0]["price"] == 2.00
        assert result[1]["price"] == 4.00

    def test_get_price_history_passes_card_id_to_query(self):
        """get_price_history binds the correct card_id parameter."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine
        mock_conn.execute.return_value.fetchall.return_value = []

        repo.get_price_history(card_id=99, days=30)

        params = mock_conn.execute.call_args[0][1]
        assert params["card_id"] == 99

    def test_get_price_history_uses_days_in_query(self):
        """get_price_history uses the days value in the SQL interval (via f-string)."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine
        mock_conn.execute.return_value.fetchall.return_value = []

        repo.get_price_history(card_id=1, days=7)

        # The SQL text should contain the days value interpolated
        sql_text = str(mock_conn.execute.call_args[0][0])
        assert "7" in sql_text

    def test_get_price_history_recorded_at_is_iso_string(self):
        """get_price_history converts datetime to ISO 8601 string."""
        repo = _make_postgres_repo()
        mock_engine, mock_conn = _make_mock_engine()
        repo._eng = mock_engine

        dt = datetime(2026, 3, 1, 10, 30, 0, tzinfo=timezone.utc)
        mock_conn.execute.return_value.fetchall.return_value = [
            (dt, Decimal("5.00"), "scryfall", "eur"),
        ]

        result = repo.get_price_history(card_id=1)

        assert isinstance(result[0]["recorded_at"], str)
        assert "2026-03-01" in result[0]["recorded_at"]
