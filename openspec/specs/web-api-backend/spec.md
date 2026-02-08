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

### Requirement: Card response SHALL include created_at

The system SHALL include an optional **`created_at`** field in each card object returned by GET `/api/cards` and GET `/api/cards/{id}` (and any other endpoint that returns card data). The value SHALL be an ISO 8601 timestamp string (e.g. from the `cards.created_at` column when using Postgres), or SHALL be omitted if not available (e.g. when the source does not provide it). This allows the frontend to sort and display cards by date added.

#### Scenario: Card list includes created_at when available
- **WHEN** client requests GET `/api/cards` and the collection is stored in Postgres (or another source that provides creation time)
- **THEN** each card object in the response MAY include a `created_at` field with an ISO timestamp string

#### Scenario: Single card response includes created_at when available
- **WHEN** client requests GET `/api/cards/{id}` and the card exists and the store provides creation time
- **THEN** the response MAY include `created_at` with an ISO timestamp string

### Requirement: Card list SHALL be ordered by newest first by default

When the collection is served from a store that supports ordering (e.g. Postgres), GET `/api/cards` SHALL return cards in an order that supports "newest first" as the default UX. For example, the underlying repository SHALL order by `created_at DESC NULLS LAST, id DESC` so that the first page of results contains the most recently added cards. Filtering and pagination SHALL apply to this ordered list so that the same ordering is preserved when filters are applied.

#### Scenario: Unfiltered list returns newest cards first
- **WHEN** client requests GET `/api/cards` without filter parameters (or with only limit/offset)
- **THEN** the returned list is ordered so that the most recently added cards (by created_at) appear first, when the store supports it

#### Scenario: Filtered list preserves newest-first order
- **WHEN** client requests GET `/api/cards` with filter parameters (search, rarity, type, etc.)
- **THEN** the filtered result is ordered so that the most recently added cards in that subset appear first, when the store supports it

### Requirement: Backend SHALL provide card image endpoint

The system SHALL provide GET `/api/cards/{id}/image` where `id` is the surrogate card id (integer). The endpoint SHALL return the card's image (binary, with appropriate image Content-Type). If the image is not stored, the system SHALL fetch the card by name from Scryfall, download the image, persist it (e.g. to database per card-image-storage spec), and then serve it. The system SHALL return 404 when the card does not exist or the image cannot be obtained.

#### Scenario: GET card image by id returns image when available
- **WHEN** client sends GET request to `/api/cards/{id}/image` and the card exists and has a stored image (or image is successfully fetched and stored)
- **THEN** system responds with status 200 and body containing the image bytes with appropriate Content-Type (e.g. image/jpeg)

#### Scenario: GET card image returns 404 when card not found
- **WHEN** client sends GET request to `/api/cards/{id}/image` and no card exists with that id
- **THEN** system responds with status 404

#### Scenario: Card image route does not conflict with get card by name
- **WHEN** client sends GET request to `/api/cards/123/image`
- **THEN** system treats this as a request for the image of card with id 123, not as a request for a card with name "123" or "123/image"

### Requirement: Backend SHALL provide card name suggest endpoint

The system SHALL expose GET `/api/cards/suggest?q=<query>` (or equivalent) that returns a list of card names matching the query from Scryfall's autocomplete API. The endpoint SHALL proxy or call Scryfall and SHALL return a JSON array of name strings (or equivalent) for the client to display in the Add card autocomplete dropdown. The backend SHALL respect Scryfall rate limits (e.g. debouncing or caching is acceptable).

#### Scenario: GET suggest returns names from Scryfall
- **WHEN** client sends GET request to `/api/cards/suggest?q=lotus`
- **THEN** system returns a JSON array of card names (e.g. from Scryfall autocomplete) that match "lotus"

#### Scenario: Suggest handles empty or short query
- **WHEN** client sends GET request to `/api/cards/suggest` with missing or very short q (e.g. length < 2)
- **THEN** system returns an empty array or 400 without calling Scryfall

### Requirement: Backend SHALL provide resolve card by name endpoint

The system SHALL expose an endpoint (e.g. GET `/api/cards/resolve?name=<card_name>`) that, given a card name, returns full card data (type, rarity, set_name, price, and other fields needed for create) from Scryfall. If the name matches a card in the collection, the system MAY return that card's data instead. The response SHALL be suitable for the client to send as the body of POST create (or the backend MAY accept a create-by-name variant). This allows the Add card flow to resolve type, rarity, price, set without the user entering them.

#### Scenario: GET resolve returns full card data for name
- **WHEN** client sends GET request to `/api/cards/resolve?name=Black%20Lotus` (or equivalent)
- **THEN** system returns JSON with at least name, type, rarity, set_name, price (and other fields as per card model) suitable for creating a card

