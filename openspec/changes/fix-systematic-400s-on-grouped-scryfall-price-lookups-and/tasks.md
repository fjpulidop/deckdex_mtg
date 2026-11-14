# Tasks

## 1. Scryfall request handling

- [x] 1.1 Add explicit client and JSON Accept headers to GET and POST; verify the POST header regression assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::test_sends_custom_user_agent_and_accept (asserts custom User-Agent and JSON Accept on POST); no direct GET-header test evidence.
- [x] 1.2 Consolidate retries and enrich HTTP failures while bypassing non-429 4xx retries; verify request retry and 400 regression assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::test_retries_on_request_exception (asserts two attempts), test_4xx_is_not_retried_and_reports_scryfall_detail (asserts one POST and propagated rule); response-text fallback and status/detail contents lack dedicated assertions.
- [x] 1.3 Add shared request scheduling and isolated limiter/sleep test setup; verify consecutive POST pacing assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::setUp and test_requests_are_paced (resets limiter and asserts sleeping occurs); exact intervals and concurrent scheduling have no direct test evidence.
- [x] 1.4 Handle non-final 429 through shared cooldown and raise an exhausted rate-limit failure on the last attempt; verify retry, Retry-After and exhausted-budget assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::test_429_is_retried, test_429_honors_retry_after_and_pauses_all_requests, test_persistent_429_raises_rate_limit_error (assert two attempts, pause of 7.0 and dedicated exception); default and clamp branches have no direct test assertions.
- [x] 1.5 Omit blank collection names and short-circuit empty filtered inputs while retaining the input limit; verify mixed-name payload and oversized-input assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::test_empty_names_are_dropped (asserts only A is posted), test_more_than_75_names_raises (asserts rejection); all-blank no-request behavior has no direct test evidence.

## 2. Grouped lookup fallback

- [x] 2.1 Propagate exhausted rate-limit errors before generic grouped fallback; verify no individual lookup occurs for that failure.
  - Evidence: deckdex/magic_card_processor.py, tests/test_price_update_freshness.py::TestRateLimitedGroupedLookup::test_rate_limit_does_not_fall_back_to_per_card_lookups (asserts propagation and no per-card calls); TestGroupedLookup::test_failing_post_falls_back_to_per_name_lookups and test_unresolved_name_falls_back_once assert retained ordinary fallback. The warning text has no direct test assertion.

## 3. Numeric PostgreSQL prices

- [x] 3.1 Define comma-normalized numeric interpretation guarded against malformed prices; verify accepted and rejected formats and normalization assertions.
  - Evidence: deckdex/storage/repository.py, tests/test_price_sql_expression.py::TestPriceNumericExpression::test_regex_accepts_comma_and_dot_decimals, test_regex_rejects_junk, test_comma_is_normalized_before_casting (assert normalized formats match, junk fails and REPLACE is present); tests do not execute PostgreSQL casts.
- [x] 3.2 Apply the shared expression to price bounds and ordering; verify bound parameters and generated ordering SQL.
  - Evidence: deckdex/storage/repository.py, tests/test_price_sql_expression.py::TestPriceFilters::test_price_filters_use_numeric_expression, test_sort_by_price_is_numeric (assert expression reuse, 1.5/10.0 bound values and descending numeric ordering SQL).
- [x] 3.3 Reuse the shared numeric expression in existing quantity-weighted statistics; verify the stats query references the expression by source inspection.
  - Evidence: deckdex/storage/repository.py::PostgresCollectionRepository.get_cards_stats; no automated test evidence for aggregate numeric results in the touched tests.
