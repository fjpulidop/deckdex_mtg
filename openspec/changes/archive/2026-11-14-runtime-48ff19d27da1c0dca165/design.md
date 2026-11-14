# Design

## Context

See proposal.md for motivation. Observed current state (Postgres path only):

- `process_card_data()` (`deckdex/magic_card_processor.py`) loads `get_cards_for_price_update()` (3-tuples `(id, name, price_str)`) and calls `update_prices_data_repo(cards)`.
- `update_prices_data_repo` submits `_update_prices_batch_repo` per `batch_size` slice to a `ThreadPoolExecutor`; each card does `_fetch_card_data(name)` (`CardFetcher.search_card`: exact, then fuzzy, then search, so at least one GET per card) and `time.sleep(api_delay)`. The main thread then writes each changed card with `repository.update(...)` + `record_price_history(...)` (one connection and commit per call) and calls `pbar.update`.
- `ProcessorService.update_prices_async` runs `process_card_data()` on a single-thread executor under `ProgressCapture`, which raises `JobCancelledException` on a captured write once the cancel flag is set; it returns `{status, error_count, not_found_cards}`.
- `POST /api/prices/update` has no body, a 5/min limiter and a 409 guard over `_active_jobs`.
- `tests/test_price_update_progress.py` builds the processor with `MagicCardProcessor.__new__` (no `card_fetcher`), a `MagicMock` repository and patches `_fetch_card_data`; it asserts `_fetch_card_data` call lists, `update.assert_not_called()` for unchanged prices and `record_price_history` per changed card.
- Open changes `price-update-progress-resume` and `buffered-price-updates-verification` are test/spec-only (no production edits), so there is no code conflict, only the shared tests which must keep passing.
- Scryfall `POST /cards/collection` takes up to 75 identifiers (`{"name": ...}` is a supported identifier) and returns `data` and `not_found`. This is from Scryfall's public API docs (no network check here). Scryfall asks for 50-100 ms between requests, which `api_delay` (0.1) already models.

## Goals / Non-Goals

**Goals:**
- Fewer requests and less sleep per refresh, skip fresh cards, record last-checked, extend the summary, add `force`.

**Non-Goals:**
- Not changing the Sheets path (`update_prices_data`), `search_card`, `price_history` schema, the single-thread job structure or the UI.
- Not fixing existing quirks (see Out-of-scope findings).

## Decisions

1. **Grouped lookup in `CardFetcher.get_cards_collection(names) -> (found, not_found)`.** One POST per up-to-75 names, reusing the retry/backoff shape of `_make_request` (new private `_post_request`). Rejected: more workers (more requests, rate risk); `cards/search` with OR queries (query-length limit, ambiguous matches).
2. **`MagicCardProcessor._fetch_card_prices_grouped(names) -> dict[name, card_dict|None]`.** Dedupes names, chunks by 75, increments `self.requests_made` per POST, matches results back to requested names case-insensitively on full name or front face of `A // B`, then falls back to `_fetch_card_data(name)` for every unresolved name (each counted as 1 request, a lower bound because `search_card` can issue up to 3 GETs) and for all names of a chunk whose POST raised any exception. `api_delay` is slept once after each POST. The fallback keeps not-found accounting (`error_count`, `not_found_cards`) in the existing `_fetch_card_data` and keeps `tests/test_price_update_progress.py` valid: its processor has no `card_fetcher`, the grouped call raises, and the fallback goes to the patched `_fetch_card_data`.
3. **`_update_prices_batch_repo` keeps its signature and list return** (changed-price tuples) but now takes a slice, calls the grouped helper once and no longer sleeps per card. Deviation from the ticket's `-> dict`: the return is an existing contract used by `update_prices_data_repo`; summary data lives on the processor instead (`self.price_stats`).
4. **Chunking.** `update_prices_data_repo` slices by a module constant `GROUPED_LOOKUP_SIZE = 75` instead of `batch_size` (batch_size is a Sheets-oriented unit and 20 would waste the 75-name capacity). Executor and ordered `future.result()` loop stay; each chunk's results are written before `pbar.update`, so cancellation (raised from the progress write) keeps every chunk already written.
5. **Stale selection.** `_select_stale_cards(cards, last_checked, freshness_window_seconds, force, now) -> (stale, skipped_count)` is a pure function over the 3-tuples plus a `dict[int, datetime|None]` loaded by a new repository method `get_price_last_checked(card_ids)`. Rule: stale if `force`, window 0, value NULL, or `now - value > window` (naive datetimes treated as UTC). Selection runs in `process_card_data` only, so `update_prices_data_repo(cards)` and single-card `update_prices_for_card_ids` keep their behaviour (single-card always looks up, and now also stamps). `get_cards_for_price_update` is untouched. Rejected: 4-tuples (breaks existing callers and tests).
6. **Writes.** New `CollectionRepository.bulk_update_prices(updates: list[PriceUpdate]) -> int` (base class no-op returning 0, like `record_price_history`; Postgres implementation is a single `UPDATE cards SET price_eur = CASE WHEN v.changed THEN v.price ELSE price_eur END, price_last_checked_at = v.checked_at FROM (VALUES ...)` per chunk in one transaction). `PriceUpdate` is a small frozen dataclass `(card_id, price, checked_at, price_changed)` in `deckdex/storage/repository.py`. History stays on the existing `record_price_history` per changed numeric price (exactly one row, unchanged schema, existing tests keep asserting it). Rejected: moving history into the bulk statement (would silently break the three existing history assertions); this leaves history rows as one INSERT per changed card, which is acceptable because only changed prices write.
7. **Failed lookups** (grouped and fallback both gave nothing): not stamped (so the next run retries), counted by existing error accounting; the legacy write of `"N/A"` for them is preserved unchanged via `repository.update`.
8. **Summary.** Processor keeps `self.price_stats` (`cards_checked`, `skipped_fresh`, `prices_changed`, `requests_made`, `elapsed_seconds`) updated per chunk, so a cancelled job still reports partial numbers. `update_prices_data_repo(cards, skipped_fresh=0)` resets and fills it. `ProcessorService.update_prices_async(force=False)` calls `processor.process_card_data(force=force)` and merges `price_stats` (via `getattr(..., {})`, tolerant of the `MagicMock` processors in existing tests) into the success and cancelled results. When `cards_checked == 0` the processor prints a "nothing to update" line.
9. **Endpoint.** Optional `UpdatePricesRequest(force: bool = False)` body (`Optional[...] = None`, so body-less calls still work), passed to `update_prices_async(force=...)`. Validation errors already map to 400. Limiter, 409 guard, response model untouched.
10. **Config.** `ProcessingConfig.price_freshness_window_seconds: int = 21600` with `>= 0` validation in `__post_init__`; flows through `ProcessingConfig(**processing_cfg)` in `config_loader.py` with no loader change. Default 6 h because Scryfall prices refresh about daily; documented in the dataclass docstring and `config.yaml` default profile.