#### Scenario: Resolve returns 404 when card not found
- **WHEN** client sends GET request to resolve with a name that Scryfall (and collection) cannot resolve
- **THEN** system returns 404 (or appropriate error) so the client can show an error or allow manual retry

### Requirement: Backend SHALL provide single-card price update endpoint

The system SHALL provide POST `/api/prices/update/{card_id}` where `card_id` is the surrogate card id (integer). The endpoint SHALL start a background job that updates only that card's price (e.g. from Scryfall) and writes the result to the collection. The response SHALL be JSON with job_id (and optionally status/message) so the client can poll GET `/api/jobs/{job_id}` or use the existing WebSocket progress flow. The job SHALL use the same progress and completion semantics as the bulk price update job (progress events, completion summary, cancellation via POST `/api/jobs/{id}/cancel`). Single-card update jobs MAY run concurrently with each other and with the bulk POST `/api/prices/update` job; the 409 conflict SHALL apply only to concurrent bulk price update requests, not to single-card updates. If the card_id does not exist, the system SHALL return 404.

#### Scenario: POST single-card price update returns job_id
- **WHEN** client sends POST request to `/api/prices/update/{card_id}` with a valid card id
- **THEN** system responds with status 200 and JSON containing job_id (and optionally status/message), and starts a background job that updates that card's price

#### Scenario: Single-card price update job uses same progress and completion as bulk
- **WHEN** a single-card price update job is running
- **THEN** the job reports progress and completion via the same mechanism as the bulk price update (e.g. WebSocket progress, GET /api/jobs/{id} with status and summary when complete)

#### Scenario: Single-card update returns 404 when card not found
- **WHEN** client sends POST request to `/api/prices/update/{card_id}` and no card exists with that id
- **THEN** system responds with status 404 and does not create a job

#### Scenario: Single-card update not blocked by bulk price update
- **WHEN** a bulk price update job is already running (POST `/api/prices/update` returned 200 and job is in progress)
- **THEN** a client MAY successfully start a single-card price update via POST `/api/prices/update/{card_id}` and receive a job_id without receiving 409

### Requirement: Backend SHALL provide analytics aggregation endpoints

The system SHALL expose HTTP endpoints that return aggregated data for the analytics dashboard. Endpoints SHALL accept the same optional filter query parameters as GET `/api/stats`: `search`, `rarity`, `type`, `set_name`, `price_min`, `price_max`. When provided, aggregation SHALL be computed over the filtered subset of the collection only. Responses SHALL be JSON structures suitable for direct use by charts (e.g. lists of { key, count } or { bucket, value }). At least the following aggregations SHALL be available: by rarity, by color identity, by CMC (converted mana cost), and by set (with support for top-N or limit). Implementation SHALL use efficient queries (e.g. SQL GROUP BY) over the backing store (PostgreSQL when configured).

#### Scenario: Get aggregation by rarity
- **WHEN** client sends GET request to the analytics rarity endpoint (e.g. GET `/api/analytics/rarity`) with optional search, rarity, type, set_name, price_min, price_max
- **THEN** system returns JSON array of { rarity, count } (or equivalent) for the filtered collection; counts SHALL match the number of cards in each rarity in that subset

#### Scenario: Get aggregation by color identity
- **WHEN** client sends GET request to the analytics color-identity endpoint (e.g. GET `/api/analytics/color-identity`) with optional filter parameters
- **THEN** system returns JSON array of { color_identity, count } (or equivalent) for the filtered collection; color identity MAY be normalized (e.g. "W", "U", "WU", "C" for colorless) as defined by the API contract

#### Scenario: Get aggregation by CMC
- **WHEN** client sends GET request to the analytics CMC endpoint (e.g. GET `/api/analytics/cmc`) with optional filter parameters
- **THEN** system returns JSON array of { cmc, count } (or bucketed, e.g. "7+") for the filtered collection; CMC SHALL be derived from the card model (numeric or bucketed)

#### Scenario: Get aggregation by set (top N)
- **WHEN** client sends GET request to the analytics set endpoint (e.g. GET `/api/analytics/sets`) with optional filter parameters and optional limit (e.g. top 10)
- **THEN** system returns JSON array of { set_name, count } (or equivalent) ordered by count descending, limited to the requested N, for the filtered collection

#### Scenario: Filter parameters apply to all analytics endpoints
- **WHEN** client sends a request to any analytics aggregation endpoint with one or more of search, rarity, type, set_name, price_min, price_max
- **THEN** system filters the collection using the same semantics as GET `/api/stats` (name contains search, exact match for rarity/type/set_name, price in [price_min, price_max]) and returns aggregates for that subset only

#### Scenario: Analytics summary (KPIs) available
- **WHEN** client needs total card count and total value for the current filter context for the Analytics page
- **THEN** system SHALL provide this via an existing or new endpoint (e.g. GET `/api/stats` with same params, or GET `/api/analytics/summary`) so that KPIs and charts use the same filtered subset
