## Change Summary

This change adds test coverage for two under-verified behaviors in the price update system: (1) that incremental buffered-write progress notifications fire correctly between batch flushes, and (2) that a cancelled price update job can be resumed from the interruption point without reprocessing already-updated cards. No production code changes are required — the mechanisms are already implemented; they just lack direct test validation.

## Impact Analysis

### Layers Affected

**Tests (`tests/`)** — Primary target. A new file `tests/test_price_update_progress.py` is created covering:
- `MagicCardProcessor.update_prices_data` (Google Sheets path, `deckdex/magic_card_processor.py` lines 173-273)
- `MagicCardProcessor.update_prices_data_repo` (Postgres path, lines 300-343)
- `MagicCardProcessor._write_buffered_prices` (line 480-513)
- `ProcessingConfig.write_buffer_batches` validation (`deckdex/config.py` line 21-32)

**Specs (`openspec/specs/price-updates/spec.md`)** — Delta spec clarifying the documented asymmetry between Google Sheets and Postgres paths regarding buffered-write progress notifications.

**No changes to:**
- `deckdex/magic_card_processor.py` — logic already complete
- `backend/api/routes/process.py` — no route changes
- `backend/api/services/processor_service.py` — no service changes
- `frontend/` — no frontend changes
- `migrations/` — no schema changes

## Implementation Design

### Discovery: What the Code Actually Does

After reading the source, the current state is:

**Google Sheets path (`update_prices_data`):**
- Uses `ThreadPoolExecutor` to submit batch futures
- Accumulates results in `pending_changes` buffer
- When `batches_processed >= config.processing.write_buffer_batches`, calls `_write_buffered_prices` then prints a progress notification to stdout
- After the loop, flushes any remaining buffer
- Progress notification is a `print()` statement — it goes to stdout, which is intercepted by `ProgressCapture` in `ProcessorService` — this means it IS visible via WebSocket if the processor is run through the API layer
- `_write_buffered_prices` delegates to `_batch_update_prices` which uses exponential backoff retry

**Postgres path (`update_prices_data_repo`):**
- Uses `ThreadPoolExecutor` with the same batch structure
- Writes each changed card immediately to the DB (`collection_repository.update(card_id, {...})`) per batch result — no buffer accumulation
- No intermediate progress notification between batches; no `_write_buffered_prices` call
- `write_buffer_batches` config is NOT respected in this path (immediate write per batch)

This is an undocumented asymmetry. The spec says "Incremental writes... every `write_buffer_batches` batches write to Sheets", implying this is a Sheets-specific feature. The Postgres path is documented separately as "Update prices using the collection repository" but the spec doesn't explicitly state the asymmetry. The delta spec will document this.

**Resume-from in context of the web API:**
- `ProcessorConfig.resume_from` is set via CLI (`--resume-from N`)
- In `process_cards_repo` (line 362-364 of `magic_card_processor.py`), `resume_from` slices the card list: `cards = cards[self.config.resume_from:]`
- In `update_prices_data_repo`, there is NO resume_from slice — the method always processes all cards passed to it
- The "resume" for prices in Postgres means: start a new job and pass only the unprocessed cards (i.e., slice the list from the caller side)
- `process_cards` (Google Sheets, line 607-609) applies `resume_from` relative to `row_index_to_start`
- `update_prices_data` (Google Sheets) does NOT apply `resume_from` — the caller must pass only the unprocessed card sublist

This means resume-from is an external concern (CLI arg or API consumer slices the list). The test will simulate this by verifying that when a partial card list is passed, only those cards are processed and previously-updated cards are not re-fetched.

### Test Design

All tests go in `tests/test_price_update_progress.py`. All fixtures use `scope="function"`. No real HTTP calls.

#### Test Group 1: Buffered Write Progress Notifications (Google Sheets Path)

**Target:** `MagicCardProcessor.update_prices_data`

