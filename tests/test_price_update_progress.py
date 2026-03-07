"""
Tests for price update buffered writes, progress notifications, and resume-from-interruption.
"""

import asyncio
import contextlib
import io
import os
import threading
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, call, patch


def _make_processor(batch_size=2, write_buffer_batches=2, use_repo=False):
    """
    Construct a MagicCardProcessor without triggering _initialize_clients.

    use_repo=True simulates Postgres path (collection_repository set).
    use_repo=False simulates Google Sheets path (spreadsheet_client set).
    """
    from deckdex.config import ProcessingConfig, ProcessorConfig
    from deckdex.magic_card_processor import MagicCardProcessor

    proc = MagicCardProcessor.__new__(MagicCardProcessor)
    proc.config = ProcessorConfig(
        processing=ProcessingConfig(
            batch_size=batch_size,
            write_buffer_batches=write_buffer_batches,
            max_workers=1,
            api_delay=0,
        )
    )
    proc.update_prices = True
    proc.dry_run = False
    proc._card_cache = {}
    proc.error_count = 0
    proc.last_error_count = 0
    proc.not_found_cards = []
    if use_repo:
        proc.collection_repository = MagicMock()
        proc.spreadsheet_client = None
    else:
        proc.collection_repository = None
        proc.spreadsheet_client = MagicMock()
        proc._headers_cache = ["Name", "Price"]
    return proc


# ---------------------------------------------------------------------------
# Task 2 — Config validation tests for write_buffer_batches
# ---------------------------------------------------------------------------


class TestWriteBufferBatchesConfig(unittest.TestCase):
    """Unit tests for ProcessingConfig.write_buffer_batches validation."""

    def test_write_buffer_batches_zero_raises(self):
        from deckdex.config import ProcessingConfig

        with self.assertRaises(ValueError) as ctx:
            ProcessingConfig(write_buffer_batches=0)
        self.assertIn("write_buffer_batches", str(ctx.exception))

    def test_write_buffer_batches_negative_raises(self):
        from deckdex.config import ProcessingConfig

        with self.assertRaises(ValueError):
            ProcessingConfig(write_buffer_batches=-1)

    def test_write_buffer_batches_one_is_valid(self):
        from deckdex.config import ProcessingConfig

        cfg = ProcessingConfig(write_buffer_batches=1)
        self.assertEqual(cfg.write_buffer_batches, 1)

    def test_write_buffer_batches_default_is_three(self):
        from deckdex.config import ProcessingConfig

        cfg = ProcessingConfig()
        self.assertEqual(cfg.write_buffer_batches, 3)


# ---------------------------------------------------------------------------
# Task 3 — Buffered write fires at correct interval (Google Sheets path)
# ---------------------------------------------------------------------------