## Local reference patterns

- Batch + executor + ordered write loop: `MagicCardProcessor.update_prices_data_repo` (`deckdex/magic_card_processor.py`).
- Retry/backoff HTTP: `CardFetcher._make_request` (`deckdex/card_fetcher.py`).
- No-op base method plus Postgres override, raw SQL via `text()` and `engine.connect()`: `record_price_history` and `get_cards_for_price_update` in `deckdex/storage/repository.py`.
- Config validation: `ProcessingConfig.__post_init__` (`deckdex/config.py`); tests in `tests/test_config.py` style if present.
- Job result and cancellation: `ProcessorService.update_prices_async` and `ProgressCapture`; tests `TestProcessorServiceUpdatePricesAsync` in `tests/test_price_update_progress.py`.
- Processor test construction: `_make_processor` in `tests/test_price_update_progress.py` (`__new__`, `MagicMock` repo; per project rule use `scope="function"`/per-test objects, no module-scoped mocks). Route tests: `tests/test_process_routes.py` (400, not 422, for validation errors).
- Async/threading: the job body runs synchronously in one worker thread; only `_emit_progress` crosses to the loop, which this change does not touch. No equivalent for a grouped Scryfall call exists today, so `get_cards_collection` is new.

## Risks / Trade-offs

- [Name-based collection lookup misses variants (double-faced, accents)] → fallback to the per-card search for every unresolved name; criterion is "fewer than baseline", not "one per 75".
- [Fallback requests under-counted (`search_card` may issue up to 3 GETs)] → documented lower bound; the baseline is also at least N.
- [Price written but history insert fails] → history errors logged and swallowed per card as today; stamp is already set, so that history point is lost (matches today's non-transactional behaviour).
- [Cancellation raises inside the `with ThreadPoolExecutor` block, which waits for in-flight chunks] → unchanged existing behaviour; at most `max_workers` chunks finish unwritten and stay unstamped.
- [Elapsed-time criterion is not wall-clock-testable without the network] → tests assert sleep calls and requests against a fake source versus the per-card baseline; real timing is measured post-ship.
- [Migration on a large `cards` table] → `ADD COLUMN IF NOT EXISTS ... NULL` with no default is metadata-only on Postgres 11+.

## Migration Plan

`migrations/016_card_price_last_checked_at.sql`: `ALTER TABLE cards ADD COLUMN IF NOT EXISTS price_last_checked_at TIMESTAMPTZ;` (idempotent; applied by the existing `scripts/setup_db.sh` glob). Rollback: drop the column; code treats missing data as NULL only if the column exists, so deploy migration first. Existing rows are NULL, so the first refresh after deploy is a full one.

## Assumptions

- Which freshness window default? Assumed 21600 s (6 h), changeable in config.
- Does the ticket's "force" need a UI control? Assumed no; API and service only (frontend not in the file touch list).
- Should failed lookups be stamped as checked? Assumed no, so they are retried next run.
- Should changed prices and history be one bulk statement? Assumed prices plus stamp in bulk, history through the existing per-card method, to keep existing tests valid.
- Migration number: assumed 016 because 015 is taken.

## Non-Goals

- No scheduled refresh, source/currency change, web resume, chart redesign, Sheets-path change or frontend change.

## Out-of-scope findings (reported, not fixed)

- A failed lookup currently overwrites a stored price with `"N/A"`.
- `openspec/specs/data-model.md` and `price-updates/spec.md` will not list the new column or config until archived or edited by their owners.
- Single-card update and CLI `--update-prices` paths share `update_prices_data_repo` and so also stamp; they have no `force` option.

## Blast radius

| File | Why |
|------|-----|
| `migrations/016_card_price_last_checked_at.sql` (create) | new nullable column |
| `deckdex/config.py` | `price_freshness_window_seconds` + validation |
| `config.yaml` | document the setting in the default profile |
| `deckdex/card_fetcher.py` | `_post_request`, `get_cards_collection` |
| `deckdex/storage/repository.py` | `PriceUpdate`, `bulk_update_prices`, `get_price_last_checked` (base no-ops + Postgres) |
| `deckdex/magic_card_processor.py` | `_select_stale_cards`, `_fetch_card_prices_grouped`, batch/update rewrite, `price_stats`, `force` on `process_card_data` |
| `backend/api/services/processor_service.py` | `force` parameter and summary merge |
| `backend/api/routes/process.py` | optional `UpdatePricesRequest` body |
| `tests/test_price_update_freshness.py` (create) | new tests for all criteria |

No locale, API-doc or other files change; no frontend file changes.
