# Proposal

## Why

Grouped Scryfall price lookups were returning 400 and degrading to per-card requests while discarding response diagnostics. The diff adds explicit client headers and failure detail, handles the subsequently reported 429 responses, and corrects numeric SQL operations on prices stored with decimal commas.

## What Changes

- Send DeckDex User-Agent and JSON Accept headers on Scryfall GET and POST requests.
- Surface response details and rule in HTTP errors; skip retries for non-429 4xx responses.
- Pace requests through a process-shared limiter, defer future reservations after 429, and propagate exhausted rate-limit failures without per-card fallback.
- Drop blank collection identifiers and avoid an HTTP request when none remain, retaining the 75-name input limit.
- Normalize comma and dot price text for PostgreSQL price bounds, numeric sorting, and quantity-weighted statistics.

## Capabilities

### New Capabilities

- `scryfall-request-diagnostics`: client identification, HTTP diagnostics, retry policy, request pacing and collection identifier validation.
- `price-numeric-sql`: interpretation of text prices for PostgreSQL filtering, ordering and aggregates, extending the repository behavior described in `openspec/specs/sql-filtering-and-pagination/spec.md`.

### Modified Capabilities

- `price-refresh-efficiency`: narrow the existing Grouped price lookup failure fallback to exclude exhausted rate-limit failures, preserving grouped resolution, request delay and unresolved-name fallback.

## Impact

Core Scryfall fetching, grouped price resolution and PostgreSQL repository queries change. Tests extend `tests/test_price_update_freshness.py` and add `tests/test_price_sql_expression.py`. No new dependencies, API shapes or schema migrations are introduced.

## Non-goals

Resolving the 53 N/A cards, changing freshness or force semantics, changing the 75-identifier chunk size, or establishing production request-count measurements. The diff does not supply a captured live 400 response or a deployment sequencing decision for spec #2.
