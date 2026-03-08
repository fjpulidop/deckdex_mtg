# Design: Buffered Price Updates Verification

## Context

This design addresses two verification gaps identified after the buffered price update
feature was merged. No production code changes are planned — this is a test-only change.

### Key files involved

| File | Role |
|---|---|
| `deckdex/config.py` | `ProcessingConfig` dataclass; `write_buffer_batches` field with `>= 1` validation |
| `deckdex/config_loader.py` | YAML load + env override + `build_processor_config` pipeline |
| `config.yaml` | Three profiles: default=3, development=2, production=5 |
| `deckdex/magic_card_processor.py` | `update_prices_data` (GSheets path); `update_prices_data_repo` (Postgres path) |
| `backend/api/services/processor_service.py` | `ProcessorService`; `_on_tqdm_progress`; `_emit_progress`; `update_prices_async` |
| `tests/test_config_loader.py` | Existing config loading tests — extend here |
| `tests/test_price_update_progress.py` | Existing buffered write + async tests — extend here |

---

## Gap 1: Config Parsing End-to-End

### What exists

`ProcessingConfig.__post_init__` validates `write_buffer_batches >= 1` and raises
`ValueError` on violation. This is already tested in `test_config_validation.py`
(`TestProcessingConfig.test_invalid_write_buffer_batches`).

`build_processor_config` in `config_loader.py` (line 234) constructs `ProcessingConfig`
from the `processing` sub-dict of the merged YAML. `write_buffer_batches` is a plain key
under `processing:` in `config.yaml`, so it will be included in `processing_cfg` when
present.

### What is missing

1. **YAML profile propagation**: No test loads the actual `config.yaml` (or a temp YAML
   with the same structure) through `load_yaml_config` and asserts the
   `write_buffer_batches` value from each profile reaches the final `ProcessingConfig`.
   The `test_config_loader.py` tests use inline YAML strings that omit
   `write_buffer_batches`.

2. **Env override**: `apply_env_overrides` maps `DECKDEX_PROCESSING_WRITE_BUFFER_BATCHES`
   to `processing.write_buffer_batches` via the `section_mapping["processing"]` path
   (line 117, `config_loader.py`). There is no test exercising this specific key.

### Design

Extend `tests/test_config_loader.py` with two new test classes.

**`TestWriteBufferBatchesYamlParsing`** — uses `tempfile.NamedTemporaryFile` with an
inline YAML that mirrors the real `config.yaml` structure (all three profiles) and verifies
the correct value emerges from `load_yaml_config` + `build_processor_config`.

```python
# Test structure (pseudocode)
yaml_content = """
default:
  processing:
    batch_size: 20
    max_workers: 4
    api_delay: 0.1
    write_buffer_batches: 3
  api: {scryfall: {}, google_sheets: {}, openai: {}}

development:
  processing:
    write_buffer_batches: 2

production:
  processing:
    write_buffer_batches: 5
"""
```

Tests:
- `test_default_profile_write_buffer_batches` — asserts value is 3
- `test_development_profile_write_buffer_batches` — asserts value is 2, confirms
  deep-merge preserved `batch_size: 20` from default
- `test_production_profile_write_buffer_batches` — asserts value is 5

**`TestWriteBufferBatchesEnvOverride`** — uses `setUp`/`tearDown` pattern from existing
`TestEnvOverrides` to restore env. Sets `DECKDEX_PROCESSING_WRITE_BUFFER_BATCHES=7` and
calls `apply_env_overrides` + `build_processor_config`, asserting the resulting
`processing.write_buffer_batches == 7`.

Important: the `tearDown` pattern in `TestEnvOverrides` saves and restores
`os.environ.copy()`. Reuse this pattern exactly — do not leave env contamination.

---

## Gap 2: Per-Flush Progress Event Emission

### What exists

`ProcessorService._on_tqdm_progress` (lines 184-207) fires when tqdm writes a progress
line to stderr. It calls `asyncio.run_coroutine_threadsafe(_emit_progress("progress", ...))`.
This is the mechanism for real-time progress events.

`ProcessorService.update_prices_async` (lines 288-358) runs the processor in a
`ThreadPoolExecutor`, then emits a single `complete` event on finish.

