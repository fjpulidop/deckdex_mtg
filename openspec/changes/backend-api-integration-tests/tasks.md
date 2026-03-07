## 1. Insights Route Integration Tests

- [ ] 1.1 Create `tests/test_insights_routes.py` with a `scope="function"` pytest fixture named `insights_client` that overrides `get_current_user_id` via `app.dependency_overrides` and yields a `TestClient`; teardown removes the override
- [ ] 1.2 Add `test_insights_catalog_returns_list`: `GET /api/insights/catalog` returns 200, body is a list, each entry has `id` and `label`, list is non-empty (no mocking needed — route returns `INSIGHTS_CATALOG` constant directly)
- [ ] 1.3 Add `test_execute_insight_success`: patch `backend.api.routes.insights.get_cached_collection` to return `[]` and `backend.api.routes.insights.InsightsService` to return a mock with `execute` returning a valid envelope dict; `POST /api/insights/total_cards` returns 200 with `insight_id`, `question`, `answer_text`, `response_type`, `data` keys
- [ ] 1.4 Add `test_execute_insight_not_found_returns_404`: patch `InsightsService.execute` to raise `ValueError`; `POST /api/insights/bad_id` returns 404
- [ ] 1.5 Add `test_execute_insight_not_implemented_returns_501`: patch `InsightsService.execute` to raise `NotImplementedError`; `POST /api/insights/some_id` returns 501
- [ ] 1.6 Add `test_execute_insight_unexpected_error_returns_500`: patch `InsightsService.execute` to raise `Exception("boom")`; `POST /api/insights/some_id` returns 500
- [ ] 1.7 Add `test_insights_suggestions_success`: patch `backend.api.routes.insights.get_cached_collection` to return `[]` and `backend.api.routes.insights.InsightsSuggestionEngine` so `get_suggestions` returns a list of dicts with `id` and `label`; `GET /api/insights/suggestions` returns 200 with a list where each entry has `id` and `label`
- [ ] 1.8 Add `test_insights_suggestions_error_returns_500`: patch `backend.api.routes.insights.InsightsSuggestionEngine` to raise on instantiation or `get_suggestions`; `GET /api/insights/suggestions` returns 500

## 2. Scryfall Credentials Route Integration Tests

- [ ] 2.1 Create `tests/test_settings_scryfall_credentials_routes.py` with a `scope="function"` pytest fixture named `creds_client` that overrides `get_current_user_id` via `app.dependency_overrides` and yields a `TestClient`; teardown removes the override
- [ ] 2.2 Add `test_get_scryfall_credentials_configured_true`: patch `backend.api.routes.settings_routes.get_scryfall_credentials` to return `{"key": "val"}`; `GET /api/settings/scryfall-credentials` returns 200 with `{"configured": true}`
- [ ] 2.3 Add `test_get_scryfall_credentials_not_configured`: patch `backend.api.routes.settings_routes.get_scryfall_credentials` to return `None`; `GET /api/settings/scryfall-credentials` returns 200 with `{"configured": false}`
- [ ] 2.4 Add `test_put_scryfall_credentials_stores_and_returns_true`: patch both `backend.api.routes.settings_routes.set_scryfall_credentials` (no-op mock) and `backend.api.routes.settings_routes.get_scryfall_credentials` (returns a dict after the call); `PUT /api/settings/scryfall-credentials` with `{"credentials": {"api_key": "abc"}}` returns 200 with `{"configured": true}` and `set_scryfall_credentials` was called once
- [ ] 2.5 Add `test_put_scryfall_credentials_null_clears_and_returns_false`: patch `set_scryfall_credentials` as a no-op and `get_scryfall_credentials` to return `None`; `PUT /api/settings/scryfall-credentials` with `{"credentials": null}` returns 200 with `{"configured": false}` and `set_scryfall_credentials` was called with `None`

## 3. Verification

- [ ] 3.1 Run `pytest tests/test_insights_routes.py -v` and confirm all tests pass with no warnings about fixture scope
- [ ] 3.2 Run `pytest tests/test_settings_scryfall_credentials_routes.py -v` and confirm all tests pass
- [ ] 3.3 Run `pytest tests/ -x` to confirm no regressions in the full suite
