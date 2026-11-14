"""
Tests for the fast, skip-if-fresh bulk price refresh: migration, config, grouped Scryfall
lookups, stale selection, bulk writes, summary counters, service and route wiring.
"""

import contextlib
import io
import os
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app
from deckdex.storage.repository import CollectionRepository, PriceUpdate

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _make_processor(api_delay=0):
    from deckdex.config import ProcessingConfig, ProcessorConfig
    from deckdex.magic_card_processor import MagicCardProcessor

    proc = MagicCardProcessor.__new__(MagicCardProcessor)
    proc.config = ProcessorConfig(processing=ProcessingConfig(max_workers=1, api_delay=api_delay))
    proc.update_prices = True
    proc.dry_run = False
    proc._card_cache = {}
    proc.error_count = 0
    proc.last_error_count = 0
    proc.not_found_cards = []
    proc.collection_repository = MagicMock()
    proc.spreadsheet_client = None
    proc.card_fetcher = MagicMock()
    return proc


def _scryfall_card(name, eur="1.00"):
    return {"name": name, "prices": {"eur": eur}}


def _collection_fetcher(prices=None, missing=()):
    """Fake get_cards_collection: resolves every requested name except `missing`."""

    def get_cards_collection(names):
        found = [_scryfall_card(n, (prices or {}).get(n, "1.00")) for n in names if n not in missing]
        return found, [n for n in names if n in missing]

    return MagicMock(side_effect=get_cards_collection)


class TestMigration(unittest.TestCase):
    def setUp(self):
        self.sql = (ROOT / "migrations" / "016_card_price_last_checked_at.sql").read_text()

    def test_adds_nullable_column_idempotently(self):
        self.assertIn("ADD COLUMN IF NOT EXISTS price_last_checked_at TIMESTAMPTZ;", self.sql)
        self.assertNotIn("NOT NULL", self.sql)

    def test_does_not_touch_price_history(self):
        self.assertNotIn("price_history", self.sql.replace("--", "").split("ALTER", 1)[1])


class TestFreshnessConfig(unittest.TestCase):
    def test_default_is_six_hours(self):
        from deckdex.config import ProcessingConfig

        self.assertEqual(ProcessingConfig().price_freshness_window_seconds, 21600)

    def test_zero_is_accepted(self):
        from deckdex.config import ProcessingConfig

        self.assertEqual(ProcessingConfig(price_freshness_window_seconds=0).price_freshness_window_seconds, 0)

    def test_negative_raises(self):
        from deckdex.config import ProcessingConfig

        with self.assertRaises(ValueError):
            ProcessingConfig(price_freshness_window_seconds=-1)

    def test_load_config_carries_yaml_value(self):
        from deckdex.config_loader import load_config

        config = load_config(profile="default")
        self.assertEqual(config.processing.price_freshness_window_seconds, 21600)


class TestRepositoryBulkMethods(unittest.TestCase):
    def _postgres_repo(self):
        from deckdex.storage.repository import PostgresCollectionRepository

        repo = PostgresCollectionRepository.__new__(PostgresCollectionRepository)
        conn = MagicMock()
        engine = MagicMock()
        engine.connect.return_value.__enter__.return_value = conn
        repo._get_engine = MagicMock(return_value=engine)
        return repo, conn

    def test_base_class_defaults(self):
        repo = MagicMock(spec=CollectionRepository)
        self.assertEqual(CollectionRepository.bulk_update_prices(repo, [PriceUpdate(1, "1,00", NOW, True)]), 0)
        self.assertEqual(CollectionRepository.get_price_last_checked(repo, [1]), {})

    def test_empty_bulk_update_issues_no_sql(self):
        repo, conn = self._postgres_repo()
        self.assertEqual(repo.bulk_update_prices([]), 0)
        conn.execute.assert_not_called()

    def test_bulk_update_is_one_statement_and_returns_rowcount(self):
        repo, conn = self._postgres_repo()
        conn.execute.return_value.rowcount = 2
        updates = [PriceUpdate(1, "1,00", NOW, True), PriceUpdate(2, "2,00", NOW, False)]
        self.assertEqual(repo.bulk_update_prices(updates), 2)
        self.assertEqual(conn.execute.call_count, 1)
        params = conn.execute.call_args[0][1]
        self.assertEqual((params["id0"], params["changed0"], params["changed1"]), (1, True, False))

    def test_empty_get_price_last_checked_issues_no_sql(self):
        repo, conn = self._postgres_repo()
        self.assertEqual(repo.get_price_last_checked([]), {})
        conn.execute.assert_not_called()

    def test_get_price_last_checked_maps_ids(self):
        repo, conn = self._postgres_repo()
        conn.execute.return_value.fetchall.return_value = [(1, NOW), (2, None)]
        self.assertEqual(repo.get_price_last_checked([1, 2]), {1: NOW, 2: None})


