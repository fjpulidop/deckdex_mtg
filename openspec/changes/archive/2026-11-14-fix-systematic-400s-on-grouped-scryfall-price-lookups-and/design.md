# Design

## Context

See proposal.md for motivation. The core fetcher had separate GET and POST retry loops; grouped price resolution already provided 75-name chunks and per-name fallback and logs the exception text on a grouped failure. The production change stays in the core layer with no backend or frontend imports.

## Goals / Non-Goals

**Goals:** identify the client on every Scryfall request, preserve Scryfall's error detail in raised errors (so the existing grouped warning shows it), avoid retrying non-429 4xx responses, avoid posting blank names, and make the API health and job tests independent of local database configuration.

**Non-Goals:** see the `## Non-Goals` section below.

## Non-Goals

- Resolve the 53 N/A prices, translate names or choose alternative printings.
- Change freshness selection, force behavior, price history writes or grouped chunk size.
- Add request pacing, cooldowns or special 429 handling; 429 keeps the ordinary retry path.
- Change the grouped per-card fallback in `deckdex/magic_card_processor.py`.
- Change price SQL, repository code or API behaviour.
- Prove the live 400 cause or production request counts from mocked tests.

## Decisions

- GET and POST delegate to one `_send_with_retry` and send shared `REQUEST_HEADERS` (DeckDex User-Agent, JSON Accept). A code comment attributes the 400 to `generic_user_agent`; the observed change is explicit identification, not a captured diagnosis.
- On a propagated HTTP error with a response, `_describe_http_error` appends JSON `details` (prefixed by `[rule]`) or, if reading JSON fails, up to 300 characters of response text; the response object is kept on the raised `HTTPError`.
- `_is_retryable` treats 4xx other than 429 as final; other failures keep the configured attempts with exponential delay.
- `get_cards_collection` checks the 75-name limit before filtering blank names and returns empty results without a request when none remain.
- Test isolation: `TestHealth` patches `backend.api.db.get_engine` per test; job-persistence route tests patch `get_job_repo` with a mock or `None`.

## Blast radius

- `deckdex/card_fetcher.py`: adds request headers, consolidated retry with enriched HTTP errors, non-429 4xx no-retry and blank-name filtering.
- `tests/test_price_update_freshness.py`: adds header (POST and GET), 4xx detail/no-retry, non-JSON truncation, blank-name and all-blank tests for the collection lookup, plus exhausted-429 fallback and warning assertions.
- `tests/test_api.py`: health tests isolated from local database configuration by patching `get_engine`; adds connected (`SELECT 1`) and failed-probe (503 degraded) coverage.
- `tests/test_job_persistence.py`: job status DB-fallback and history route tests isolated by mocking `get_job_repo`, so they no longer need PostgreSQL.

## Rejected alternatives

None recorded for the Scryfall fix beyond earlier pacing, 429 cooldown, rate-limit fallback bypass and numeric price SQL work, which was removed in a correction round and is not part of this change. Skipping the database-dependent tests was rejected in the conversation in favour of isolating them.

## Assumptions

- The attribution of the 400 to a generic User-Agent rests on a code comment and a mocked `generic_user_agent` response; no live body was captured.
- The per-line diff of `tests/test_api.py` and `tests/test_job_persistence.py` could not be read with git in this session; their description comes from the current file contents and the conversation decisions (isolation only, no production change).

## Risks / Trade-offs

- 429 responses are retried with the ordinary exponential delay and no pacing, so rate-limit exposure is unchanged.
- Coverage is mock-based; live Scryfall behaviour is not established by the tests.

## Migration Plan

No schema or data migration. Reverting `deckdex/card_fetcher.py` restores prior Scryfall behaviour.
