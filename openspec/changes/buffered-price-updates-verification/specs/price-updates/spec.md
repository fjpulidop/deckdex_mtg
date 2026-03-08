# Delta Spec: Buffered Price Updates Verification

Base spec: [price-updates](../../../specs/price-updates/spec.md)

This delta adds verification requirements only. No behavior changes to production code.

## Testing Requirements

### Config Parsing

The full configuration pipeline MUST be verified for `write_buffer_batches`:

- `load_yaml_config` with the `default` profile MUST yield `write_buffer_batches: 3`.
- `load_yaml_config` with the `development` profile MUST yield `write_buffer_batches: 2`
  while preserving `batch_size` from the default profile (deep-merge verification).
- `load_yaml_config` with the `production` profile MUST yield `write_buffer_batches: 5`.
- `DECKDEX_PROCESSING_WRITE_BUFFER_BATCHES=<N>` environment variable MUST override the
  YAML value to `N` after `apply_env_overrides` + `build_processor_config`.
- `ProcessingConfig(write_buffer_batches=0)` MUST raise `ValueError` with the message
  "write_buffer_batches must be >= 1" (already implemented; must be test-covered).
- `ProcessingConfig(write_buffer_batches=-1)` MUST raise `ValueError`.
- `ProcessingConfig(write_buffer_batches=1)` MUST succeed (boundary value).
- `ProcessingConfig()` default MUST be `write_buffer_batches=3`.

### Progress Event Emission

The `ProgressCapture` class behavior MUST be verified:

- When a tqdm-format string matching `\d+%\|.*?\|\s*\d+/\d+` is written to a
  `ProgressCapture` instance, the callback MUST be called with `(current, total, percentage)`.
- When an arbitrary string (e.g., the `"✓ Write #N"` flush notification) that does NOT
  match the tqdm pattern is written, the callback MUST NOT be called.
- The `flush()` method MUST NOT trigger the progress callback.

The `ProcessorService._on_tqdm_progress` method MUST be verified:

- When `_loop` is set and `progress_callback` is set, calling `_on_tqdm_progress` MUST
  schedule a coroutine via `asyncio.run_coroutine_threadsafe` that eventually calls
  `progress_callback` with a dict containing `{"type": "progress"}`.
- When `_cancel_flag` is set before `_on_tqdm_progress` is called, the method MUST
  return immediately without scheduling a callback.

### Buffered Write Interval (Google Sheets path)

These behaviors MUST be covered by tests (some already exist in
`tests/test_price_update_progress.py` — listed here as the canonical contract):

- With `write_buffer_batches=2` and 6 cards at `batch_size=2` (3 total batches),
  `_write_buffered_prices` MUST be called at least twice.
- With `write_buffer_batches=3` and 4 cards at `batch_size=2` (2 total batches, below
  threshold), `_write_buffered_prices` MUST be called exactly once (end-of-loop flush).
- With all prices unchanged, `_write_buffered_prices` MUST NOT be called.
- With `write_buffer_batches=1`, `_write_buffered_prices` MUST be called once per batch
  that contains changes.

## No Changes To

- Spec sections: Config, Execution, Consistency and compatibility — unchanged.
- Production code: `deckdex/config.py`, `deckdex/magic_card_processor.py`,
  `backend/api/services/processor_service.py`.