The spec requirement is: "Notify user after each incremental write (write number, update
counts)." The print statement in `update_prices_data` (`Colors.GREEN "✓ Write #N ..."`)
goes to stdout, which is captured by the `ProgressCapture` wrapper in
`ProcessorService`. However, `ProgressCapture.write()` only emits progress events when
it matches the `_tqdm_pattern` regex (`\d+%\|.*?\|\s*\d+/\d+`). The write notification
output does NOT match this pattern, so no WebSocket event is emitted per flush.

### What the spec actually requires vs what is practical

The spec says "Notify user after each incremental write." In the current architecture
the notification is the print to stdout (captured by `ProgressCapture`). The `_on_tqdm_progress`
callback is invoked indirectly from `ProgressCapture.write()`. Progress events are already
emitted as tqdm updates the bar — these are per-batch events that effectively track the
work done between flushes.

The gap is whether a specific `flush` or `buffer_write` WebSocket event type should be
emitted. Looking at the existing tests in `test_price_update_progress.py`, class
`TestProcessorServiceUpdatePricesAsync` tests that:
- A `complete` event is emitted
- Status becomes `complete` on success
- Status becomes `error` on failure

These tests do not verify that intermediate `progress` events are emitted during the run.

### Design decision

Rather than adding a new event type to `ProcessorService` (which would require production
code changes), the verification approach is:

1. **Test that `_on_tqdm_progress` schedules progress events correctly** — unit test the
   method directly by setting `service._loop` to a real running event loop (or using
   `asyncio.new_event_loop`) and `service.progress_callback` to an `AsyncMock`, then
   calling `_on_tqdm_progress(50, 100, 50.0)` and asserting that the callback was
   eventually called with `{"type": "progress", ...}`.

2. **Test that `ProgressCapture` emits progress on tqdm-pattern matches** — unit test
   `ProgressCapture` directly with a mock callback, write a tqdm-formatted string to it,
   and assert the callback fires with correct current/total/percentage values.

3. **Document the stdout-flush gap**: Add a clear assertion in the test that the
   `"✓ Write #N"` stdout print does NOT trigger a WebSocket event (only tqdm lines do),
   and document this as expected behavior. This makes the gap visible and intentional
   rather than invisible.

These are pure unit tests — no production code changes.

---

## Test File Strategy

### `tests/test_config_loader.py` — add two new classes

Add at the bottom of the existing file (after `TestPriorityOrder`):

- `TestWriteBufferBatchesYamlParsing` — 3 test methods
- `TestWriteBufferBatchesEnvOverride` — 2 test methods

Pattern follows `TestEnvOverrides` for env cleanup and `TestConfigLoader` for temp file
creation/cleanup.

### `tests/test_price_update_progress.py` — add two new classes

Add after existing classes:

- `TestProgressCaptureCallback` — 3 test methods testing `ProgressCapture` directly:
  - `test_tqdm_pattern_match_fires_callback`
  - `test_non_tqdm_text_does_not_fire_callback`
  - `test_flush_write_notification_does_not_fire_callback`

- `TestProcessorServiceProgressEvents` — 2 test methods testing `_on_tqdm_progress`:
  - `test_on_tqdm_progress_schedules_async_event`
  - `test_on_tqdm_progress_skipped_when_cancelled`

All new tests use `scope="function"` fixtures (or class-level `setUp`/`tearDown`) per
project conventions.

---

## What NOT to change

- `deckdex/config.py` — validation already correct
- `deckdex/magic_card_processor.py` — buffer logic already correct
- `backend/api/services/processor_service.py` — existing behavior is already correct;
  per-flush WebSocket events are delivered as tqdm progress events, not a separate
  `flush` event type
- No migrations, no frontend changes, no API contract changes

---

## Risk: Test Isolation

`TestEnvOverrides` in `test_config_loader.py` uses `setUp` to copy `os.environ` and
`tearDown` to restore it. Any new env-based tests MUST use the same pattern. Failing to
restore the environment would contaminate other tests (especially any that read
`DECKDEX_PROCESSING_*` vars).

## Risk: tqdm behavior in tests

`ProgressCapture` tests must use `@patch.dict(os.environ, {"TQDM_DISABLE": "1"})` or
write directly to the capture (bypassing tqdm entirely). Existing tests in
`test_price_update_progress.py` already demonstrate the correct approach: set
`TQDM_DISABLE=1` on tests that run `update_prices_data`.
