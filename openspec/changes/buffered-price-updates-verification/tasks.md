# Tasks: Buffered Price Updates Verification

All tasks are test-only. No production code is modified.

---

## Task 1 — Add write_buffer_batches YAML parsing tests

**File:** `tests/test_config_loader.py`

**Where:** Append a new class `TestWriteBufferBatchesYamlParsing` after the existing
`TestPriorityOrder` class.

**What to implement:**

Create a class that uses `tempfile.NamedTemporaryFile` (deleted via `os.unlink` in a
`finally` block, mirroring the pattern in `TestConfigLoader.test_load_yaml_config_with_profiles`)
with this YAML content:

```yaml
default:
  processing:
    batch_size: 20
    max_workers: 4
    api_delay: 0.1
    write_buffer_batches: 3
  api:
    scryfall:
      max_retries: 3
      retry_delay: 0.5
      timeout: 10.0
    google_sheets:
      batch_size: 500
      max_retries: 5
      retry_delay: 2.0
      sheet_name: magic
      worksheet_name: cards
    openai:
      enabled: false
      model: gpt-3.5-turbo
      max_tokens: 150
      temperature: 0.7
      max_retries: 3

development:
  processing:
    batch_size: 10
    max_workers: 2
    api_delay: 0.2
    write_buffer_batches: 2

production:
  processing:
    batch_size: 50
    max_workers: 8
    api_delay: 0.05
    write_buffer_batches: 5
```

**Test methods:**

1. `test_default_profile_write_buffer_batches`:
   - Call `load_yaml_config(temp_path, "default")` then
     `build_processor_config(yaml_config)`.
   - Assert `config.processing.write_buffer_batches == 3`.

2. `test_development_profile_write_buffer_batches`:
   - Call `load_yaml_config(temp_path, "development")` then `build_processor_config(...)`.
   - Assert `config.processing.write_buffer_batches == 2`.
   - Also assert `config.processing.batch_size == 10` (confirms deep-merge from
     development profile override, not a regression).

3. `test_production_profile_write_buffer_batches`:
   - Call `load_yaml_config(temp_path, "production")` then `build_processor_config(...)`.
   - Assert `config.processing.write_buffer_batches == 5`.

**Acceptance criteria:** All three tests pass. The temp file is cleaned up regardless of
test outcome (use `finally: os.unlink(temp_path)`).

**Dependencies:** None. Can be implemented immediately.

---

## Task 2 — Add write_buffer_batches env override test

**File:** `tests/test_config_loader.py`

**Where:** Append a new class `TestWriteBufferBatchesEnvOverride` after
`TestWriteBufferBatchesYamlParsing`.

**What to implement:**

Class inherits from `unittest.TestCase`. Use the `setUp`/`tearDown` pattern from
`TestEnvOverrides` to save and restore `os.environ`:

```python
def setUp(self):
    self.original_env = os.environ.copy()

def tearDown(self):
    os.environ.clear()
    os.environ.update(self.original_env)
```

**Test methods:**

1. `test_env_override_write_buffer_batches`:
   - Start with a base config dict: `{"processing": {"batch_size": 20, "max_workers": 4,
     "api_delay": 0.1, "write_buffer_batches": 3}, "api": {"scryfall": {}, "google_sheets":
     {}, "openai": {}}}`.
   - Set `os.environ["DECKDEX_PROCESSING_WRITE_BUFFER_BATCHES"] = "7"`.
   - Call `apply_env_overrides(config)` then `build_processor_config(config)`.
   - Assert `config_result.processing.write_buffer_batches == 7`.
   - Assert the type is `int` (not string).

2. `test_env_override_write_buffer_batches_invalid_value_raises`:
   - Set `os.environ["DECKDEX_PROCESSING_WRITE_BUFFER_BATCHES"] = "0"`.
   - Call `apply_env_overrides` then `build_processor_config`.
   - Assert `ValueError` is raised (from `ProcessingConfig.__post_init__`).

**Acceptance criteria:** Both tests pass. `os.environ` is restored to its original state
after each test (tearDown runs even on failure).

**Dependencies:** Task 1 (same file, append after).

---

## Task 3 — Add ProgressCapture unit tests

**File:** `tests/test_price_update_progress.py`

**Where:** Append a new class `TestProgressCaptureCallback` after the existing
`TestResumePriceUpdatePostgresPath` class (before the existing
`TestProcessorServiceUpdatePricesAsync`).

**What to implement:**

Import `ProgressCapture` from `backend.api.services.processor_service`.

The `ProgressCapture` constructor takes `(original_stream, callback, cancel_event=None)`.
Use `io.StringIO()` as `original_stream` and a `MagicMock()` as the callback.

**Test methods:**

1. `test_tqdm_pattern_match_fires_callback`:
   - Create `ProgressCapture(io.StringIO(), mock_callback)`.
   - Write a valid tqdm string: `"  45%|#####     | 45/100 [00:05<00:06]"`.
   - Assert `mock_callback.call_count == 1`.
   - Assert `mock_callback.call_args[0]` is `(45, 100, 45.0)` — positional args
     `(current, total, percentage)`.

