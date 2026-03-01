## 1. Fix CardFetcher bug in importer_service.py

- [x] 1.1 In `backend/api/services/importer_service.py` line 69, change `CardFetcher(config)` to `CardFetcher(config.scryfall, config.openai)`.

## 2. Wire WebSocket progress for catalog sync

- [x] 2.1 In `backend/api/routes/catalog_routes.py` `trigger_sync()`: import `manager` from `websockets/progress.py` and `_active_jobs`/`_job_results` from `process.py`. Create an async `progress_callback` that bridges sync→async (using `asyncio.run_coroutine_threadsafe`) and calls `manager.send_progress(job_id, current, total, percentage, phase=phase)`.
- [x] 2.2 In `backend/api/routes/catalog_routes.py` `trigger_sync()`: register the job_id in `_active_jobs` with a lightweight sentinel so the WebSocket endpoint accepts connections. Store the job_id in `_job_types` as `'catalog_sync'`.
- [x] 2.3 In `backend/api/services/catalog_service.py` `start_sync()`: ensure the `on_progress` parameter is passed through to `CatalogSyncJob`. In the `_run()` thread wrapper, on completion or failure: emit a WebSocket `complete` event via the callback, move job_id to `_job_results`, and remove from `_active_jobs`.
- [x] 2.4 In `catalog_routes.py` `trigger_sync()`: wrap the sync `on_progress(phase, current, total)` callback to translate it into the async `progress_callback(event)` format expected by the WebSocket manager: `{"type": "progress", "current": current, "total": total, "percentage": pct, "phase": phase}`.

## 3. Unit tests for CatalogRepository

- [x] 3.1 Create `tests/test_catalog_repository.py` with mocked database interactions. Test `search_by_name()`: verify it returns cards matching the query case-insensitively, respects the limit parameter, and returns empty list for no matches.
- [x] 3.2 Test `autocomplete()`: verify prefix matching, limit, and 2-character minimum behavior.
- [x] 3.3 Test `upsert_cards()`: verify batch insert, update on conflict (same scryfall_id), and that `synced_at` is set.
- [x] 3.4 Test `get_sync_state()` and `update_sync_state()`: verify state reads and writes, including status transitions (idle → syncing_data → syncing_images → completed).

## 4. Integration tests for catalog routes

- [x] 4.1 Create `tests/test_catalog_routes.py` using FastAPI TestClient. Override dependencies (`get_catalog_repo`, `get_current_user_id`, `get_image_store`) with mocks.
- [x] 4.2 Test `GET /api/catalog/search?q=bolt`: verify 200 response with list of cards, verify 501 when no Postgres.
- [x] 4.3 Test `GET /api/catalog/autocomplete?q=li`: verify 200 with list of names.
- [x] 4.4 Test `GET /api/catalog/cards/{scryfall_id}`: verify 200 with card data, 404 for unknown ID.
- [x] 4.5 Test `POST /api/catalog/sync`: verify 200 with job_id, verify 409 when already running.

## 5. Integration tests for external-apis settings

- [x] 5.1 Create `tests/test_external_apis_routes.py` using FastAPI TestClient. Override auth and settings repo dependencies.
- [x] 5.2 Test `GET /api/settings/external-apis`: verify 200 with default `{"scryfall_enabled": false}`, verify response after enabling.
- [x] 5.3 Test `PUT /api/settings/external-apis`: verify 200 with updated value, verify 422 for invalid body.
- [x] 5.4 Add regression test for CardFetcher bug: mock `CardFetcher.__init__` and verify it receives `(config.scryfall, config.openai)` when `_run_import()` is called.

## 6. Verify and run tests

- [x] 6.1 Run `pytest tests/test_catalog.py tests/test_catalog_repository.py tests/test_catalog_routes.py tests/test_external_apis_settings.py tests/test_external_apis_routes.py -v` and ensure all tests pass.