**Setup:** Mock `_fetch_card_data` to return predetermined prices, mock `_write_buffered_prices` to return a count, mock `tqdm` side effects to avoid terminal output.

**Tests:**

1. `test_buffered_write_fires_after_write_buffer_batches` — Configure `batch_size=2`, `write_buffer_batches=2`. Pass 6 cards with known price changes. Assert `_write_buffered_prices` is called at least once mid-run (not only at the end), specifically when `batches_processed` reaches `write_buffer_batches`. Verify the call count matches expected flush intervals.

2. `test_buffered_write_flushes_remainder_at_end` — Configure `batch_size=2`, `write_buffer_batches=3`. Pass 4 cards (2 batches, less than the buffer threshold). Assert `_write_buffered_prices` is called exactly once at the end (remainder flush), not mid-run.

3. `test_no_write_when_no_price_changes` — All cards return the same price as `current_price`. Assert `_write_buffered_prices` is never called (no changes to write).

4. `test_write_buffer_batches_config_respected` — Use `write_buffer_batches=1` (write after every batch). Pass 4 cards (2 batches). Assert `_write_buffered_prices` is called at least twice.

**Mock strategy for Google Sheets path:**
- `MagicCardProcessor` needs a `spreadsheet_client` to avoid `ClientFactory.create_spreadsheet_client` raising on missing credentials. Inject a `MagicMock()` as `processor.spreadsheet_client` directly after construction. Mock `_fetch_card_data` with `@patch.object`. Mock `_write_buffered_prices` with `@patch.object` to avoid gspread calls.
- Suppress tqdm output by patching `sys.stderr` or by setting `disable=True` — achieved by setting `os.environ["TQDM_DISABLE"] = "1"` or by mocking `tqdm.tqdm`.

**Alternative (simpler) mock strategy:** Construct `MagicCardProcessor.__new__(MagicCardProcessor)` and manually set attributes, bypassing `__init__` and `_initialize_clients`. This avoids needing to mock gspread at the class level.

Use the `__new__` approach (consistent with how `test_job_persistence.py` handles `JobRepository`).

#### Test Group 2: write_buffer_batches Config Validation

**Target:** `ProcessingConfig.__post_init__`

5. `test_write_buffer_batches_zero_raises` — Construct `ProcessingConfig(write_buffer_batches=0)`. Assert `ValueError` is raised with message containing "write_buffer_batches".

6. `test_write_buffer_batches_one_is_valid` — Construct `ProcessingConfig(write_buffer_batches=1)`. Assert no exception.

#### Test Group 3: Resume-from-Interruption (Postgres Path)

**Target:** `MagicCardProcessor.update_prices_data_repo`

The "resume" scenario for the Postgres path: after a partial run (cards 0-N processed), a new job is started with only cards N+1 onwards. The test verifies that `_fetch_card_data` is called exactly for the cards in the resumed list, and NOT for any card in the already-processed list.

**Tests:**

7. `test_resume_from_processes_only_remaining_cards` — Create a list of 6 cards. Simulate "first run interrupted after 4 cards" by calling `update_prices_data_repo` with only the last 2 cards. Assert `_fetch_card_data` is called exactly 2 times. Assert `collection_repository.update` is called at most 2 times (only for changed cards).

8. `test_no_duplicate_writes_when_price_unchanged` — Pass 3 cards where all prices are already current (same as Scryfall). Assert `collection_repository.update` is never called. Assert `collection_repository.record_price_history` is never called.

9. `test_price_history_recorded_for_numeric_prices` — Pass 2 cards with price change from "N/A" to "1,50". Assert `record_price_history` is called with `float(1.5)`.

10. `test_price_history_skipped_for_non_numeric_price` — Pass 1 card where new price is "N/A". Assert `record_price_history` is never called (the `except (ValueError, TypeError): pass` guard).

#### Test Group 4: ProcessorService Progress Callback Integration

