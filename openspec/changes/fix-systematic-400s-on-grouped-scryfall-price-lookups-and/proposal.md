# Proposal

## Why

During a bulk price refresh every grouped POST to Scryfall `/cards/collection` failed with 400, the code logged a generic warning and fell back to one request per card, and Scryfall's error body was discarded. The code shows the cause was the request shape: default library User-Agent, which Scryfall rejects (rule `generic_user_agent`). While investigating against a real database, the price column was also found to be text with a decimal comma ("0,08"), which broke SQL price filtering, sorting and stats.

## What Changes

- Scryfall GET and POST requests send an explicit `User-Agent` and `Accept: application/json`.
- HTTP errors from Scryfall carry the response status plus Scryfall's `details` (and `rule` when present), so the existing "Grouped price lookup failed" warning shows the cause.
- 4xx responses other than 429 are not retried.
- On 429 the shared rate limiter pauses all requests for `Retry-After` (default and cap constants); after the last attempt a `ScryfallRateLimitError` is raised and the grouped lookup re-raises it instead of falling back to per-card lookups.
- Requests are paced by a class-level rate limiter with separate minimum intervals for GET and POST.
- Repository SQL uses one shared numeric expression for `price_eur` that normalizes the decimal comma and casts only well-formed numbers; price_min/price_max filters, sort by price and aggregate stats use it.

## Capabilities

### New Capabilities
- `scryfall-request-diagnostics`: Scryfall request headers, error detail surfacing, retry and rate-limit behaviour for grouped and per-card lookups.
- `price-numeric-sql`: numeric handling of the text `price_eur` column in filters, sorting and stats.

### Modified Capabilities

None.

## Impact

- `deckdex/card_fetcher.py`, `deckdex/magic_card_processor.py`, `deckdex/storage/repository.py`
- `tests/test_price_update_freshness.py`, `tests/test_price_sql_expression.py`
- Bulk price refresh (POST /api/prices/update) and collection price filters, sort and stats.

## Non-goals

- The 53 cards with `N/A` prices (unresolved names, missing `eur`) are out of scope.
- No change to freshness / skip-if-fresh logic or to the 75-identifier chunk size.
