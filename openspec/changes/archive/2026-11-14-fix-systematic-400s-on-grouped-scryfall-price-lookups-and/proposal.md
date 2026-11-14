# Proposal

## Why

Grouped Scryfall price lookups were returning 400 and degrading to per-card requests while discarding the response body. The diff makes the request identify itself with explicit headers and surfaces Scryfall's status and error detail when a request fails. Separately, local API/job tests depended on the developer's PostgreSQL configuration; the working tree isolates them from it.

## What Changes

- Send DeckDex User-Agent and JSON Accept headers on Scryfall GET and POST requests.
- Surface response details and rule (or up to 300 characters of non-JSON body) in HTTP errors; skip retries for non-429 4xx responses.
- Drop blank collection identifiers and avoid an HTTP request when none remain, retaining the 75-name input limit.
- Test isolation only (no production change): health tests in `tests/test_api.py` patch `backend.api.db.get_engine` and cover not-configured, connected and failed-probe cases; job tests in `tests/test_job_persistence.py` mock `get_job_repo`.

## Capabilities

### New Capabilities

- `scryfall-request-diagnostics`: client identification, HTTP error diagnostics, retry policy and collection identifier validation.

### Modified Capabilities

- `price-refresh-efficiency`: the grouped-failure scenario now requires the warning to include Scryfall response detail; per-card fallback is unchanged.

## Impact

Core Scryfall fetching changes (`deckdex/card_fetcher.py`). Grouped price resolution in `deckdex/magic_card_processor.py` is unchanged and picks up the enriched error text. Tests change in `tests/test_price_update_freshness.py`, `tests/test_api.py` and `tests/test_job_persistence.py`. No dependencies, API shapes or schema changes.

## Non-goals

Resolving the 53 N/A cards, changing freshness or force semantics, changing the 75-identifier chunk size, request pacing or rate-limit handling, price SQL changes, changing API behaviour, and measuring production request counts. The diff supplies no captured live 400 response.
