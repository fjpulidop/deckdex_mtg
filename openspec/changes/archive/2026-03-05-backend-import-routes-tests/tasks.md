# Tasks: backend-import-routes-tests

## Task 1: Create test file with module fixture
- [x] Create `tests/test_import_routes.py` with a module-scoped `import_client` fixture
  - Override `get_current_user_id` in `app.dependency_overrides`
  - Disable the slowapi rate limiter (mock `app.state.limiter`)
  - Yield `TestClient(app)`
  - Teardown: remove `get_current_user_id` override and restore limiter

## Task 2: Tests for POST /api/import/file
- [x] `test_import_file_csv_success` — upload valid CSV, mock `get_collection_repo` returning mock repo → 200, `imported` key in response
- [x] `test_import_file_json_success` — upload valid JSON array, mock repo → 200
- [x] `test_import_file_no_file_returns_400` — POST without file → 400
- [x] `test_import_file_no_postgres_returns_501` — mock `get_collection_repo` returning None → 501

## Task 3: Tests for POST /api/import/preview
- [x] `test_import_preview_text_success` — POST with MTGO text form field, mock `mtgo.parse` → 200, `detected_format`, `card_count`, `sample`
- [x] `test_import_preview_file_success` — upload file, mock `_parse_file` → 200
- [x] `test_import_preview_no_input_returns_400` — POST with neither file nor text → 400

## Task 4: Tests for POST /api/import/resolve
- [x] `test_import_resolve_text_success` — POST with text, mock `mtgo.parse` and `ResolveService.resolve` → 200, valid `ResolveResponse` shape
- [x] `test_import_resolve_file_success` — upload file, mock parsers and `ResolveService` → 200
- [x] `test_import_resolve_no_input_returns_400` — POST with neither → 400

## Task 5: Tests for POST /api/import/external
- [x] `test_import_external_text_success` — POST with text, mock `get_collection_repo` and `mtgo.parse` → 200, `job_id` in response
- [x] `test_import_external_no_postgres_returns_501` — mock `get_collection_repo` None → 501
- [x] `test_import_external_no_input_returns_400` — POST with neither file nor text → 400

## Task 6: Tests for POST /api/import/external/cards
- [x] `test_import_external_cards_success` — POST JSON with cards list, mock `get_collection_repo` → 200, `job_id` in response
- [x] `test_import_external_cards_no_postgres_returns_501` — mock `get_collection_repo` None → 501
- [x] `test_import_external_cards_empty_list_returns_400` — POST `{"cards": []}` → 400

## Task 7: Verify all tests pass
- [x] Run `pytest tests/test_import_routes.py -v` and confirm all tests pass (21/21)
- [x] Run `pytest tests/ -q` and confirm no regressions (244 passed, 0 failed)
