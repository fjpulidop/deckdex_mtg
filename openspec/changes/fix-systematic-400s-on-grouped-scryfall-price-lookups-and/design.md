# Design

## Context

See proposal.md for motivation. The existing core fetcher used separate GET and POST retry loops; grouped price resolution already provided 75-name chunks and per-name fallback. PostgreSQL stores price_eur as text, including comma-decimal output from refresh. Changes stay in the core layer and its storage adapter, with no backend or frontend imports added.

## Goals / Non-Goals

Goals are to reuse the fetcher's request path for identification, diagnostics and retry scheduling, preserve ordinary grouped fallback, and consistently interpret persisted prices in repository queries. Existing repository SQL construction and existing mock-based unittest patterns are retained.

## Non-Goals

- Resolve the 53 N/A prices, translate names or choose alternative printings.
- Change freshness selection, force behavior, price history writes or grouped chunk size.
- Migrate price storage to a numeric column, change API response shapes, or establish cross-process request coordination.
- Prove the live 400 cause or production request counts from mocked tests.

## Decisions

- GET and POST delegate to `_send_with_retry` and send shared DeckDex User-Agent and JSON Accept headers. The code comment attributes 400 to `generic_user_agent`; the observed change is explicit identification, not proof of the production cause.
- HTTP errors retain the requests error text and response object, adding JSON details and rule when available. Failed JSON extraction uses at most 300 response-text characters. Existing grouped warnings naturally include the enriched message.
- Non-429 4xx errors return immediately; other request failures retain configured attempts and exponential delay. Non-final 429 uses numeric Retry-After clamped to 0–120 seconds, defaulting to 60, and advances the shared schedule. Final 429 raises `ScryfallRateLimitError`.
- A class-level limiter reserves request times under a lock using monotonic time, sleeping outside the lock. GET reservations use 0.1-second intervals and POST uses 0.5 seconds. A cooldown adjusts subsequent reservations; already sleeping reservations are not rechecked.
- Grouped resolution rethrows the rate-limit exception before the existing generic catch and fallback. Other failures still log and fall back, and unresolved response names still receive individual lookups. The delta updates the existing Grouped price lookup requirement accordingly.
- Collection input length is checked before empty-name filtering. Remaining names are unchanged; all-blank input produces no POST.
- `PRICE_NUMERIC_SQL` normalizes comma to dot and validates unsigned integer/decimal text before casting. Filters, price ordering and stats reuse it. Ordering retains NULLS LAST and ID tie-breaking; aggregate weighting and rounding remain as before.

## Blast radius

- `deckdex/card_fetcher.py`: adds request identification, shared pacing and retry handling, enriched HTTP errors, rate-limit exception and blank-name filtering.
- `deckdex/magic_card_processor.py`: imports and rethrows exhausted rate-limit failures before ordinary grouped fallback.
- `deckdex/storage/repository.py`: adds a shared numeric price expression used in bounds, ordering and statistics.
- `tests/test_price_sql_expression.py`: adds regression checks for normalized price syntax, bound parameters and generated numeric ordering SQL.
- `tests/test_price_update_freshness.py`: isolates limiter state and sleeping, adds header, HTTP retry/detail, 429, pacing and blank-name tests, and verifies rate-limit failures bypass fallback.

## Rejected alternatives

Continuing per-card fallback after exhausted 429 was explicitly rejected in the processor comment because it would add requests while Scryfall asks callers to stop. No other considered alternatives are recorded.

## Assumptions

- The non-obvious causal attribution of the original 400 to a generic User-Agent is supported only by the code comment and a mocked `generic_user_agent` response. It is treated as the implementation's rationale, not a captured production diagnosis.
- The conversation's broad promise that failed chunks always fall back is qualified by the actual diff: exhausted 429 propagates without fallback. Likewise, “pause all requests” means advancing future shared reservations, not interrupting requests or sleepers already scheduled.
- The price SQL correction extends the initial ticket focus; the summary records the operator's report of broken price calculation and filters, and the diff provides the implemented scope. Spec #2 delivery ordering and a live 400 body remain unestablished.

## Risks / Trade-offs

- Shared cooldown cannot retract already reserved or in-flight requests → the artifact contract describes future reservations only; no stronger concurrency guarantee is claimed.
- Added request pacing and cooldown increase refresh latency → intervals and numeric waits are bounded by constants.
- Test coverage is primarily mocks and SQL-string assertions → live Scryfall diagnosis, concurrent scheduling, GET-specific assertions, response-text fallback, wait bounds, all-blank input, and database aggregate execution are not directly established by the touched tests.

## Migration Plan

No schema or data migration is present. The change updates core runtime code and SQL expressions while retaining text price storage; reverting those changes restores the prior behavior. Runtime deployment and rollback execution belong to the host workflow.
