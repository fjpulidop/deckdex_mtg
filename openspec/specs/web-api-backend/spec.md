## ADDED Requirements

### Requirement: Backend SHALL expose REST API endpoints

The system SHALL provide a FastAPI-based REST API backend that exposes endpoints for accessing collection data, executing processes, and monitoring job status.

#### Scenario: Health check returns service status
- **WHEN** client sends GET request to `/api/health`
- **THEN** system returns 200 OK with service name and version

#### Scenario: CORS enabled for local development
- **WHEN** frontend at localhost:5173 makes API request
- **THEN** system allows the request with appropriate CORS headers

### Requirement: Backend SHALL provide collection data endpoints

The system SHALL expose endpoints to retrieve card collection data from Google Sheets with robust price parsing.

#### Scenario: List all cards in collection
- **WHEN** client sends GET request to `/api/cards`
- **THEN** system returns JSON array of cards with name, type, price, rarity, and other metadata

#### Scenario: List cards with pagination
- **WHEN** client sends GET request to `/api/cards?limit=50&offset=100`
- **THEN** system returns 50 cards starting from offset 100

#### Scenario: Search cards by name
- **WHEN** client sends GET request to `/api/cards?search=lotus`
- **THEN** system returns only cards whose name contains "lotus" (case-insensitive)

#### Scenario: Get single card details
- **WHEN** client sends GET request to `/api/cards/{card_name}`
- **THEN** system returns detailed JSON object for that card including all available metadata

#### Scenario: Parse price fields with multiple formats in collection cache
- **WHEN** caching collection data from Google Sheets
- **THEN** system uses same robust price parsing logic for CMC and price fields that handles European/US formats with or without thousands separators

### Requirement: Backend SHALL provide collection statistics endpoint

The system SHALL calculate and return aggregate statistics about the collection with robust price parsing that handles multiple European and US number formats.

#### Scenario: Get collection summary statistics
- **WHEN** client sends GET request to `/api/stats`
- **THEN** system returns JSON with total_cards, total_value, average_price, last_updated timestamp

#### Scenario: Statistics cached to avoid excessive Sheets API calls
- **WHEN** client requests stats within 30 seconds of previous request
- **THEN** system returns cached statistics without querying Google Sheets

#### Scenario: Parse European price format with thousands separator
- **WHEN** Google Sheets returns price as "1.234,56" (European format with thousands separator)
- **THEN** system correctly parses it as 1234.56 and includes it in total_value calculation

#### Scenario: Parse European price format without thousands separator
- **WHEN** Google Sheets returns price as "123,45" (European format without thousands separator)
- **THEN** system correctly parses it as 123.45 and includes it in total_value calculation

#### Scenario: Parse US price format with thousands separator
- **WHEN** Google Sheets returns price as "1,234.56" (US format with comma thousands separator)
- **THEN** system correctly parses it as 1234.56 and includes it in total_value calculation

#### Scenario: Skip invalid price formats gracefully
- **WHEN** price value cannot be parsed as a number
- **THEN** system logs the error and excludes that card from total_value but continues processing remaining cards

#### Scenario: Skip N/A prices
- **WHEN** card has price value "N/A"
- **THEN** system excludes that card from total_value and average_price calculations

### Requirement: Backend SHALL provide process execution endpoints

The system SHALL allow clients to trigger card processing and price update operations.

#### Scenario: Trigger new card processing
- **WHEN** client sends POST request to `/api/process` with optional limit parameter
- **THEN** system creates a new job, returns job_id, and begins processing in background

#### Scenario: Trigger price update
- **WHEN** client sends POST request to `/api/prices/update`
- **THEN** system creates a new job, returns job_id, and begins price updates in background

#### Scenario: Cannot start process while another is running
- **WHEN** client sends POST to `/api/process` while another process is active
- **THEN** system returns 409 Conflict with message indicating active job_id

### Requirement: Backend SHALL provide job monitoring endpoint

The system SHALL allow clients to query the status of background jobs.

#### Scenario: Get active job status
- **WHEN** client sends GET request to `/api/jobs/{job_id}`
- **THEN** system returns JSON with status, progress, errors, start_time, and job_type

#### Scenario: Query completed job
- **WHEN** client sends GET request to `/api/jobs/{job_id}` for completed job
- **THEN** system returns final summary with total_processed, success_count, error_count, duration

#### Scenario: Query non-existent job
- **WHEN** client sends GET request to `/api/jobs/{invalid_id}`
- **THEN** system returns 404 Not Found

#### Scenario: List all jobs
- **WHEN** client sends GET request to `/api/jobs`
- **THEN** system returns JSON array of all active and recently completed jobs with job_id, status, job_type, progress, and start_time

### Requirement: Backend SHALL provide job cancellation endpoint

The system SHALL allow clients to cancel running background jobs.

#### Scenario: Cancel a running job
- **WHEN** client sends POST request to `/api/jobs/{job_id}/cancel`
- **AND** job exists and is in `running` state
- **THEN** system calls `cancel_async()` on the ProcessorService
- **AND** stores `{'status': 'cancelled'}` in `_job_results`
- **AND** returns `{"job_id": "...", "status": "cancelled", "message": "Job cancellation requested"}`

#### Scenario: Cancel non-existent job
- **WHEN** client sends POST to `/api/jobs/{invalid_id}/cancel`
- **THEN** system returns 404 Not Found

#### Scenario: Cancel already-finished job
- **WHEN** client sends POST to `/api/jobs/{job_id}/cancel` for a job not in `running` state
- **THEN** system returns 409 Conflict with message indicating current status

### Requirement: Backend SHALL reuse existing processor logic

The system SHALL wrap existing `MagicCardProcessor` and `CardFetcher` without modifying their behavior.

#### Scenario: Backend uses SpreadsheetClient to read collection
- **WHEN** backend needs card data
- **THEN** it uses existing `spreadsheet_client.get_cards()` method

#### Scenario: Backend uses CardFetcher for Scryfall queries
- **WHEN** processing cards
- **THEN** it delegates to existing `CardFetcher.search_card()` method

#### Scenario: Backend respects existing configuration
- **WHEN** creating processor instances
- **THEN** it loads config using existing `config_loader.load_config()` with appropriate profile

### Requirement: Backend SHALL handle errors gracefully

The system SHALL return appropriate HTTP status codes and error messages for failures.

#### Scenario: Invalid request parameters
- **WHEN** client sends request with invalid parameters (e.g., negative offset)
- **THEN** system returns 400 Bad Request with validation error details

#### Scenario: Google Sheets API quota exceeded
- **WHEN** Sheets API returns quota error
- **THEN** system returns 503 Service Unavailable with retry-after header

#### Scenario: Card not found in Scryfall
- **WHEN** processing fails to find card
- **THEN** error is tracked in job status but processing continues for remaining cards

### Requirement: Backend SHALL log operations appropriately

The system SHALL use existing loguru logger for backend operations.

#### Scenario: Log API requests at INFO level
- **WHEN** API receives request
- **THEN** system logs endpoint, method, and response status

#### Scenario: Log errors at ERROR level
- **WHEN** unhandled exception occurs
- **THEN** system logs full traceback and returns 500 Internal Server Error to client
