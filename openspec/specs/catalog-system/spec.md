# Catalog System

Local card catalog storing all MTG card printings from Scryfall bulk data. Provides offline card lookups and serves as the primary data source for card metadata and images.

## Requirements

### Requirement: catalog_cards table
The system SHALL store all Scryfall card printings in a `catalog_cards` table keyed by `scryfall_id` (Scryfall UUID). This table is global (not user-scoped) and contains full card metadata.

#### Scenario: Catalog contains card metadata
- **WHEN** the catalog has been synced
- **THEN** `catalog_cards` SHALL contain one row per card printing with: scryfall_id (PK), oracle_id, name, type_line, oracle_text, mana_cost, cmc, colors, color_identity, power, toughness, rarity, set_id, set_name, collector_number, release_date, image_uri_small, image_uri_normal, image_uri_large, prices_eur, prices_usd, prices_usd_foil, edhrec_rank, keywords, legalities (JSONB), scryfall_uri, image_status, synced_at, created_at

### Requirement: catalog_sync_state table
The system SHALL maintain a singleton `catalog_sync_state` table tracking sync progress across restarts.

#### Scenario: Sync state tracks progress
- **WHEN** a sync job is running or has completed
- **THEN** `catalog_sync_state` SHALL contain: last_bulk_sync (timestamp), last_image_cursor (scryfall_id), total_cards, total_images_downloaded, status (idle|syncing_data|syncing_images|completed|failed), error_message, updated_at

### Requirement: Bulk data sync from Scryfall
The system SHALL download Scryfall's "Default Cards" bulk data file and UPSERT all cards into `catalog_cards`.

#### Scenario: Full bulk data sync
- **WHEN** an admin triggers a catalog sync
- **THEN** the system SHALL download the bulk JSON from Scryfall's bulk data API
- **AND** parse all card entries and UPSERT into `catalog_cards` by `scryfall_id`
- **AND** update `catalog_sync_state.status` to `syncing_data` during download, then `syncing_images` during image download

#### Scenario: Only one sync at a time
- **WHEN** a sync is already running and another sync is triggered
- **THEN** the system SHALL return HTTP 409

### Requirement: Image download with resume
The system SHALL download card images to filesystem, respecting Scryfall's 100ms rate limit, with cursor-based resumability.

#### Scenario: Image download iterates catalog
- **WHEN** the sync job reaches the image download phase
- **THEN** the system SHALL iterate `catalog_cards` ordered by `scryfall_id`
- **AND** for each card with `image_status = 'pending'`, download the `normal` size image
- **AND** store it via ImageStore with key = `scryfall_id`
- **AND** update `catalog_cards.image_status` to `downloaded`
- **AND** sleep at least 100ms between Scryfall requests

#### Scenario: Resume after interruption
- **WHEN** a sync job restarts after interruption
- **THEN** the system SHALL read `catalog_sync_state.last_image_cursor`
- **AND** resume downloading from the next `scryfall_id` after the cursor
- **AND** skip cards already marked `image_status = 'downloaded'`

#### Scenario: Image download failure
- **WHEN** an individual image download fails after 3 retries
- **THEN** the system SHALL mark that card's `image_status` as `failed`
- **AND** continue to the next card (do not abort the entire sync)

### Requirement: Catalog search
The system SHALL provide local card search via the catalog.

#### Scenario: Search by name
- **WHEN** a client calls `GET /api/catalog/search?q={query}&limit={n}`
- **THEN** the system SHALL return cards from `catalog_cards` whose name contains the query (case-insensitive)
- **AND** limit results to `n` (default 20)

#### Scenario: Autocomplete
- **WHEN** a client calls `GET /api/catalog/autocomplete?q={query}`
- **THEN** the system SHALL return up to 20 card names from `catalog_cards` matching the query prefix (case-insensitive)

#### Scenario: Get by scryfall_id
- **WHEN** a client calls `GET /api/catalog/cards/{scryfall_id}`
- **THEN** the system SHALL return the full card metadata from `catalog_cards`
- **OR** return 404 if not found

### Requirement: Catalog image endpoint
The system SHALL serve catalog card images from filesystem via ImageStore.

#### Scenario: Image available
- **WHEN** an authenticated user calls `GET /api/catalog/cards/{scryfall_id}/image`
- **AND** the image exists in ImageStore
- **THEN** the system SHALL return 200 with image bytes and correct Content-Type

#### Scenario: Image not available
- **WHEN** an authenticated user requests an image that hasn't been downloaded yet
- **THEN** the system SHALL return 404

### Requirement: Sync progress via WebSocket
The system SHALL report sync progress via WebSocket using the existing ConnectionManager pattern. The catalog sync route SHALL wire the `on_progress` callback to the WebSocket manager.

#### Scenario: Progress callback wired in route
- **WHEN** `POST /api/catalog/sync` is called
- **THEN** the route SHALL create an async progress callback that calls `ConnectionManager.send_progress()`
- **AND** pass it through `catalog_service.start_sync(on_progress=...)` to `CatalogSyncJob`
- **AND** register the job_id in the active jobs tracking so WebSocket connections are accepted

#### Scenario: Progress events during sync
- **WHEN** a sync job is running and a client connects to `/ws/progress/{job_id}`
- **THEN** the system SHALL send progress events with: phase (data|images), current, total, percentage

#### Scenario: Completion event
- **WHEN** the sync job completes (success or failure)
- **THEN** the system SHALL send a complete event via WebSocket with `status` and `summary`
- **AND** move the job_id from active jobs to job results for cleanup

### Requirement: Sync API endpoint
The system SHALL expose an endpoint to trigger catalog sync.

#### Scenario: Trigger sync
- **WHEN** a client calls `POST /api/catalog/sync`
- **THEN** the system SHALL start a background sync job
- **AND** return the job_id for WebSocket progress tracking
- **AND** record the job in the `jobs` table with type `catalog_sync`

#### Scenario: Get sync status
- **WHEN** a client calls `GET /api/catalog/sync/status`
- **THEN** the system SHALL return the current `catalog_sync_state` row

### Requirement: CatalogRepository tests
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

### Requirement: Catalog routes integration tests
The system SHALL have integration tests for catalog API routes using FastAPI TestClient with mocked dependencies.

#### Scenario: Search endpoint tested
- **WHEN** `GET /api/catalog/search?q=bolt` is called via TestClient
- **THEN** the test SHALL verify 200 response with matching cards

#### Scenario: Sync endpoint tested
- **WHEN** `POST /api/catalog/sync` is called via TestClient
- **THEN** the test SHALL verify 200 response with job_id
- **AND** a second call while running SHALL return 409
