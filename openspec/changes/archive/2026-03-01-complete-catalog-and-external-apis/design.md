## Context

- The `catalog-system` change landed all core infrastructure: `catalog_cards` table, `CatalogSyncJob`, `CatalogRepository`, `ImageStore`, catalog routes, and catalog service. The sync job accepts an `on_progress` callback but it is never wired to the HTTP/WebSocket layer.
- The `external-apis-settings` change landed per-user settings (table, repository, endpoints, frontend toggle) and catalog-first refactoring across all four Scryfall call points. However, `importer_service.py` has a bug on line 69 where `CardFetcher(config)` is called instead of `CardFetcher(config.scryfall, config.openai)`.
- The WebSocket progress system uses a global `ConnectionManager` (`manager` in `websockets/progress.py`). Routes create an async `progress_callback` that calls `manager.send_progress/error/complete`. The WebSocket endpoint validates jobs against `_active_jobs` and `_job_results` dicts in `process.py`.
- Both features have partial test coverage: parsing logic and mock-based catalog-first tests exist, but no `CatalogRepository` tests or integration tests.

## Goals / Non-Goals

**Goals:**

- Wire WebSocket progress for catalog sync so the Admin UI shows real-time sync progress.
- Fix the `CardFetcher` instantiation bug in the importer so Scryfall fallback works.
- Add unit tests for `CatalogRepository` methods.
- Add integration-style tests for catalog routes and external-apis settings flow.

**Non-Goals:**

- Changing catalog sync logic (phases, batching, retry — all working correctly).
- Changing the external-apis settings UI or API contract.
- Adding new features or endpoints.

## Decisions

1. **WebSocket wiring: async callback bridge from sync thread**
   - **Decision:** In `catalog_routes.py`, create an async `progress_callback` (same pattern as `process.py` lines 155-176) that calls `manager.send_progress` and `manager.send_complete`. Since `CatalogSyncJob` runs in a background thread and calls `on_progress(phase, current, total)` synchronously, `catalog_service.start_sync()` will wrap the async callback using `asyncio.run_coroutine_threadsafe()` to bridge the sync→async boundary.
   - **Rationale:** This is the exact pattern used by `ProcessorService._emit()` — proven to work. The sync job emits `(phase, current, total)` which maps directly to `send_progress(job_id, current, total, percentage, phase=phase)`.

2. **Job registration in _active_jobs for WebSocket validation**
   - **Decision:** Register the catalog sync job_id in the `_active_jobs` dict (from `process.py`) so the WebSocket endpoint accepts connections for it. Use a lightweight sentinel object (not a full `ProcessorService`) since we only need the WebSocket to not reject the connection. Clean up on completion.
   - **Rationale:** The WebSocket endpoint (`websocket_progress`) validates `job_id in _active_jobs or job_id in _job_results`. Without registration, WebSocket connections for catalog sync jobs get rejected with 4004. We need minimal integration with the existing job tracking.

3. **CardFetcher bug fix: pass correct config attributes**
   - **Decision:** Change line 69 of `importer_service.py` from `CardFetcher(config)` to `CardFetcher(config.scryfall, config.openai)`.
   - **Rationale:** `CardFetcher.__init__` signature is `(scryfall_config: ScryfallConfig, openai_config: OpenAIConfig)`. The current code passes the entire `ProcessorConfig` object which crashes at runtime.

4. **CatalogRepository tests: use mock DB via SQLAlchemy in-memory**
   - **Decision:** Test `CatalogRepository` methods using a real SQLite in-memory database with the same schema. This tests actual SQL behavior (ILIKE patterns, UPSERT, ordering) without requiring PostgreSQL.
   - **Rationale:** Unit tests should be runnable without external deps. SQLite supports enough of the SQL surface for these tests. For PostgreSQL-specific features (ILIKE), we'll use `LIKE` with `COLLATE NOCASE` or test the method interface with mocked query results.
   - **Alternative considered:** Mock the entire DB layer — but that wouldn't catch SQL bugs. Use the real CatalogRepository but with mocked `engine.connect()` returns.

5. **Integration tests: FastAPI TestClient with mocked dependencies**
   - **Decision:** Use FastAPI's `TestClient` with overridden dependencies (mock `get_catalog_repo`, `get_user_settings_repo`, etc.) to test route→service→response flow without a real database.
   - **Rationale:** Follows the pattern in existing `tests/test_api.py`. Tests HTTP contracts (status codes, response shapes) and dependency wiring without infrastructure.

## Risks / Trade-offs

- **Risk:** The WebSocket wiring adds `_active_jobs` coupling between `catalog_routes.py` and `process.py`. **Mitigation:** This is the existing pattern — all job types share the same tracking dict. A future refactor could extract job tracking to its own module, but that's out of scope.
- **Risk:** SQLite in-memory tests may miss PostgreSQL-specific behavior (e.g., ILIKE). **Mitigation:** The existing parsing tests cover data integrity. The mock-based tests focus on interface correctness. Full E2E tests against Postgres are out of scope for this change.

## Open Questions

- None. All decisions finalized from the explore session gap analysis.
