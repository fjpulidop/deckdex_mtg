# Tasks

## 1. Scryfall request handling

- [x] 1.1 Add explicit client and JSON Accept headers to GET and POST; verify header assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::test_sends_custom_user_agent_and_accept (POST headers), test_get_sends_client_headers (GET headers).
- [x] 1.2 Consolidate retries, enrich HTTP failures and skip retries for non-429 4xx; verify retry and 400 assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::test_retries_on_request_exception (two attempts), test_4xx_is_not_retried_and_reports_scryfall_detail (one POST, rule/detail in message), test_non_json_error_includes_only_first_300_body_characters (exact 300-char message).
- [x] 1.3 Omit blank collection names, short-circuit empty filtered input and keep the 75-name limit; verify payload and rejection assertions.
  - Evidence: deckdex/card_fetcher.py, tests/test_price_update_freshness.py::TestCollectionLookup::test_empty_names_are_dropped, test_all_blank_names_send_no_request, test_more_than_75_names_raises.

## 2. Preserve grouped fallback

- [x] 2.1 Verify exhausted 429 retries still fall back for every card and retain response diagnostics in the grouped warning.
  - Evidence: tests/test_price_update_freshness.py::TestGroupedLookup::test_exhausted_429_falls_back_for_every_name_and_logs_detail.

## 3. Test isolation from local database configuration

- [x] 3.1 Isolate health tests by patching `backend.api.db.get_engine`; cover not-configured, connected (`SELECT 1`) and failed-probe (503) cases.
  - Evidence: tests/test_api.py::TestHealth::test_health_returns_200, test_health_probes_configured_database, test_health_reports_database_failure.
- [x] 3.2 Isolate job status DB-fallback and history route tests by mocking `get_job_repo`.
  - Evidence: tests/test_job_persistence.py::TestGetJobStatusDBFallback, TestJobHistoryRouteOrdering::test_history_route_is_reachable and test_history_route_returns_list_without_db.
