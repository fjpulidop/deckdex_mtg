# Web API Backend (Delta)

Data served from Postgres; new auth, import, and CRUD endpoints. Existing endpoints retained with data source change.

## MODIFIED Requirements

### Requirement: Collection and card data SHALL be served from Postgres

**Previous:** GET /api/cards (list; optional limit, offset, search); GET /api/cards/{card_name} (single). Parse prices: EU/US formats; skip invalid/N/A. Reuse SpreadsheetClient. 503 Sheets quota.

**Updated:** FastAPI; collection data SHALL be read from the collection repository (PostgreSQL), not from SpreadsheetClient or Google Sheets. GET /api/health (200 + service/version); CORS for localhost:5173. GET /api/cards (list; optional limit, offset, search) — data from Postgres; same query semantics. GET /api/cards/{id} (single by surrogate id) SHALL be supported; GET /api/cards/{card_name} MAY be retained for backward compatibility. Parse/format prices: EU/US formats; skip invalid/N/A. GET /api/stats (total_cards, total_value, average_price, last_updated) — computed from Postgres; caching (e.g. 30s) optional. POST /api/process — body: { limit?, scope?: "all" | "new_only" }; scope=new_only processes only cards with name but no type_line; returns job_id, background run; 409 if another full process job is already running. POST /api/prices/update → job_id; 409 if another update_prices job is already running (full process and update_prices may run in parallel). GET /api/jobs, GET /api/jobs/{id}; POST /api/jobs/{id}/cancel. GET /api/settings/scryfall-credentials — returns { configured: boolean }; PUT /api/settings/scryfall-credentials — body: { credentials: object | null }, stores JSON internally. Errors: 400 invalid params, 404 not found, 500 + log traceback. For quota limits, 503 SHALL be used only when applicable (e.g. external API quota during import), not for normal Postgres reads. Log requests (endpoint, method, status) at INFO; errors at ERROR.

#### Scenario: List cards from Postgres
- **WHEN** the client calls GET /api/cards
- **THEN** the backend SHALL query the collection repository (Postgres) and SHALL return the list with optional limit, offset, search

#### Scenario: Stats from Postgres
- **WHEN** the client calls GET /api/stats
- **THEN** the backend SHALL compute stats from the Postgres collection and SHALL return total_cards, total_value, average_price, last_updated

## ADDED Requirements

### Requirement: Auth endpoints SHALL support Google OAuth

The backend SHALL provide: GET /api/auth/google — redirects the user to Google's OAuth authorization URL. GET /api/auth/callback — accepts query parameters code and state from Google, exchanges code for tokens, stores refresh token (e.g. in session/DB), redirects browser to frontend (e.g. /settings). GET /api/auth/status — returns whether the current session has Google connected (e.g. { connected: boolean, email?: string }). POST /api/auth/logout — invalidates the session / disconnects Google for the current session.

#### Scenario: OAuth initiate redirect
- **WHEN** the client navigates to GET /api/auth/google
- **THEN** the backend SHALL respond with a redirect (302) to Google's authorization URL with correct client_id, redirect_uri, scope, and state

#### Scenario: OAuth callback stores token and redirects
- **WHEN** Google redirects to GET /api/auth/callback?code=...&state=...
- **THEN** the backend SHALL exchange the code for tokens, SHALL store the refresh token, and SHALL redirect the browser to the frontend Settings page

### Requirement: Import endpoints SHALL support Sheets and local file

The backend SHALL provide: GET /api/google/sheets — returns the list of spreadsheets (and worksheets) for the connected user (requires valid session with Google tokens). POST /api/import/sheets — body: { spreadsheet_id, worksheet_id or range }; reads the sheet via Sheets API, maps rows to cards, replaces collection in Postgres; returns import result (e.g. { imported: number }). POST /api/import/file or POST /api/import/upload — accepts CSV or JSON file (or body); parses and maps to cards, replaces collection in Postgres; returns import result or validation error.

#### Scenario: List sheets when connected
- **WHEN** the client calls GET /api/google/sheets with a session that has valid Google tokens
- **THEN** the backend SHALL call the Google Sheets/Drive API and SHALL return the list of spreadsheets (id, title, and optionally worksheets)

#### Scenario: Import from Sheets
- **WHEN** the client calls POST /api/import/sheets with a valid spreadsheet_id (and optional worksheet)
- **THEN** the backend SHALL read the sheet, map to cards, replace the collection in Postgres, and SHALL return the number of cards imported

#### Scenario: Import from file
- **WHEN** the client uploads a CSV or JSON file to the import endpoint
- **THEN** the backend SHALL parse the file, map to cards, replace the collection in Postgres, and SHALL return the result or a validation error

### Requirement: Card CRUD endpoints SHALL be provided

The backend SHALL provide: POST /api/cards — body: card payload; creates a card in Postgres; returns the created card with id (201 or 200). GET /api/cards/{id} — returns the card with the given surrogate id or 404. PUT or PATCH /api/cards/{id} — body: fields to update; updates the card in Postgres; returns the updated card or 404. DELETE /api/cards/{id} — deletes the card; returns 204 or 200 on success, 404 if not found.

#### Scenario: Create card
- **WHEN** the client sends POST /api/cards with valid card data
- **THEN** the backend SHALL insert the card in Postgres and SHALL return the card including its id

#### Scenario: Update card by id
- **WHEN** the client sends PUT or PATCH /api/cards/{id} with valid data
- **THEN** the backend SHALL update the card in Postgres and SHALL return the updated card, or 404 if id not found

#### Scenario: Delete card by id
- **WHEN** the client sends DELETE /api/cards/{id}
- **THEN** the backend SHALL delete the card from Postgres and SHALL return success, or 404 if id not found

### Requirement: Process job SHALL support scope (all vs new/incomplete only)

POST /api/process SHALL accept a body with optional limit and optional scope. When scope is "new_only", the backend SHALL process only cards that have a name but no type_line (new or incomplete cards). When scope is "all" or omitted, the backend SHALL process all cards. 409 Conflict SHALL be returned only when a job of the same type (full process or update_prices) is already running; one full process and one update_prices job MAY run in parallel.

### Requirement: Settings endpoints SHALL support Scryfall credentials storage

The backend SHALL provide GET /api/settings/scryfall-credentials (returns { configured: boolean }; stored JSON not returned). PUT /api/settings/scryfall-credentials with body { credentials: object | null } SHALL store or clear the credentials JSON internally (e.g. app settings file) so the backend remembers it for the next run. When operations require credentials and none are configured, the system SHALL return a clear message (e.g. "Scryfall credentials not configured"), not a raw file-not-found error.
