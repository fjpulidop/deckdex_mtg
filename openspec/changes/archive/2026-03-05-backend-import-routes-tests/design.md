## Context

`backend/api/routes/import_routes.py` defines 5 endpoints:
1. `POST /api/import/file` — CSV/JSON file upload → DB replace
2. `POST /api/import/preview` — parse file or text, return format + card count (no DB write)
3. `POST /api/import/resolve` — parse + resolve card names vs catalog/Scryfall
4. `POST /api/import/external` — async import job via `ImporterService`
5. `POST /api/import/external/cards` — async import from pre-resolved JSON card list

Each endpoint calls module-level functions (`get_collection_repo`, `get_catalog_repo`, etc.) directly (not as FastAPI Depends), and imports parsers/services inline. This means mocking must happen via `unittest.mock.patch`.

## Goals / Non-Goals

**Goals:**
- 100% endpoint coverage (every route has at least one happy-path test)
- Error path coverage: 400 (bad input), 501 (no Postgres), 413 (file too large)
- All tests run with no DB, no Scryfall, no filesystem access
- Follow `test_decks.py` pattern: pytest functions, module-scoped fixtures, `dependency_overrides`

**Non-Goals:**
- Testing `ImporterService` internals (covered by `test_external_apis_routes.py`)
- Testing background task execution (background tasks are fire-and-forget; we verify they're queued)
- WebSocket progress messages (covered by websocket-specific tests)

## Decisions

### Decision 1: `dependency_overrides` for `get_current_user_id` + `patch` for module-level calls

`get_current_user_id` is a FastAPI `Depends()`, so it can be overridden via `app.dependency_overrides`. But `get_collection_repo()`, `get_catalog_repo()`, etc. are called directly (not as Depends), so they must be patched at their call site in `backend.api.routes.import_routes`.

**Pattern:**
```python
with patch("backend.api.routes.import_routes.get_collection_repo", return_value=mock_repo):
    response = client.post(...)
```

### Decision 2: Module-scoped fixture for the TestClient

Same pattern as `test_decks.py`: one `@pytest.fixture(scope="module")` that yields `client` with `get_current_user_id` overridden. Individual tests use `patch` context managers for the stateful dependencies.

### Decision 3: Disable the slowapi rate limiter in tests

The routes use `@limiter.limit("5/minute")`. In test mode, making more than 5 requests in quick succession will trigger 429s. The cleanest solution is to patch the limiter to be a no-op by replacing `app.state.limiter` with a disabled limiter, or by setting `RATELIMIT_ENABLED=0` env var before app import. Since slowapi respects `app.state.limiter`, we can patch the decorator at the route level by setting `RATELIMIT_ENABLED` environment variable before tests run, or use `slowapi`'s built-in test mode.

Chosen approach: set `RATELIMIT_ENABLED = "0"` in the test module before import, OR patch `backend.api.routes.import_routes.limiter.limit` to return a no-op decorator. The simplest robust approach: override the limiter on `app.state` with a mock in the module fixture.

### Decision 4: Async background tasks — verify queued, not executed

`/api/import/external` and `/api/import/external/cards` schedule background tasks. Tests verify the response (202-ish 200 with `job_id`) and that `ImporterService` was instantiated with correct arguments. They do NOT wait for background task completion.

## Risks / Trade-offs

- **Rate limiter interference**: If slowapi's in-memory storage accumulates across tests, later tests in the same process may get 429. Mitigation: reset or disable the limiter in the module fixture.
- **Inline imports in routes**: Parsers (`detect_format`, `moxfield.parse`, etc.) are imported inside route functions. These must be patched at the deckdex module level. If the import path changes, patches break. Mitigation: use `autospec=False` and verify behavior (return values), not import paths.