class TestBufferedWriteGoogleSheetsPath(unittest.TestCase):
    """Tests for MagicCardProcessor.update_prices_data buffered write behavior."""

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_buffered_write_fires_after_write_buffer_batches(self):
        """With 6 cards, batch_size=2, write_buffer_batches=2: _write_buffered_prices fires at least twice."""
        proc = _make_processor(batch_size=2, write_buffer_batches=2, use_repo=False)
        # 6 cards × 2 per batch = 3 batches; threshold=2 => fires at batch 2 (mid-run) + remainder
        cards = [
            ["Card A", "0,50"],
            ["Card B", "0,50"],
            ["Card C", "0,50"],
            ["Card D", "0,50"],
            ["Card E", "0,50"],
            ["Card F", "0,50"],
        ]
        with (
            patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "2.00"}}),
            patch.object(proc, "_write_buffered_prices", return_value=2) as mock_write,
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                proc.update_prices_data(cards)
        self.assertGreaterEqual(mock_write.call_count, 2)

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_buffered_write_flushes_remainder_at_end(self):
        """With 4 cards, batch_size=2, write_buffer_batches=3: only one flush (end-of-loop remainder)."""
        proc = _make_processor(batch_size=2, write_buffer_batches=3, use_repo=False)
        # 4 cards / batch_size=2 = 2 batches; 2 < threshold=3 => no mid-run flush; only remainder flush
        cards = [
            ["Card A", "0,50"],
            ["Card B", "0,50"],
            ["Card C", "0,50"],
            ["Card D", "0,50"],
        ]
        with (
            patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "2.00"}}),
            patch.object(proc, "_write_buffered_prices", return_value=2) as mock_write,
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                proc.update_prices_data(cards)
        self.assertEqual(mock_write.call_count, 1)

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_no_write_when_no_price_changes(self):
        """When all cards have unchanged prices, _write_buffered_prices is never called."""
        proc = _make_processor(batch_size=2, write_buffer_batches=2, use_repo=False)
        # current_price == new_price => no pending_changes
        cards = [
            ["Card A", "1,00"],
            ["Card B", "1,00"],
            ["Card C", "1,00"],
            ["Card D", "1,00"],
        ]
        with (
            patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "1.00"}}),
            patch.object(proc, "_write_buffered_prices", return_value=0) as mock_write,
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                # Note: Scryfall returns "1.00", processor converts to "1,00" which equals current_price
                proc.update_prices_data(cards)
        mock_write.assert_not_called()

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_write_buffer_batches_one_writes_after_every_batch(self):
        """With write_buffer_batches=1 and 4 cards (2 batches), _write_buffered_prices is called >= 2 times."""
        proc = _make_processor(batch_size=2, write_buffer_batches=1, use_repo=False)
        cards = [
            ["Card A", "0,50"],
            ["Card B", "0,50"],
            ["Card C", "0,50"],
            ["Card D", "0,50"],
        ]
        with (
            patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "2.00"}}),
            patch.object(proc, "_write_buffered_prices", return_value=2) as mock_write,
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                proc.update_prices_data(cards)
        self.assertGreaterEqual(mock_write.call_count, 2)


# ---------------------------------------------------------------------------
# Task 4 — Resume-from-interruption tests (Postgres path)
# ---------------------------------------------------------------------------


class TestResumePriceUpdatePostgresPath(unittest.TestCase):
    """Tests for MagicCardProcessor.update_prices_data_repo resume-from-interruption behavior."""

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_resume_only_processes_remaining_cards(self):
        """Resume from card 4: only Card E and Card F are fetched (not the first 4)."""
        proc = _make_processor(batch_size=2, write_buffer_batches=2, use_repo=True)
        # Simulate: cards 0-3 already processed; resume with only the remaining 2
        remaining_cards = [(5, "Card E", "0,50"), (6, "Card F", "0,50")]
        with patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "2.00"}}) as mock_fetch:
            with contextlib.redirect_stdout(io.StringIO()):
                proc.update_prices_data_repo(remaining_cards)
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(mock_fetch.call_args_list, [call("Card E"), call("Card F")])

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_no_duplicate_db_writes_when_price_unchanged(self):
        """When Scryfall returns the same price as current, no DB writes occur."""
        proc = _make_processor(batch_size=2, write_buffer_batches=2, use_repo=True)
        # current_price "1,00" == processed price "1,00" from Scryfall "1.00"
        cards = [
            (1, "Card A", "1,00"),
            (2, "Card B", "1,00"),
            (3, "Card C", "1,00"),
        ]
        with patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "1.00"}}):
            with contextlib.redirect_stdout(io.StringIO()):
                proc.update_prices_data_repo(cards)
        proc.collection_repository.update.assert_not_called()
        proc.collection_repository.record_price_history.assert_not_called()

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_price_history_recorded_for_numeric_price(self):
        """When price changes to a numeric value, record_price_history is called with the float value."""
        proc = _make_processor(batch_size=2, write_buffer_batches=2, use_repo=True)
        # current_price empty string, Scryfall returns 1.50 => new_price = "1,50"
        cards = [
            (1, "Card A", ""),
            (2, "Card B", ""),
        ]
        with patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "1.50"}}):
            with contextlib.redirect_stdout(io.StringIO()):
                proc.update_prices_data_repo(cards)
        # record_price_history should have been called with float 1.5
        calls = proc.collection_repository.record_price_history.call_args_list
        self.assertEqual(len(calls), 2)
        for c in calls:
            price_arg = c[0][1]
            self.assertAlmostEqual(price_arg, 1.5)

    @patch.dict(os.environ, {"TQDM_DISABLE": "1"})
    def test_price_history_skipped_for_na_price(self):
        """When Scryfall returns None price (N/A), record_price_history is never called."""
        proc = _make_processor(batch_size=1, write_buffer_batches=1, use_repo=True)
        cards = [(1, "Card A", "0,50")]
        # None price => _process_price returns "N/A"
        with patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": None}}):
            with contextlib.redirect_stdout(io.StringIO()):
                proc.update_prices_data_repo(cards)
        proc.collection_repository.record_price_history.assert_not_called()


