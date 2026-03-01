# Catalog System — Delta Spec

## Changed Requirements

### Requirement: Sync progress via WebSocket (UPDATED)

The system SHALL report sync progress via WebSocket using the existing ConnectionManager pattern. The catalog sync route SHALL wire the `on_progress` callback to the WebSocket manager.

#### Scenario: Progress callback wired in route (NEW)

- **WHEN** `POST /api/catalog/sync` is called
- **THEN** the route SHALL create an async progress callback that calls `ConnectionManager.send_progress()`
- **AND** pass it through `catalog_service.start_sync(on_progress=...)` to `CatalogSyncJob`
- **AND** register the job_id in the active jobs tracking so WebSocket connections are accepted

#### Scenario: Progress events include phase

- **WHEN** the sync job emits progress via callback
- **THEN** the WebSocket message SHALL include `phase` ("data" or "images") in addition to current, total, percentage

#### Scenario: Completion event via WebSocket (NEW)

- **WHEN** the catalog sync job completes (success or failure)
- **THEN** the system SHALL send a `complete` event via WebSocket with `status` and `summary`
- **AND** move the job_id from active jobs to job results for cleanup

### Requirement: CatalogRepository tests (NEW)

The system SHALL have unit tests for `CatalogRepository` covering search, autocomplete, upsert, and sync state methods.

#### Scenario: search_by_name tested

- **GIVEN** a CatalogRepository with test data
- **WHEN** `search_by_name("bolt")` is called
- **THEN** the test SHALL verify cards with "bolt" in the name are returned (case-insensitive)

#### Scenario: autocomplete tested

- **GIVEN** a CatalogRepository with test data
- **WHEN** `autocomplete("light")` is called
- **THEN** the test SHALL verify card names starting with "light" are returned

#### Scenario: upsert_cards tested

- **GIVEN** a CatalogRepository
- **WHEN** `upsert_cards([...])` is called with a batch of cards
- **THEN** the test SHALL verify cards are inserted and can be retrieved
- **AND** calling `upsert_cards` again with updated data SHALL update existing rows

### Requirement: Catalog routes integration tests (NEW)

The system SHALL have integration tests for catalog API routes using FastAPI TestClient with mocked dependencies.

#### Scenario: Search endpoint tested

- **WHEN** `GET /api/catalog/search?q=bolt` is called via TestClient
- **THEN** the test SHALL verify 200 response with matching cards

#### Scenario: Sync endpoint tested

- **WHEN** `POST /api/catalog/sync` is called via TestClient
- **THEN** the test SHALL verify 200 response with job_id
- **AND** a second call while running SHALL return 409