2. `test_flush_notification_does_not_fire_callback`:
   - Create `ProgressCapture(io.StringIO(), mock_callback)`.
   - Write the flush notification string:
     `"\nWrite #1 (40 cards): 12 updates"` (a string that does NOT match the tqdm
     regex pattern `\d+%\|.*?\|\s*\d+/\d+`).
   - Assert `mock_callback.call_count == 0`.

3. `test_cancel_event_set_raises_on_write`:
   - Create a `threading.Event()`, set it, then create
     `ProgressCapture(io.StringIO(), mock_callback, cancel_event=cancel_event)`.
   - Call `capture.write("any text")` and assert `JobCancelledException` is raised.
   - Import `JobCancelledException` from `backend.api.services.processor_service`.

**Acceptance criteria:** All three tests pass without external I/O. `io.StringIO()` is
used for stream isolation.

**Dependencies:** None. Can be implemented alongside Task 4.

---

## Task 4 — Add ProcessorService._on_tqdm_progress unit tests

**File:** `tests/test_price_update_progress.py`

**Where:** Append a new class `TestProcessorServiceProgressEvents` after
`TestProgressCaptureCallback`.

**What to implement:**

Build a minimal `ProcessorService` instance using `ProcessorService.__new__` (same
pattern as `TestProcessorServiceUpdatePricesAsync._make_service`). The helper should set:

```python
import threading
from datetime import datetime

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
```

**Test methods:**

1. `test_on_tqdm_progress_updates_progress_data`:
   - Call `service._on_tqdm_progress(30, 100, 30.0)`.
   - Assert `service.progress_data["current"] == 30`.
   - Assert `service.progress_data["total"] == 100`.
   - Assert `service.progress_data["percentage"] == 30.0`.
   - (No loop set, so no coroutine scheduled — tests state mutation only.)

2. `test_on_tqdm_progress_skipped_when_cancelled`:
   - Set `service._cancel_flag.set()`.
   - Call `service._on_tqdm_progress(50, 100, 50.0)`.
   - Assert `service.progress_data["current"] == 0` (unchanged — early return).

3. `test_on_tqdm_progress_schedules_coroutine_when_loop_set`:
   - Create a real event loop with `asyncio.new_event_loop()`.
   - Set `service._loop = loop`.
   - Set `service.progress_callback = AsyncMock()`.
   - Call `service._on_tqdm_progress(50, 100, 50.0)`.
   - Run the loop briefly to drain the scheduled coroutine:
     `loop.run_until_complete(asyncio.sleep(0))` (one iteration is enough for
     `run_coroutine_threadsafe` futures to resolve when called from the same thread in
     test context — alternatively call `loop.call_soon_threadsafe` style; use
     `asyncio.run_coroutine_threadsafe(...).result(timeout=1)` is not available here
     since we need the loop to run).
   - A simpler approach: use `unittest.IsolatedAsyncioTestCase` and `asyncio.get_event_loop()`
     to provide a running loop, then call `_on_tqdm_progress` from a thread via
     `threading.Thread` and join it, then `await asyncio.sleep(0)`.
   - Assert `service.progress_callback.call_count >= 1`.
   - Assert the first call's argument has `{"type": "progress"}`.
   - Close the loop in teardown.

   Implementation note: The simplest reliable approach for testing `run_coroutine_threadsafe`
   is to subclass `unittest.IsolatedAsyncioTestCase`, set `service._loop =
   asyncio.get_event_loop()` inside the async test (the running loop), call
   `_on_tqdm_progress` synchronously (it uses `run_coroutine_threadsafe` which can be
   called from any thread when a loop is already running), then `await asyncio.sleep(0)`
   to drain the pending coroutine.

**Acceptance criteria:** All three tests pass. No real event loop creation issues;
`IsolatedAsyncioTestCase` manages the loop lifecycle.

**Dependencies:** None. Can be implemented alongside Task 3.

---

## Task 5 — Verify all new and existing tests pass

**No file changes.** Verification step.

Run from the repo root:

```
pytest tests/test_config_loader.py tests/test_price_update_progress.py -v
```

Expected outcome:
- All existing tests in both files continue to pass (no regression).
- All new tests added in Tasks 1-4 pass.
- No warnings about `scope="module"` on mocked fixtures.

If any test fails:
- Check that `os.environ` teardown is running (verify `TestWriteBufferBatchesEnvOverride`
  uses `setUp`/`tearDown`, not `setUpClass`/`tearDownClass`).
- Check that `IsolatedAsyncioTestCase` loop lifetime covers the coroutine drain in Task 4.
- Check that the tqdm pattern string in Task 3 exactly matches the regex
  `(\d+)%\|.*?\|\s*(\d+)/(\d+)` — use a string like `"  45%|#####     | 45/100 [...]"`.

**Acceptance criteria:** Zero test failures. Zero new deprecation warnings introduced.
