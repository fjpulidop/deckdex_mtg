## Why

The price update system has buffered writes implemented in `deckdex/magic_card_processor.py` (the `update_prices_data` method and `_write_buffered_prices` helper), but there is no verification that the in-flight progress notifications sent to WebSocket clients are correct after each buffered write, and no test coverage for the resume-from-interruption scenario. Without these, users who cancel a long-running price update job have no guarantee that the progress state is accurately reported or that they can safely resume without reprocessing already-updated cards.

## What Changes

- Add integration tests verifying that buffered write progress notifications (`write_number`, `update_counts`) are correctly emitted between batch flushes during `update_prices_data` (Google Sheets path).
- Add integration tests verifying that `update_prices_data_repo` (Postgres path) respects `write_buffer_batches` — specifically that the config value is read from `config.processing.write_buffer_batches`, not the deprecated `config.write_buffer_batches` property.
- Add a resume-from-interruption test: simulate a job cancelled mid-run, then rerun from the resume point, verifying cards already updated are not reprocessed (no duplicate Scryfall calls, no duplicate DB writes).
- Add a test verifying that `config.processing.write_buffer_batches` validation (must be >= 1) is enforced when the processor is constructed.

## Capabilities

### New Capabilities
None. This change is test and verification only.

### Modified Capabilities
- `price-updates`: Validate that the progress notification between batches is tested. Clarify that `update_prices_data_repo` (Postgres path) does not currently implement buffered writes with intermediate progress notifications — only the Google Sheets path (`update_prices_data`) does. Document this asymmetry explicitly in the spec.

## Impact

- `tests/`: New test file `tests/test_price_update_progress.py` (unit/integration tests for `MagicCardProcessor` price update methods).
- `deckdex/magic_card_processor.py`: No functional changes. Existing buffered-write logic already implemented. Tests will validate it as-is.
- `openspec/specs/price-updates/spec.md`: Delta spec to clarify the Postgres path asymmetry (no buffered-write progress notifications for `update_prices_data_repo`).

## Non-goals

- This change does not modify any production code in `deckdex/` or `backend/`.
- This change does not add buffered writes to the Postgres price update path (`update_prices_data_repo`).
- This change does not add resume-from-interruption support to the web API (the `POST /api/prices/update` endpoint). Resume-from is a CLI flag only.
- This change does not add WebSocket-level integration tests (those require a running server).
