# Price Updates (Delta)

Delta spec for change `price-update-progress-resume`. Amends `openspec/specs/price-updates/spec.md`.

## Clarification: Storage-Path Asymmetry for Buffered Writes

The buffered-write and progress-notification behavior described in the base spec applies **only to the Google Sheets path** (`update_prices_data` in `deckdex/magic_card_processor.py`).

The Postgres path (`update_prices_data_repo`) writes each price change immediately to the database as each batch future completes. It does NOT accumulate a buffer and does NOT emit intermediate progress notifications between batch flushes. This is by design: Postgres provides transactional durability per write, making large-buffer strategies unnecessary for data-loss reduction.

### Google Sheets Path (existing behavior, now explicitly documented)

- Accumulates changes in `pending_changes` buffer.
- Every `write_buffer_batches` batches: calls `_write_buffered_prices`, prints write progress to stdout (intercepted by `ProgressCapture` for WebSocket delivery when run via API), then sleeps 1.5s.
- After the loop: flushes remaining buffer.
- `write_buffer_batches` is read from `config.processing.write_buffer_batches` (not the deprecated `config.write_buffer_batches` property).

### Postgres Path (clarified scope)

- Writes each changed card to `collection_repository` immediately per batch result.
- No intermediate progress notifications between batches (only the tqdm bar progresses).
- `write_buffer_batches` is NOT applied; this config field is Sheets-specific.
- Data-loss window is one batch (at most `config.processing.batch_size` cards), not one buffer.

## Test Requirements

The following behaviors MUST be covered by automated tests in `tests/test_price_update_progress.py`:

1. Buffered flush fires at correct batch interval (`write_buffer_batches`) — Google Sheets path.
2. Remainder buffer is flushed after loop end — Google Sheets path.
3. No write occurs when no price changes are detected — both paths.
4. `config.processing.write_buffer_batches < 1` raises `ValueError` at `ProcessingConfig` construction time.
5. Resume-from scenario: passing a sublist of cards (simulating post-interruption resume) results in exactly that sublist being fetched from Scryfall — Postgres path.
6. No duplicate DB writes when card prices are already current — Postgres path.
7. `record_price_history` is called only for numerically parseable prices — Postgres path.
8. `ProcessorService.update_prices_async` emits a `complete` event via `progress_callback` on successful completion.
