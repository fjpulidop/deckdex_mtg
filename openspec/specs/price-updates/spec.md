# Price Updates

Update sheet prices from Scryfall; write only changed values. **Incremental (buffered) writes** during verification to reduce data-loss window and improve progress visibility.

## Config

- ProcessorConfig has `write_buffer_batches` (int, default 3). Validation: ≥ 1.

## Execution

- **Incremental writes:** During verification, accumulate (row_index, card_name, new_price); every `write_buffer_batches` batches write to Sheets, then 1.5s delay. After verification, flush remaining buffer.
- **Helper:** `_write_buffered_prices(list of (row_index, card_name, new_price))` → count written; uses existing batch update + retry logic. Price column index cached in _headers_cache.
- **Progress:** Notify user after each incremental write (write number, update counts). Progress bar for verification unchanged.
- **Summary:** Total verified, total updated; hint "To resume from here: --resume-from N".

## Consistency and compatibility

- Retry with backoff on write failure; after max retries log and continue. No duplicate writes (per cell, latest wins).
- **Resume-from,** **dry-run,** existing CLI args unchanged. Default buffer: 3 batches (e.g. 20 cards/batch → write every 60 cards). Max data loss window: one buffer (e.g. 60 cards) instead of full run.
