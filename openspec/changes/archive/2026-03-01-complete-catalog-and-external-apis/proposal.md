## Why

The `catalog-system` and `external-apis-settings` features were implemented in prior changes but left with gaps that prevent them from being fully functional:

1. **Catalog sync has no real-time progress**: The `CatalogSyncJob` has an `on_progress` callback parameter, but `catalog_routes.py` never wires it to the WebSocket `ConnectionManager`. Users who trigger a sync from the Admin UI see no live progress updates.

2. **Import crashes on Scryfall fallback**: `importer_service.py` line 69 instantiates `CardFetcher(config)` but `CardFetcher.__init__` expects `(scryfall_config, openai_config)`. Any import that needs Scryfall fallback (card not in catalog) will crash at runtime.

3. **Missing test coverage**: Both features have incomplete test suites — no `CatalogRepository` unit tests, no catalog route integration tests, and no external-apis integration tests.

## What Changes

- **Fix** the `CardFetcher` instantiation bug in `importer_service.py` (1 line).
- **Wire** WebSocket progress for catalog sync: pass an `on_progress` callback from `catalog_routes.py` through `catalog_service.start_sync()` to `CatalogSyncJob`, using the existing `ConnectionManager` + `_active_jobs` pattern.
- **Register** catalog sync jobs in `_active_jobs` so the WebSocket endpoint accepts connections for catalog sync job IDs.
- **Add** unit tests for `CatalogRepository` (search, autocomplete, upsert, sync_state).
- **Add** integration-style tests for catalog routes and external-apis flow.

## Capabilities

### Modified Capabilities

- `catalog-system`: WebSocket progress now wired for sync jobs. Tests added.
- `external-apis-settings`: CardFetcher bug fixed in importer. Tests added.

## Impact

- **Backend**: Modified `importer_service.py` (bug fix), `catalog_routes.py` (WebSocket wiring), `catalog_service.py` (pass callback + job registration).
- **Tests**: New test files/additions for `CatalogRepository` and integration tests.
- **Frontend**: No changes (Admin UI already listens for WebSocket progress).
- **Database**: No changes.
