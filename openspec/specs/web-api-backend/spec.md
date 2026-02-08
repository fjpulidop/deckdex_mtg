# Web API Backend

FastAPI; collection data, process execution, job monitoring. **Endpoints:** GET /api/health (200 + service/version); CORS for localhost:5173. GET /api/cards (list; optional limit, offset, search); GET /api/cards/{id}/image (card image by id, on-demand Scryfall fetch and store); GET /api/cards/{card_name} (single). Parse prices: EU/US formats with/without thousands separators; skip invalid/N/A. GET /api/stats (total_cards, total_value, average_price, last_updated); 30s cache. POST /api/process (optional limit) → job_id, background run; POST /api/prices/update → job_id. 409 if process already running. GET /api/jobs, GET /api/jobs/{id} (status, progress, errors, start_time; completed: summary). POST /api/jobs/{id}/cancel → 200 with status cancelled (or 404/409). POST /api/import/file — upload CSV or JSON file to replace collection in Postgres (requires DATABASE_URL); 400 invalid file, 501 if Postgres not configured.

Reuse SpreadsheetClient, CardFetcher, config_loader; wrap processor via ProcessorService. Errors: 400 invalid params, 503 Sheets quota (retry-after), 500 + log traceback. Log requests (endpoint, method, status) at INFO; errors at ERROR.

### Requirement: Backend SHALL provide collection statistics endpoint

The system SHALL calculate and return aggregate statistics about the collection with robust price parsing that handles multiple European and US number formats. GET `/api/stats` SHALL accept optional query parameters that filter the collection before aggregation: `search` (name contains, case-insensitive), `rarity`, `type`, `set_name` (exact match), `price_min`, `price_max` (numeric, inclusive). When any of these parameters are provided, the system SHALL return total_cards, total_value, and average_price for the subset of the collection matching those filters only. When no filter parameters are provided, the system SHALL return aggregates for the entire collection. The stats cache SHALL be keyed by the set of filter parameters so that unfiltered and each distinct filtered request have separate cache entries (e.g. 30s TTL per entry).

#### Scenario: Get collection summary statistics
- **WHEN** client sends GET request to `/api/stats`
- **THEN** system returns JSON with total_cards, total_value, average_price, last_updated timestamp

#### Scenario: Get stats for filtered collection
- **WHEN** client sends GET request to `/api/stats` with one or more of search, rarity, type, set_name, price_min, price_max
- **THEN** system filters the collection by those criteria (same semantics as dashboard: name contains search, exact match for rarity/type/set_name, price in [price_min, price_max]) and returns total_cards, total_value, average_price, last_updated for the filtered subset only

#### Scenario: Statistics cached to avoid excessive Sheets API calls
- **WHEN** client requests stats within 30 seconds of previous request with the same set of filter parameters
- **THEN** system returns cached statistics for that filter combination without recomputing

#### Scenario: Cache key includes filter parameters
- **WHEN** client requests stats with filter params A and later with different filter params B (or no params)
- **THEN** system does not return the cached result from A for request B; each distinct filter combination has its own cache entry

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

### Requirement: Backend SHALL provide collection data endpoints

The system SHALL expose endpoints to retrieve card collection data from Google Sheets with robust price parsing. GET `/api/cards` SHALL accept optional query parameters that filter the collection before pagination, using the same semantics as GET `/api/stats`: `search` (name contains, case-insensitive), `rarity`, `type`, `set_name` (exact match), `price_min`, `price_max` (inclusive). When any of these filter parameters are provided, the system SHALL first filter the collection by those criteria and SHALL then apply `limit` and `offset` to the filtered result, so that the returned list and the statistics for the same filter set refer to the same subset of the collection. When no filter parameters are provided (other than limit/offset/search), behavior SHALL remain as before (list from full collection or search-only subset, then paginated).

#### Scenario: List all cards in collection
- **WHEN** client sends GET request to `/api/cards`
- **THEN** system returns JSON array of cards with name, type, price, rarity, and other metadata

#### Scenario: List cards with pagination
- **WHEN** client sends GET request to `/api/cards?limit=50&offset=100`
- **THEN** system returns 50 cards starting from offset 100

#### Scenario: Search cards by name
- **WHEN** client sends GET request to `/api/cards?search=lotus`
- **THEN** system returns only cards whose name contains "lotus" (case-insensitive)

#### Scenario: List cards filtered by set
- **WHEN** client sends GET request to `/api/cards?set_name=Adventures%20in%20the%20Forgotten%20Realms`
- **THEN** system returns only cards whose set_name equals "Adventures in the Forgotten Realms", and the number of cards returned (subject to limit/offset) SHALL be consistent with GET `/api/stats` with the same set_name (i.e. total count and list refer to the same filtered subset)

#### Scenario: List cards with multiple filters
- **WHEN** client sends GET request to `/api/cards` with two or more of search, rarity, type, set_name, price_min, price_max
- **THEN** system filters the collection by all provided criteria (same semantics as GET `/api/stats`: name contains search, exact match for rarity/type/set_name, price in [price_min, price_max]) and returns the paginated (limit/offset) slice of that filtered result

#### Scenario: Get single card details
- **WHEN** client sends GET request to `/api/cards/{card_name}`
- **THEN** system returns detailed JSON object for that card including all available metadata

#### Scenario: Parse price fields with multiple formats in collection cache
- **WHEN** caching collection data from Google Sheets
- **THEN** system uses same robust price parsing logic for CMC and price fields that handles European/US formats with or without thousands separators

### Requirement: Backend SHALL provide card image endpoint

The system SHALL provide GET `/api/cards/{id}/image` where `id` is the surrogate card id (integer). The endpoint SHALL return the card's image (binary, with appropriate image Content-Type). If the image is not stored, the system SHALL fetch the card by name from Scryfall, download the image, persist it (e.g. to filesystem), and then serve it. The system SHALL return 404 when the card does not exist or the image cannot be obtained.

#### Scenario: GET card image by id returns image when available
- **WHEN** client sends GET request to `/api/cards/{id}/image` and the card exists and has a stored image (or image is successfully fetched and stored)
- **THEN** system responds with status 200 and body containing the image bytes with appropriate Content-Type (e.g. image/jpeg)

#### Scenario: GET card image returns 404 when card not found
- **WHEN** client sends GET request to `/api/cards/{id}/image` and no card exists with that id
- **THEN** system responds with status 404

#### Scenario: Card image route does not conflict with get card by name
- **WHEN** client sends GET request to `/api/cards/123/image`
- **THEN** system treats this as a request for the image of card with id 123, not as a request for a card with name "123" or "123/image"
