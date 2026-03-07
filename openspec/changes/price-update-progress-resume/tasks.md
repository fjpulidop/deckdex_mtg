# Tasks: price-update-progress-resume

All tasks are test-only. No production code changes. Execute in the order listed.

---

## Task 1: Create test file scaffold with shared helper

**Layer:** Tests (`tests/`)
**File:** `tests/test_price_update_progress.py`
**Depends on:** Nothing

Create the test file with a shared `_make_processor` factory helper used by all subsequent test groups. The helper constructs `MagicCardProcessor` via `__new__` (bypassing `_initialize_clients` which requires live credentials) and sets up the minimum attributes needed for price update methods.

**Implementation:**

```python
"""
Tests for price update buffered writes, progress notifications, and resume-from-interruption.
"""
import os
import unittest
from unittest.mock import MagicMock, patch, call


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
```

**Acceptance criteria:**
- File is importable without error: `python -m pytest tests/test_price_update_progress.py --collect-only` reports collected items (even with no test classes yet).
- `_make_processor()` returns a `MagicCardProcessor` instance without raising.

---

## Task 2: Config validation tests for write_buffer_batches

**Layer:** Tests (`tests/`)
**File:** `tests/test_price_update_progress.py`
**Depends on:** Task 1

Add `TestWriteBufferBatchesConfig` class testing that `ProcessingConfig` validates `write_buffer_batches`.

**Tests to add:**

- `test_write_buffer_batches_zero_raises`: Construct `ProcessingConfig(write_buffer_batches=0)`. Assert `ValueError` is raised. Assert the error message contains `"write_buffer_batches"`.
- `test_write_buffer_batches_negative_raises`: Construct `ProcessingConfig(write_buffer_batches=-1)`. Assert `ValueError` is raised.
- `test_write_buffer_batches_one_is_valid`: Construct `ProcessingConfig(write_buffer_batches=1)`. Assert no exception. Assert `.write_buffer_batches == 1`.
- `test_write_buffer_batches_default_is_three`: Construct `ProcessingConfig()` with no args. Assert `.write_buffer_batches == 3`.

**Acceptance criteria:**
- All 4 tests pass with `pytest tests/test_price_update_progress.py::TestWriteBufferBatchesConfig`.
- Tests use `scope` implicitly (class-based, no fixtures needing scope).

---

## Task 3: Buffered write fires at correct interval (Google Sheets path)

**Layer:** Tests (`tests/`)
**File:** `tests/test_price_update_progress.py`
**Depends on:** Task 1

Add `TestBufferedWriteGoogleSheetsPath` class testing `MagicCardProcessor.update_prices_data`.

**Context:** `update_prices_data` takes a `List[List[str]]` where each item is `[card_name, current_price]`. The method runs `ThreadPoolExecutor` over batches, accumulates `pending_changes`, and calls `_write_buffered_prices` when `batches_processed >= write_buffer_batches`.

Suppress tqdm and stdout output by patching `os.environ` with `TQDM_DISABLE=1` and redirecting stdout via `contextlib.redirect_stdout(io.StringIO())`.

**Tests to add:**

- `test_buffered_write_fires_after_write_buffer_batches`: batch_size=2, write_buffer_batches=2, 6 cards with price changes. Mock `_fetch_card_data` to return `{"prices": {"eur": "2.00"}}` for all. Mock `_write_buffered_prices` to return 2. Assert `_write_buffered_prices` is called at least twice (once mid-run at batch 2, once at end for batch 3 remainder).

- `test_buffered_write_flushes_remainder_at_end`: batch_size=2, write_buffer_batches=3, 4 cards (2 batches only). All prices change. Assert `_write_buffered_prices` is called exactly once (the end-of-loop remainder flush, since 2 < 3 threshold).

- `test_no_write_when_no_price_changes`: batch_size=2, write_buffer_batches=2, 4 cards. Mock `_fetch_card_data` to return `{"prices": {"eur": "1,00"}}`. Set all input cards' `current_price` to `"1,00"` (same value, no change). Assert `_write_buffered_prices` is never called.

- `test_write_buffer_batches_one_writes_after_every_batch`: batch_size=2, write_buffer_batches=1, 4 cards (2 batches). All prices change. Assert `_write_buffered_prices` call count >= 2.

**Patching pattern:**
```python
@patch.dict(os.environ, {"TQDM_DISABLE": "1"})
def test_buffered_write_fires_after_write_buffer_batches(self):
    import io, contextlib
    proc = _make_processor(batch_size=2, write_buffer_batches=2, use_repo=False)
    cards = [["Card A", "0,50"], ["Card B", "0,50"], ["Card C", "0,50"],
             ["Card D", "0,50"], ["Card E", "0,50"], ["Card F", "0,50"]]
    with patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "2.00"}}), \
         patch.object(proc, "_write_buffered_prices", return_value=2) as mock_write:
        with contextlib.redirect_stdout(io.StringIO()):
            proc.update_prices_data(cards)
    self.assertGreaterEqual(mock_write.call_count, 2)
```

**Acceptance criteria:**
- All 4 tests pass.
- No real gspread calls are made (confirmed by `proc.spreadsheet_client` never being called directly on `_write_buffered_prices` — it is mocked at that level).

---

## Task 4: Resume-from-interruption tests (Postgres path)

