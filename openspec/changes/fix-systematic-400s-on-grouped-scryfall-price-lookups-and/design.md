# Design

## Context

Grouped lookups to Scryfall `/cards/collection` returned 400 and silently degraded to per-card requests. A shared `REQUEST_HEADERS` (explicit User-Agent and Accept) and a single retry path now serve both GET and POST. All layers touched are in `deckdex/` (core) with tests in `tests/`.

## Goals / Non-Goals

**Goals:**
- Grouped lookups succeed, and failures show Scryfall's status and detail.
- Price SQL handles the decimal-comma text column.

**Non-Goals:**
- Resolving the 53 `N/A` cards (unresolved names or missing `eur`).
- Changing freshness / skip-if-fresh behaviour or the 75-identifier chunk size.

## Decisions

- Error description rebuilds the HTTPError message with Scryfall's `details`/`rule`, falling back to the first 300 characters of the body.
- 4xx other than 429 are not retried; 429 pauses a class-level limiter (`Retry-After`, default and max constants) and raises `ScryfallRateLimitError` on the last attempt.
- The grouped lookup re-raises rate-limit errors so no extra per-card requests are made while Scryfall asks to stop; other failures log a warning and fall back per name.
- `PRICE_NUMERIC_SQL` is one SQL expression reused by filters, sort and stats.

## Blast radius

- `deckdex/card_fetcher.py`: request headers, error description, no retry on non-429 4xx, 429 pause, request pacing.
- `deckdex/magic_card_processor.py`: grouped lookup re-raises rate-limit errors and logs the detailed failure; falls back per name otherwise.
- `deckdex/storage/repository.py`: adds `PRICE_NUMERIC_SQL` and uses it in price filters, sort and stats.
- `tests/test_price_sql_expression.py`: new regression tests for the numeric price expression, filters and sort.
- `tests/test_price_update_freshness.py`: tests for headers, 4xx no-retry with detail, 429 handling, pacing, grouped fallback and rate-limit behaviour.

## Rejected alternatives

None were recorded in the summary or the code.

## Assumptions

- The 400 cause (generic User-Agent) is taken from the code comment citing Scryfall rule `generic_user_agent`; the response body itself was not observed in the available evidence.
- The rate-limit and SQL price changes go beyond the intent text; the summary shows they arose in the same session (a 429 log and broken price filters), so they are described as part of this change.
- No shell was available, so the git diff could not be read; behaviour was derived from the current files and tests, and which lines are new versus pre-existing is inferred.

## Risks / Trade-offs

- A 429 pause of up to the maximum wait blocks all Scryfall requests in the process. Mitigation: the wait is capped.
