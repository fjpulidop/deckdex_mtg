# Proposal: Buffered Price Updates Verification

## What and Why

The buffered price update feature was merged into the `price-updates` spec and the core
implementation exists in `deckdex/magic_card_processor.py`. However, the verification
gap is twofold:

1. **Config parsing end-to-end**: `write_buffer_batches` is defined in `ProcessingConfig`
   and validated on construction, but there are no tests that verify the full YAML loading
   pipeline (`config.yaml` -> `load_yaml_config` -> `apply_env_overrides` ->
   `build_processor_config`) correctly threads `write_buffer_batches` through to the live
   `ProcessorConfig` object. The env-override path (`DECKDEX_PROCESSING_WRITE_BUFFER_BATCHES`)
   is also untested.

2. **Progress emission per flush**: The spec requires "Notify user after each incremental
   write (write number, update counts)." The `ProcessorService` in
   `backend/api/services/processor_service.py` emits progress only from `_on_tqdm_progress`
   (which reads tqdm stderr) and a final `complete` event. There is no `flush` progress
   event emitted after each buffer write. The existing
   `tests/test_price_update_progress.py` already covers `ProcessorService.update_prices_async`
   at the job lifecycle level but does not assert that a per-flush WebSocket event is
   emitted.

This change produces the test artifacts needed to lock down both behaviors so that future
refactoring of config loading or the progress pipeline cannot silently break them.

## Scope

- Unit tests for `write_buffer_batches` config parsing via YAML and env override in the
  `config_loader` pipeline (extends `tests/test_config_loader.py`).
- Unit tests verifying `ProcessorService._on_tqdm_progress` emits intermediate `progress`
  events (not just `complete`) during a price update run.
- Integration-level test confirming that when `update_prices_data` flushes a buffer it
  produces observable side-effects (already partially covered; gaps filled in
  `tests/test_price_update_progress.py`).
- No new production code is required — the implementation is already present. The change
  is entirely test coverage.

## Success Criteria

1. `DECKDEX_PROCESSING_WRITE_BUFFER_BATCHES=5` env var correctly propagates to
   `config.processing.write_buffer_batches == 5` after full `load_config()` pipeline.
2. All three `config.yaml` profiles (`default`, `development`, `production`) yield the
   correct `write_buffer_batches` values (3, 2, 5 respectively) when loaded via
   `load_yaml_config`.
3. `ProcessorService._on_tqdm_progress` schedules an async `progress` event via
   `asyncio.run_coroutine_threadsafe` when a loop and callback are set.
4. `update_prices_data` (Google Sheets path) calls `_write_buffered_prices` at the correct
   interval determined by `write_buffer_batches`.
5. All tests pass with `pytest tests/` from repo root with no external API calls.