class TestCollectionLookup(unittest.TestCase):
    def _fetcher(self):
        from deckdex.card_fetcher import CardFetcher
        from deckdex.config import OpenAIConfig, ScryfallConfig

        with patch.dict(os.environ, {}, clear=False):
            return CardFetcher(ScryfallConfig(max_retries=2, retry_delay=0), OpenAIConfig())

    @staticmethod
    def _response(payload):
        response = MagicMock()
        response.json.return_value = payload
        return response

    def test_posts_identifiers_and_parses_response(self):
        fetcher = self._fetcher()
        payload = {"data": [{"name": "A"}], "not_found": [{"name": "B"}]}
        with patch("requests.post", return_value=self._response(payload)) as post:
            found, not_found = fetcher.get_cards_collection(["A", "B"])
        self.assertEqual((found, not_found), ([{"name": "A"}], ["B"]))
        self.assertTrue(post.call_args[0][0].endswith("/cards/collection"))
        self.assertEqual(post.call_args[1]["json"], {"identifiers": [{"name": "A"}, {"name": "B"}]})

    # [spec:scryfall-request-diagnostics/non-429-client-errors-are-not-retried]
    def test_retries_on_request_exception(self):
        import requests

        fetcher = self._fetcher()
        ok = self._response({"data": [], "not_found": []})
        with patch("requests.post", side_effect=[requests.exceptions.RequestException("x"), ok]) as post:
            fetcher.get_cards_collection(["A"])
        self.assertEqual(post.call_count, 2)

    # [spec:scryfall-request-diagnostics/scryfall-requests-identify-the-client]
    def test_sends_custom_user_agent_and_accept(self):
        fetcher = self._fetcher()
        with patch("requests.post", return_value=self._response({"data": [], "not_found": []})) as post:
            fetcher.get_cards_collection(["A"])
        headers = post.call_args[1]["headers"]
        self.assertEqual(headers["User-Agent"], "DeckDex/1.0 (MTG collection manager)")
        self.assertEqual(headers["Accept"], "application/json")

    # [spec:scryfall-request-diagnostics/scryfall-error-detail-is-surfaced]
    # [spec:scryfall-request-diagnostics/non-429-client-errors-are-not-retried]
    def test_4xx_is_not_retried_and_reports_scryfall_detail(self):
        import requests

        fetcher = self._fetcher()
        bad = MagicMock(status_code=400)
        bad.json.return_value = {"rule": "generic_user_agent", "details": "Use a custom UA"}
        bad.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error", response=bad)
        with patch("requests.post", return_value=bad) as post:
            with self.assertRaises(requests.exceptions.HTTPError) as ctx:
                fetcher.get_cards_collection(["A"])
        self.assertEqual(post.call_count, 1)
        self.assertIn("generic_user_agent", str(ctx.exception))
        self.assertIn("400 Client Error", str(ctx.exception))
        self.assertIn("Use a custom UA", str(ctx.exception))

    # [spec:scryfall-request-diagnostics/collection-lookup-omits-blank-identifiers]
    def test_empty_names_are_dropped(self):
        fetcher = self._fetcher()
        with patch("requests.post", return_value=self._response({"data": [], "not_found": []})) as post:
            fetcher.get_cards_collection(["A", "", "  "])
        self.assertEqual(post.call_args[1]["json"], {"identifiers": [{"name": "A"}]})

    # [spec:scryfall-request-diagnostics/collection-lookup-omits-blank-identifiers]
    def test_more_than_75_names_raises(self):
        with self.assertRaises(ValueError):
            self._fetcher().get_cards_collection([f"C{i}" for i in range(76)])

    # [spec:scryfall-request-diagnostics/scryfall-requests-identify-the-client]
    def test_get_sends_client_headers(self):
        fetcher = self._fetcher()
        with patch("requests.get", return_value=self._response({"data": []})) as get:
            fetcher._make_request("https://api.scryfall.com/cards/search")
        self.assertEqual(
            get.call_args.kwargs["headers"],
            {
                "User-Agent": "DeckDex/1.0 (MTG collection manager)",
                "Accept": "application/json",
            },
        )

    # [spec:scryfall-request-diagnostics/scryfall-error-detail-is-surfaced]
    def test_non_json_error_includes_only_first_300_body_characters(self):
        import requests

        fetcher = self._fetcher()
        bad = MagicMock(status_code=400, text="x" * 300 + "TRUNCATED")
        bad.json.side_effect = ValueError("not JSON")
        bad.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error", response=bad)
        with patch("requests.post", return_value=bad):
            with self.assertRaises(requests.exceptions.HTTPError) as ctx:
                fetcher.get_cards_collection(["A"])
        self.assertEqual(str(ctx.exception), "400 Client Error - Scryfall response: " + "x" * 300)

    # [spec:scryfall-request-diagnostics/collection-lookup-omits-blank-identifiers]
    def test_all_blank_names_send_no_request(self):
        fetcher = self._fetcher()
        with patch("requests.post") as post:
            self.assertEqual(fetcher.get_cards_collection(["", "  "]), ([], []))
        post.assert_not_called()