**Layer:** Tests (`tests/`)
**File:** `tests/test_price_update_progress.py`
**Depends on:** Task 1

Add `TestResumePriceUpdatePostgresPath` class testing `MagicCardProcessor.update_prices_data_repo`.

**Context:** `update_prices_data_repo` takes `List[Tuple[int, str, str]]` where each item is `(card_id, card_name, current_price_str)`. It calls `_fetch_card_data(card_name)` for each card in batches, then calls `collection_repository.update(card_id, {...})` and `record_price_history` for changed prices.

**Resume-from logic:** The caller is responsible for passing only the unprocessed sublist. The test simulates this by calling `update_prices_data_repo` with only the tail of the full card list (cards that weren't processed before interruption).

**Tests to add:**

- `test_resume_only_processes_remaining_cards`: Full list has 6 cards. "Interruption" after card index 3 (cards 0-3 already done). Resume by calling with only cards 4-5. Assert `_fetch_card_data` called exactly 2 times with names "Card E" and "Card F" (not the already-processed ones).

- `test_no_duplicate_db_writes_when_price_unchanged`: Pass 3 cards where Scryfall returns the same price as current. Assert `collection_repository.update` is never called. Assert `collection_repository.record_price_history` is never called.

- `test_price_history_recorded_for_numeric_price`: Pass 2 cards with current_price="" and Scryfall returning `{"eur": "1.50"}`. Confirm `_process_price` converts to `"1,50"`. Assert `record_price_history` called with `pytest.approx(1.5)` (after `float(str("1,50").replace(",", "."))` in the method).

- `test_price_history_skipped_for_na_price`: Pass 1 card where Scryfall returns `None` or `{"eur": None}`, leading to `new_price = "N/A"`. Assert `record_price_history` is never called (the `except (ValueError, TypeError): pass` block in the method handles `float("N/A")`).

**Patching pattern:**
```python
@patch.dict(os.environ, {"TQDM_DISABLE": "1"})
def test_resume_only_processes_remaining_cards(self):
    import io, contextlib
    proc = _make_processor(batch_size=2, write_buffer_batches=2, use_repo=True)
    # Simulate: cards 0-3 already processed, resume from card 4
    remaining_cards = [(5, "Card E", "0,50"), (6, "Card F", "0,50")]
    with patch.object(proc, "_fetch_card_data", return_value={"prices": {"eur": "2.00"}}) as mock_fetch:
        with contextlib.redirect_stdout(io.StringIO()):
            proc.update_prices_data_repo(remaining_cards)
    self.assertEqual(mock_fetch.call_count, 2)
    self.assertEqual(mock_fetch.call_args_list, [call("Card E"), call("Card F")])
```

**Acceptance criteria:**
- All 4 tests pass.
- `collection_repository.update` and `record_price_history` call counts are verifiable (MagicMock records all calls).

---

## Task 5: ProcessorService async complete event test

**Layer:** Tests (`tests/`)
**File:** `tests/test_price_update_progress.py`
**Depends on:** Tasks 1-4

Add `TestProcessorServiceUpdatePricesAsync` class using `unittest.IsolatedAsyncioTestCase` (consistent with `test_job_persistence.py`'s `TestProcessorServiceSingleCardPersist`).

**Tests to add:**

- `test_update_prices_async_emits_complete_event`: Construct `ProcessorService` via `__new__` (same pattern as `test_job_persistence.py`). Patch `MagicCardProcessor.process_card_data` to return immediately (no-op). Set `service.progress_callback` to an `AsyncMock`. Call `await service.update_prices_async()`. Assert the callback was called at least once with a dict where `event["type"] == "complete"`.

- `test_update_prices_async_status_becomes_complete_on_success`: Same setup. After `await service.update_prices_async()`, assert `service.status == "complete"`.

- `test_update_prices_async_status_becomes_error_on_failure`: Patch `MagicCardProcessor.process_card_data` to raise `RuntimeError("simulated failure")`. Assert `service.status == "error"` after the call returns (the inner thread catches the exception and returns `{"status": "error"}`). The outer `try/except` in `update_prices_async` only triggers if `run_in_executor` itself raises, not if the inner function handles it — so status should be `"error"` from the inner result, not a raised exception.

**Helper for constructing ProcessorService (mirrors test_job_persistence.py):**
```python
def _make_service(self):
    import threading
    from datetime import datetime
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
```

**Acceptance criteria:**
- All 3 tests pass with `IsolatedAsyncioTestCase`.
- No real `MagicCardProcessor` execution occurs (patched out).
- `progress_callback` is an `AsyncMock` so `await callback(event)` works correctly in `_emit_progress`.

---

## Task 6: Run full test suite and verify no regressions

**Layer:** Tests (`tests/`)
**File:** All
**Depends on:** Tasks 1-5

Run `pytest tests/test_price_update_progress.py -v` and verify all tests in the new file pass.

Run `pytest tests/ -x --tb=short` to verify no regressions in existing tests.

**Acceptance criteria:**
- All tests in `tests/test_price_update_progress.py` pass (target: 15 tests total across 4 test classes).
- Zero regressions in existing test suite (`tests/` directory).
- No `DeprecationWarning` from accessing the deprecated `config.write_buffer_batches` property (all tests use `config.processing.write_buffer_batches`).
