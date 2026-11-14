# Proposal

## Why

Bulk "Update prices" on the Postgres path looks up every card one at a time (`_update_prices_batch_repo` calls `_fetch_card_data(name)` per card and sleeps `api_delay` after each). Request count and elapsed time grow linearly with the collection, and the job re-checks every card on every run even when it was refreshed minutes ago. Nothing records when a card's price was last checked.

## What Changes

- Add nullable `cards.price_last_checked_at TIMESTAMPTZ` (migration `016_card_price_last_checked_at.sql`; `015` is already taken by `015_card_filter_indexes.sql`).
- Add `processing.price_freshness_window_seconds` (int >= 0, 0 = always refresh).
- Bulk refresh skips fresh cards (NULL = stale) unless `force` is set.
- Prices for stale cards are resolved with Scryfall `POST /cards/collection` (up to 75 names per request), falling back to the existing per-card lookup only for names the grouped call could not resolve. `api_delay` is applied between requests, not between cards.
- Looked-up cards are stamped with `price_last_checked_at` in one bulk statement per chunk, together with their changed prices. History still gets one `price_history` row per changed numeric price.
- `POST /api/prices/update` accepts an optional body `{ "force": bool }`; response shape unchanged. The completion summary gains `cards_checked`, `skipped_fresh`, `prices_changed`, `requests_made`, `elapsed_seconds`.

## Capabilities

### New Capabilities
- `price-refresh-efficiency`: stale-card selection, grouped price lookup, last-checked tracking, force flag and refresh summary counters for the bulk price refresh job.

### Modified Capabilities

None. `openspec/specs/price-updates/spec.md` has no Purpose or Requirements sections, so it is not targeted.

## Impact

- Code: `deckdex/magic_card_processor.py`, `deckdex/card_fetcher.py`, `deckdex/storage/repository.py`, `deckdex/config.py`, `backend/api/services/processor_service.py`, `backend/api/routes/process.py`, `migrations/016_card_price_last_checked_at.sql`, `config.yaml`.
- Tests: new `tests/test_price_update_freshness.py`; `tests/test_price_update_progress.py` and `tests/test_process_routes.py` must keep passing unchanged.
- Coexists with open changes `price-update-progress-resume` and `buffered-price-updates-verification` (both test/spec-only, no production edits); this change is additive to the same processor methods.
- No new dependency.

## Non-goals

- No scheduled or automatic refresh, no change of price source or currency (EUR only).
- No resume-from-interruption for the web API.
- No frontend change (no "force" control in the UI, no price chart change).
- No change to the Google Sheets price path or to the `price_history` schema.