class TestGroupedLookup(unittest.TestCase):
    def test_150_names_make_two_requests_and_two_sleeps(self):
        proc = _make_processor(api_delay=0.1)
        proc.card_fetcher.get_cards_collection = _collection_fetcher()
        names = [f"Card {i}" for i in range(150)]
        with patch("deckdex.magic_card_processor.time.sleep") as sleep:
            results = proc._fetch_card_prices_grouped(names)
        self.assertEqual(proc.card_fetcher.get_cards_collection.call_count, 2)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(proc.requests_made, 2)
        self.assertLess(proc.requests_made, len(names))
        self.assertTrue(all(results[n] is not None for n in names))

    def test_duplicate_names_are_looked_up_once(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher()
        results = proc._fetch_card_prices_grouped(["Bolt", "Bolt", "Bolt"])
        self.assertEqual(proc.card_fetcher.get_cards_collection.call_args[0][0], ["Bolt"])
        self.assertEqual(list(results), ["Bolt"])

    def test_matching_is_case_insensitive_and_uses_front_face(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = MagicMock(
            return_value=([_scryfall_card("Delver of Secrets // Insectile Aberration")], [])
        )
        results = proc._fetch_card_prices_grouped(["delver of secrets"])
        self.assertIsNotNone(results["delver of secrets"])
        self.assertEqual(proc.requests_made, 1)

    # [spec:price-refresh-efficiency/grouped-price-lookup]
    def test_unresolved_name_falls_back_once(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher(missing={"Ghost"})
        with patch.object(proc, "_fetch_card_data", return_value=None) as fetch:
            results = proc._fetch_card_prices_grouped(["Real", "Ghost"])
        fetch.assert_called_once_with("Ghost")
        self.assertIsNone(results["Ghost"])
        self.assertEqual(proc.requests_made, 2)

    # [spec:price-refresh-efficiency/grouped-price-lookup]
    def test_not_found_card_lands_in_error_accounting(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher(missing={"Ghost"})
        proc.card_fetcher.search_card.side_effect = Exception("Card not found: Ghost")
        with contextlib.redirect_stdout(io.StringIO()):
            proc._fetch_card_prices_grouped(["Ghost"])
        self.assertEqual(proc.error_count, 1)
        self.assertEqual(proc.not_found_cards, ["Ghost"])

    # [spec:price-refresh-efficiency/grouped-price-lookup]
    def test_failing_post_falls_back_to_per_name_lookups(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = MagicMock(side_effect=RuntimeError("boom"))
        with patch.object(proc, "_fetch_card_data", return_value=_scryfall_card("x")) as fetch:
            results = proc._fetch_card_prices_grouped(["A", "B"])
        self.assertEqual(fetch.call_count, 2)
        self.assertTrue(all(results.values()))

    # [spec:price-refresh-efficiency/grouped-price-lookup]
    # [spec:scryfall-request-diagnostics/non-429-client-errors-are-not-retried]
    # [spec:scryfall-request-diagnostics/scryfall-error-detail-is-surfaced]
    def test_exhausted_429_falls_back_for_every_name_and_logs_detail(self):
        import requests

        from deckdex.card_fetcher import CardFetcher
        from deckdex.config import OpenAIConfig, ScryfallConfig

        proc = _make_processor()
        proc.card_fetcher = CardFetcher(ScryfallConfig(max_retries=3, retry_delay=1), OpenAIConfig())
        bad = MagicMock(status_code=429)
        bad.json.return_value = {"details": "Too many requests", "rule": "rate_limit"}
        bad.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Client Error", response=bad)
        with (
            patch("requests.post", return_value=bad) as post,
            patch("deckdex.card_fetcher.time.sleep") as sleep,
            patch("deckdex.magic_card_processor.logger.warning") as warning,
            patch.object(proc, "_fetch_card_data", side_effect=lambda name: _scryfall_card(name)) as fetch,
        ):
            results = proc._fetch_card_prices_grouped(["A", "B"])
        self.assertEqual(post.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list[:2]], [1, 2])
        self.assertEqual([c.args[0] for c in fetch.call_args_list], ["A", "B"])
        self.assertEqual(results, {name: _scryfall_card(name) for name in ["A", "B"]})
        message = warning.call_args.args[0]
        self.assertIn("429", message)
        self.assertIn("rate_limit", message)
        self.assertIn("Too many requests", message)


class TestSelectStaleCards(unittest.TestCase):
    CARDS = [(1, "A", ""), (2, "B", ""), (3, "C", "")]

    def select(self, last_checked, window=3600, force=False):
        return _make_processor()._select_stale_cards(self.CARDS, last_checked, window, force, NOW)

    def test_null_and_missing_are_stale(self):
        stale, skipped = self.select({1: None})
        self.assertEqual((len(stale), skipped), (3, 0))

    def test_within_window_is_skipped(self):
        stale, skipped = self.select({1: NOW - timedelta(seconds=10), 2: None, 3: None})
        self.assertEqual([c[0] for c in stale], [2, 3])
        self.assertEqual(skipped, 1)

    def test_exactly_at_window_is_not_stale(self):
        stale, skipped = self.select({1: NOW - timedelta(seconds=3600), 2: NOW, 3: NOW})
        self.assertEqual((stale, skipped), ([], 3))

    def test_beyond_window_is_stale(self):
        stale, _ = self.select({1: NOW - timedelta(seconds=3601), 2: NOW, 3: NOW})
        self.assertEqual([c[0] for c in stale], [1])

    def test_window_zero_treats_all_as_stale(self):
        stale, skipped = self.select({1: NOW, 2: NOW, 3: NOW}, window=0)
        self.assertEqual((len(stale), skipped), (3, 0))

    def test_force_treats_all_as_stale(self):
        stale, skipped = self.select({1: NOW, 2: NOW, 3: NOW}, force=True)
        self.assertEqual((len(stale), skipped), (3, 0))

    def test_naive_datetime_is_treated_as_utc(self):
        stale, skipped = self.select({1: NOW.replace(tzinfo=None), 2: NOW, 3: NOW})
        self.assertEqual((stale, skipped), ([], 3))


@contextlib.contextmanager
def _quiet():
    with patch.dict(os.environ, {"TQDM_DISABLE": "1"}), contextlib.redirect_stdout(io.StringIO()):
        yield


class TestUpdatePricesDataRepo(unittest.TestCase):
    def test_changed_price_gets_update_and_one_history_row(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher({"A": "2.50"})
        with _quiet():
            proc.update_prices_data_repo([(1, "A", "1,00")])
        updates = proc.collection_repository.bulk_update_prices.call_args[0][0]
        self.assertEqual([(u.card_id, u.price, u.price_changed) for u in updates], [(1, "2,50", True)])
        self.assertIsNotNone(updates[0].checked_at.tzinfo)
        proc.collection_repository.record_price_history.assert_called_once_with(1, 2.5)

    def test_unchanged_price_is_stamped_without_history(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher({"A": "1.00"})
        with _quiet():
            proc.update_prices_data_repo([(1, "A", "1,00")])
        updates = proc.collection_repository.bulk_update_prices.call_args[0][0]
        self.assertFalse(updates[0].price_changed)
        proc.collection_repository.record_price_history.assert_not_called()

    def test_non_numeric_price_has_no_history(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = MagicMock(return_value=([_scryfall_card("A", None)], []))
        with _quiet():
            proc.update_prices_data_repo([(1, "A", "1,00")])
        proc.collection_repository.record_price_history.assert_not_called()

    def test_failed_lookup_is_not_stamped_and_does_not_stop_later_cards(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher(missing={"Ghost"})
        proc.card_fetcher.search_card.side_effect = Exception("Card not found")
        with _quiet():
            proc.update_prices_data_repo([(1, "Ghost", "1,00"), (2, "Real", "")])
        updates = proc.collection_repository.bulk_update_prices.call_args[0][0]
        self.assertEqual([u.card_id for u in updates], [2])
        proc.collection_repository.update.assert_called_once_with(1, {"price_eur": "N/A"})
        self.assertEqual(proc.error_count, 1)

    def test_price_stats_counters(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher({"A": "2.00", "B": "1.00"})
        with _quiet():
            proc.update_prices_data_repo([(1, "A", "1,00"), (2, "B", "1,00")], skipped_fresh=4)
        stats = proc.price_stats
        self.assertEqual(
            (stats["cards_checked"], stats["skipped_fresh"], stats["prices_changed"], stats["requests_made"]),
            (2, 4, 1, 1),
        )
        self.assertIn("elapsed_seconds", stats)

    def test_cancellation_after_first_chunk_keeps_written_chunk(self):
        proc = _make_processor()
        proc.card_fetcher.get_cards_collection = _collection_fetcher()
        cards = [(i, f"Card {i}", "") for i in range(150)]

        class Cancelled(Exception):
            pass

        with _quiet(), patch("deckdex.magic_card_processor.tqdm") as tqdm_cls:
            tqdm_cls.return_value.__enter__.return_value.update.side_effect = Cancelled
            with self.assertRaises(Cancelled):
                proc.update_prices_data_repo(cards)
        first_call = proc.collection_repository.bulk_update_prices.call_args_list[0][0][0]
        self.assertEqual(len(first_call), 75)

    def test_nothing_to_update_message(self):
        proc = _make_processor()
        out = io.StringIO()
        with patch.dict(os.environ, {"TQDM_DISABLE": "1"}), contextlib.redirect_stdout(out):
            proc.update_prices_data_repo([], skipped_fresh=3)
        self.assertIn("Nothing to update", out.getvalue())
        proc.card_fetcher.get_cards_collection.assert_not_called()


class _StampingRepository:
    """Fake repository remembering price_last_checked_at like the Postgres one."""

    def __init__(self, cards):
        self.cards = cards
        self.stamps = {}
        self.history = []

    def get_cards_for_price_update(self):
        return list(self.cards)

    def get_price_last_checked(self, card_ids):
        return {i: self.stamps.get(i) for i in card_ids}

    def bulk_update_prices(self, updates):
        for update in updates:
            self.stamps[update.card_id] = update.checked_at
        return len(updates)

    def record_price_history(self, card_id, price, **_kwargs):
        self.history.append((card_id, price))

    def update(self, card_id, data):
        pass


class TestProcessCardDataFreshness(unittest.TestCase):
    def _processor(self, cards):
        proc = _make_processor()
        proc.collection_repository = _StampingRepository(cards)
        proc.card_fetcher.get_cards_collection = _collection_fetcher()
        return proc

    def test_first_run_looks_up_and_stamps_all_cards(self):
        proc = self._processor([(1, "A", ""), (2, "B", "")])
        with _quiet():
            proc.process_card_data()
        self.assertEqual(proc.card_fetcher.get_cards_collection.call_count, 1)
        self.assertEqual(set(proc.collection_repository.stamps), {1, 2})

    def test_immediate_rerun_makes_zero_lookups(self):
        proc = self._processor([(1, "A", ""), (2, "B", "")])
        with _quiet():
            proc.process_card_data()
            proc.card_fetcher.get_cards_collection.reset_mock()
            proc.process_card_data()
        proc.card_fetcher.get_cards_collection.assert_not_called()
        self.assertEqual(proc.price_stats["skipped_fresh"], 2)
        self.assertEqual(proc.price_stats["cards_checked"], 0)

    def test_force_looks_up_fresh_cards(self):
        proc = self._processor([(1, "A", ""), (2, "B", "")])
        with _quiet():
            proc.process_card_data()
            proc.card_fetcher.get_cards_collection.reset_mock()
            proc.process_card_data(force=True)
        self.assertEqual(proc.card_fetcher.get_cards_collection.call_count, 1)
        self.assertEqual(proc.price_stats["skipped_fresh"], 0)

    def test_null_stamp_card_is_looked_up_and_stamped(self):
        proc = self._processor([(1, "A", ""), (2, "B", "")])
        with _quiet():
            proc.process_card_data()
            proc.collection_repository.stamps[2] = None
            proc.card_fetcher.get_cards_collection.reset_mock()
            proc.process_card_data()
        self.assertEqual(proc.card_fetcher.get_cards_collection.call_args[0][0], ["B"])
        self.assertIsNotNone(proc.collection_repository.stamps[2])

    def test_full_refresh_makes_fewer_requests_than_per_card_baseline(self):
        cards = [(i, f"Card {i}", "") for i in range(150)]
        proc = self._processor(cards)
        with _quiet():
            proc.process_card_data()
        self.assertLess(proc.price_stats["requests_made"], len(cards))


class TestServiceForceAndStats(unittest.IsolatedAsyncioTestCase):
    def _service(self):
        from backend.api.services.processor_service import ProcessorService

        service = ProcessorService.__new__(ProcessorService)
        service.config = MagicMock()
        service.progress_callback = None
        service._job_repo = None
        service._user_id = 1
        service.job_id = "job"
        service.start_time = datetime.now()
        service.status = "pending"
        service.progress_data = {"current": 0, "total": 0, "percentage": 0.0, "errors": []}
        service._loop = None
        service._cancel_flag = threading.Event()
        service._lock = threading.Lock()
        return service

    async def _run(self, processor, force=False):
        service = self._service()
        with patch("backend.api.services.processor_service.MagicCardProcessor", return_value=processor):
            return await service.update_prices_async(force=force)

    async def test_force_is_passed_through(self):
        proc = MagicMock(error_count=0, not_found_cards=[])
        await self._run(proc, force=True)
        proc.process_card_data.assert_called_once_with(force=True)

    async def test_success_result_contains_price_stats(self):
        stats = {
            "cards_checked": 3,
            "skipped_fresh": 1,
            "prices_changed": 2,
            "requests_made": 1,
            "elapsed_seconds": 0.5,
        }
        proc = MagicMock(error_count=0, not_found_cards=[], price_stats=stats)
        result = await self._run(proc)
        self.assertEqual(result["status"], "success")
        for key, value in stats.items():
            self.assertEqual(result[key], value)

    async def test_cancelled_result_contains_price_stats(self):
        from backend.api.services.processor_service import JobCancelledException

        proc = MagicMock(error_count=1, not_found_cards=["X"], price_stats={"requests_made": 4})
        proc.process_card_data.side_effect = JobCancelledException("stop")
        result = await self._run(proc)
        self.assertEqual((result["status"], result["requests_made"], result["error_count"]), ("cancelled", 4, 1))

    async def test_magicmock_processor_still_succeeds(self):
        result = await self._run(MagicMock())
        self.assertEqual(result["status"], "success")


class TestUpdatePricesRoute(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        self.client = TestClient(app)
        self.service = MagicMock(job_id="job-1", status="pending")

        async def update_prices_async(force=False):
            return {"status": "success"}

        self.service.update_prices_async = MagicMock(side_effect=update_prices_async)
        patches = [
            patch("backend.api.routes.process.ProcessorService", return_value=self.service),
            patch("backend.api.routes.process.get_job_repo"),
            patch("deckdex.config_loader.load_config", return_value=MagicMock()),
            patch("backend.api.routes.process._active_jobs", {}),
            patch("backend.api.routes.process._job_types", {}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user_id, None)

    def test_no_body_runs_without_force(self):
        response = self.client.post("/api/prices/update")
        self.assertEqual(response.status_code, 200)
        self.service.update_prices_async.assert_called_once_with(force=False)

    def test_force_true_is_passed(self):
        response = self.client.post("/api/prices/update", json={"force": True})
        self.assertEqual(response.status_code, 200)
        self.service.update_prices_async.assert_called_once_with(force=True)

    def test_non_boolean_force_returns_400(self):
        response = self.client.post("/api/prices/update", json={"force": "maybe"})
        self.assertEqual(response.status_code, 400)

    def test_running_job_returns_409(self):
        from backend.api.routes import process

        running = MagicMock(status="running")
        process._active_jobs["other"] = running
        process._job_types["other"] = "update_prices"
        response = self.client.post("/api/prices/update")
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