# ---------------------------------------------------------------------------
# Task 5 — ProcessorService async complete event tests
# ---------------------------------------------------------------------------


class TestProcessorServiceUpdatePricesAsync(unittest.IsolatedAsyncioTestCase):
    """Tests for ProcessorService.update_prices_async complete event emission."""

    def _make_service(self):
        from backend.api.services.processor_service import ProcessorService

        service = ProcessorService.__new__(ProcessorService)
        service.config = MagicMock()
        service.progress_callback = None
        service._job_repo = None
        service._user_id = 1
        service.job_id = "test-price-update-job"
        service.start_time = datetime.now()
        service.status = "pending"
        service.progress_data = {"current": 0, "total": 0, "percentage": 0.0, "errors": []}
        service._loop = None
        service._cancel_flag = threading.Event()
        service._lock = threading.Lock()
        return service

    async def test_update_prices_async_emits_complete_event(self):
        """update_prices_async emits a 'complete' event via the progress_callback."""
        service = self._make_service()
        service.progress_callback = AsyncMock()

        with patch("backend.api.services.processor_service.MagicCardProcessor") as MockProcessor:
            mock_proc = MagicMock()
            mock_proc.error_count = 0
            mock_proc.not_found_cards = []
            mock_proc.process_card_data.return_value = None
            MockProcessor.return_value = mock_proc

            await service.update_prices_async()

        calls = service.progress_callback.call_args_list
        self.assertTrue(len(calls) >= 1, "progress_callback should be called at least once")
        event_types = [c[0][0]["type"] for c in calls]
        self.assertIn("complete", event_types)

    async def test_update_prices_async_status_becomes_complete_on_success(self):
        """After a successful update_prices_async, service.status is 'complete'."""
        service = self._make_service()

        with patch("backend.api.services.processor_service.MagicCardProcessor") as MockProcessor:
            mock_proc = MagicMock()
            mock_proc.error_count = 0
            mock_proc.not_found_cards = []
            mock_proc.process_card_data.return_value = None
            MockProcessor.return_value = mock_proc

            await service.update_prices_async()

        self.assertEqual(service.status, "complete")

    async def test_update_prices_async_status_becomes_error_on_failure(self):
        """When the inner processor raises, service.status becomes 'error'."""
        service = self._make_service()

        with patch("backend.api.services.processor_service.MagicCardProcessor") as MockProcessor:
            mock_proc = MagicMock()
            mock_proc.error_count = 0
            mock_proc.not_found_cards = []
            mock_proc.process_card_data.side_effect = RuntimeError("simulated failure")
            MockProcessor.return_value = mock_proc

            result = await service.update_prices_async()

        # The inner run_update catches the exception and returns {"status": "error"}
        self.assertEqual(service.status, "error")
        self.assertEqual(result.get("status"), "error")


# ---------------------------------------------------------------------------
# Task 3 (new) — ProgressCapture unit tests
# ---------------------------------------------------------------------------


