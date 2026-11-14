# Tasks

## 1. Scryfall requests

- [x] 1.1 Send explicit User-Agent and Accept headers on GET and POST
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py (test_sends_custom_user_agent_and_accept)
- [x] 1.2 Include Scryfall status and detail in raised errors; do not retry non-429 4xx
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py (test_4xx_is_not_retried_and_reports_scryfall_detail)
- [x] 1.3 Pause all requests on 429 per Retry-After and raise a rate-limit error when persistent
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py (test_429_is_retried, test_429_honors_retry_after_and_pauses_all_requests, test_persistent_429_raises_rate_limit_error)
- [x] 1.4 Pace requests with a shared limiter
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py (test_requests_are_paced)

## 2. Grouped lookup

- [x] 2.1 Log the detailed failure and fall back per name; do not fall back on rate-limit errors
  - Evidence: deckdex/magic_card_processor.py, tests/test_price_update_freshness.py (test_failing_post_falls_back_to_per_name_lookups, test_rate_limit_does_not_fall_back_to_per_card_lookups)

## 3. Numeric price SQL

- [x] 3.1 Add shared numeric price expression and use it in filters, sort and stats
  - Evidence: deckdex/storage/repository.py, tests/test_price_sql_expression.py (test_regex_accepts_comma_and_dot_decimals, test_regex_rejects_junk, test_comma_is_normalized_before_casting, test_price_filters_use_numeric_expression, test_sort_by_price_is_numeric); the stats query has no test