**Target:** `ProcessorService.update_prices_async` (verifying callback is wired)

11. `test_update_prices_async_emits_complete_event` — Construct a `ProcessorService` via `__new__`, patch `MagicCardProcessor.process_card_data` to return immediately, set a mock `progress_callback`, run `update_prices_async`. Assert the callback received at least one call with `event["type"] == "complete"`.

12. `test_update_prices_async_emits_progress_events` — Patch `ProgressCapture.write` to invoke the callback, verify that a "progress" event is emitted during the run.

**Note:** Groups 1 and 4 are the most critical for spec compliance. Groups 2 and 3 are supporting validation.

### Mock Construction Pattern

Following the pattern in `test_job_persistence.py`:

```python
def _make_processor(self, batch_size=2, write_buffer_batches=2):
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
    proc.spreadsheet_client = MagicMock()
    proc.collection_repository = MagicMock()
    proc._card_cache = {}
    proc.error_count = 0
    proc.last_error_count = 0
    proc.not_found_cards = []
    proc._headers_cache = ["Name", "Price"]
    return proc
```

For Postgres path tests, `collection_repository` is set to a real `MagicMock()`. For Google Sheets path tests, `collection_repository` is set to `None` and `spreadsheet_client` to a `MagicMock()`.

### Architectural Decisions

**Decision 1: No production code changes.** The buffered write logic in `update_prices_data` is fully implemented. Tests verify behavior without modifying it. Rationale: the spec requires verification, not implementation.

**Decision 2: Document Postgres path asymmetry in spec, not fix it.** Adding buffered writes to `update_prices_data_repo` is a separate feature with different trade-offs (Postgres has transactional guarantees; buffering for write-reduction is less valuable than for Sheets API quota management). Documenting the asymmetry is correct scope.

**Decision 3: Use `__new__` for processor construction in tests.** `MagicCardProcessor.__init__` calls `_initialize_clients` which tries to connect to Google Sheets or Postgres. Bypassing via `__new__` is the cleanest approach without patching `ClientFactory` at the module level.

**Decision 4: `max_workers=1` in all test configs.** The Google Sheets path uses `ThreadPoolExecutor`. Setting `max_workers=1` makes future ordering deterministic and avoids race conditions in test assertions.

## Risks and Considerations

**Risk 1: `tqdm` output to stdout/stderr.** `update_prices_data` and `update_prices_data_repo` both print to stdout. Tests using `__new__` + direct calls will produce tqdm output during test runs. Mitigate by redirecting stdout/stderr in tests (use `contextlib.redirect_stdout`) or by setting `TQDM_DISABLE=1` env var via `unittest.mock.patch.dict(os.environ, {"TQDM_DISABLE": "1"})`.

**Risk 2: Thread safety in progress callback tests (Group 4).** `ProcessorService` uses `asyncio.run_coroutine_threadsafe` to fire callbacks from a thread. In tests, the event loop may not be running. Use `IsolatedAsyncioTestCase` (as in `test_job_persistence.py`) to handle this correctly.

**Risk 3: `_write_buffered_prices` depends on `gspread.utils.rowcol_to_a1`.** When mocking at the `_write_buffered_prices` level, this dependency is bypassed. But if testing `_write_buffered_prices` directly (test group 1), patch `gspread.utils.rowcol_to_a1` or mock `self._batch_update_prices`.

**Risk 4: `futures` ordering is non-deterministic with `max_workers > 1`.** All tests set `max_workers=1` to ensure batch completion order matches submission order, making `batches_processed` counter reliable.

**Edge case: zero price changes.** `_write_buffered_prices` is only called when `pending_changes` is non-empty. If all cards have unchanged prices, no write occurs. Test 3 covers this explicitly.

**Edge case: partial buffer at end.** After the main loop, `pending_changes` may still have items (last partial buffer). The flush-at-end block (`if pending_changes:` at line 252) handles this. Test 2 covers this case.