class TestProgressCaptureCallback(unittest.TestCase):
    """Unit tests for ProgressCapture write() and callback firing logic."""

    def test_tqdm_pattern_match_fires_callback(self):
        """A valid tqdm-formatted string triggers the callback with (current, total, percentage)."""
        from backend.api.services.processor_service import ProgressCapture

        mock_callback = MagicMock()
        capture = ProgressCapture(io.StringIO(), mock_callback)
        capture.write("  45%|#####     | 45/100 [00:05<00:06]")

        self.assertEqual(mock_callback.call_count, 1)
        args = mock_callback.call_args[0]
        self.assertEqual(args[0], 45)  # current
        self.assertEqual(args[1], 100)  # total
        self.assertEqual(args[2], 45.0)  # percentage

    def test_flush_notification_does_not_fire_callback(self):
        """A flush/write-notification string that does not match the tqdm regex does not fire the callback."""
        from backend.api.services.processor_service import ProgressCapture

        mock_callback = MagicMock()
        capture = ProgressCapture(io.StringIO(), mock_callback)
        capture.write("\nWrite #1 (40 cards): 12 updates")

        self.assertEqual(mock_callback.call_count, 0)

    def test_cancel_event_set_raises_on_write(self):
        """When the cancel_event is set, write() raises JobCancelledException."""
        from backend.api.services.processor_service import JobCancelledException, ProgressCapture

        cancel_event = threading.Event()
        cancel_event.set()
        mock_callback = MagicMock()
        capture = ProgressCapture(io.StringIO(), mock_callback, cancel_event=cancel_event)

        with self.assertRaises(JobCancelledException):
            capture.write("any text")


# ---------------------------------------------------------------------------
# Task 4 (new) — ProcessorService._on_tqdm_progress unit tests
# ---------------------------------------------------------------------------


class TestProcessorServiceProgressEvents(unittest.IsolatedAsyncioTestCase):
    """Unit tests for ProcessorService._on_tqdm_progress state mutations and scheduling."""

    def _make_service(self):
        from backend.api.services.processor_service import ProcessorService

        service = ProcessorService.__new__(ProcessorService)
        service.config = MagicMock()
        service.progress_callback = AsyncMock()
        service._job_repo = None
        service._user_id = 1
        service.job_id = "test-job"
        service.start_time = datetime.now()
        service.status = "running"
        service.progress_data = {"current": 0, "total": 0, "percentage": 0.0, "errors": []}
        service._cancel_flag = threading.Event()
        service._lock = threading.Lock()
        service._loop = None
        return service

    def test_on_tqdm_progress_updates_progress_data(self):
        """_on_tqdm_progress mutates progress_data correctly when not cancelled and no loop set."""
        service = self._make_service()
        # No loop set — only state mutation is exercised, no coroutine is scheduled
        service._loop = None
        service._on_tqdm_progress(30, 100, 30.0)

        self.assertEqual(service.progress_data["current"], 30)
        self.assertEqual(service.progress_data["total"], 100)
        self.assertEqual(service.progress_data["percentage"], 30.0)

    def test_on_tqdm_progress_skipped_when_cancelled(self):
        """_on_tqdm_progress returns early without updating state when the cancel flag is set."""
        service = self._make_service()
        service._cancel_flag.set()
        service._on_tqdm_progress(50, 100, 50.0)

        # progress_data must remain at initial values (early return before mutation)
        self.assertEqual(service.progress_data["current"], 0)
        self.assertEqual(service.progress_data["total"], 0)
        self.assertEqual(service.progress_data["percentage"], 0.0)

    async def test_on_tqdm_progress_schedules_coroutine_when_loop_set(self):
        """When _loop is set, _on_tqdm_progress schedules a 'progress' event via the callback."""
        service = self._make_service()
        loop = asyncio.get_event_loop()
        service._loop = loop
        service.progress_callback = AsyncMock()

        # _on_tqdm_progress uses run_coroutine_threadsafe which is designed for cross-thread use.
        # Call it from a background thread so the Future is correctly enqueued onto the running loop.
        done = threading.Event()

        def call_from_thread():
            service._on_tqdm_progress(50, 100, 50.0)
            done.set()

        t = threading.Thread(target=call_from_thread)
        t.start()
        t.join(timeout=2)

        # Give the event loop a chance to run the scheduled coroutine
        await asyncio.sleep(0.05)

        self.assertGreaterEqual(service.progress_callback.call_count, 1)
        first_call_arg = service.progress_callback.call_args_list[0][0][0]
        self.assertEqual(first_call_arg["type"], "progress")
