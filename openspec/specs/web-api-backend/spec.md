# Web API Backend

FastAPI; collection data, process execution, job monitoring. **Endpoints:** GET /api/health (200 + service/version); CORS for localhost:5173. GET /api/cards (list; optional limit, offset, search, rarity, type, set_name, price_min, price_max); GET /api/cards/{id}/image (card image by id, on-demand Scryfall fetch and store); GET /api/cards/{card_name} (single). Parse prices: EU/US formats with/without thousands separators; skip invalid/N/A. GET /api/stats (total_cards, total_value, average_price, last_updated); same filter params as cards; 30s cache per filter key. POST /api/process (optional limit) → job_id, background run; POST /api/prices/update → job_id; POST /api/prices/update/{card_id} → job_id (single-card). 409 if bulk process already running. GET /api/jobs, GET /api/jobs/{id} (status, progress, errors, start_time; completed: summary). POST /api/jobs/{id}/cancel → 200 (or 404/409). POST /api/import/file — CSV/JSON to Postgres (DATABASE_URL); 400 invalid file, 501 no Postgres. GET /api/cards/suggest?q=, GET /api/cards/resolve?name= (Scryfall); GET /api/analytics/rarity, color-identity, cmc, sets (same filter params as stats).

Reuse SpreadsheetClient, CardFetcher, config_loader; ProcessorService. Errors: 400 invalid params, 503 Sheets quota (Retry-After), 500 + log. Log requests (method, path, status) INFO; errors ERROR.

### Requirements (compact)

- **Stats:** GET /api/stats → total_cards, total_value, average_price, last_updated. Optional query: search, rarity, type, set_name, price_min, price_max (same semantics as cards: name contains, exact match rarity/type/set_name, price range). Cache 30s per filter combination. Price parsing: EU/US with or without thousands; skip N/A and invalid.
- **Cards list:** GET /api/cards — filter then paginate (limit/offset); same filter semantics as stats so list and stats match. Order: newest first (created_at DESC) when store supports it. Card object MAY include created_at (ISO).
- **Card single:** GET /api/cards/{id} or name → 404 if not found. GET /api/cards/{id}/image → image bytes or 404; fetch/store from Scryfall when missing.
- **Suggest:** GET /api/cards/suggest?q= → JSON array of names (Scryfall); empty/short q → [] or 400.
- **Resolve:** GET /api/cards/resolve?name= → full card data for create; 404 if not found.
- **Single-card price update:** POST /api/prices/update/{card_id} → job_id; 404 if no card; not blocked by bulk update (409 only for concurrent bulk).
- **Analytics:** GET /api/analytics/rarity|color-identity|cmc|sets — same filter params as stats; JSON arrays for charts (e.g. { rarity, count }); KPIs via GET /api/stats with same params.
## Requirements
### Requirement: Authentication dependency injection
The backend SHALL provide a FastAPI dependency `get_current_user` that extracts and validates the JWT from the request cookie and returns the user payload. A convenience dependency `get_current_user_id` SHALL return only the user's database ID.

#### Scenario: Dependency returns user payload
- **WHEN** a route declares `Depends(get_current_user)` and the request has a valid JWT cookie
- **THEN** the dependency SHALL return a dict with `id`, `email`, `name`, `picture`

#### Scenario: Dependency returns 401 on missing/invalid JWT
- **WHEN** a route declares `Depends(get_current_user)` and the request has no JWT or an invalid/expired JWT
- **THEN** the dependency SHALL raise HTTPException with status 401

### Requirement: All data endpoints require authentication
Every existing data endpoint (cards, stats, analytics, decks, process, import, jobs, settings, prices) SHALL require a valid JWT cookie. The authenticated user's ID SHALL be used to scope data queries.

#### Scenario: Authenticated request to cards list
- **WHEN** an authenticated user calls `GET /api/cards`
- **THEN** the backend SHALL return only cards belonging to that user (filtered by `user_id`)

#### Scenario: Authenticated request to stats
- **WHEN** an authenticated user calls `GET /api/stats`
- **THEN** the backend SHALL compute stats only from that user's cards

#### Scenario: Authenticated request to decks
- **WHEN** an authenticated user calls `GET /api/decks`
- **THEN** the backend SHALL return only decks belonging to that user

#### Scenario: Unauthenticated request to data endpoint
- **WHEN** an unauthenticated client calls any data endpoint (e.g., `GET /api/cards`)
- **THEN** the backend SHALL return HTTP 401

### Requirement: Card CRUD scoped by user
Card create, update, and delete operations SHALL be scoped to the authenticated user.

#### Scenario: Create card for authenticated user
- **WHEN** an authenticated user calls `POST /api/cards/` with card data
- **THEN** the backend SHALL create the card with `user_id` set to the authenticated user's ID

#### Scenario: Update card owned by user
- **WHEN** an authenticated user calls `PUT /api/cards/{id}` for a card they own
- **THEN** the backend SHALL update the card

#### Scenario: Update card not owned by user
- **WHEN** an authenticated user calls `PUT /api/cards/{id}` for a card belonging to another user
- **THEN** the backend SHALL return HTTP 404

#### Scenario: Delete card not owned by user
- **WHEN** an authenticated user calls `DELETE /api/cards/{id}` for a card belonging to another user
- **THEN** the backend SHALL return HTTP 404

### Requirement: Deck operations scoped by user
All deck CRUD and card-in-deck operations SHALL be scoped to the authenticated user.

#### Scenario: Create deck for authenticated user
- **WHEN** an authenticated user calls `POST /api/decks/`
- **THEN** the backend SHALL create the deck with `user_id` set to the authenticated user's ID

#### Scenario: Access deck owned by another user
- **WHEN** an authenticated user calls `GET /api/decks/{id}` for a deck belonging to another user
- **THEN** the backend SHALL return HTTP 404

### Requirement: Process and price update scoped by user
Process and price update jobs SHALL operate only on the authenticated user's cards.

#### Scenario: Trigger process for user
- **WHEN** an authenticated user calls `POST /api/process`
- **THEN** the backend SHALL process only cards belonging to that user

#### Scenario: Trigger price update for user
- **WHEN** an authenticated user calls `POST /api/prices/update`
- **THEN** the backend SHALL update prices only for cards belonging to that user

### Requirement: Import scoped by user
File import SHALL create cards belonging to the authenticated user.

#### Scenario: Import file for user
- **WHEN** an authenticated user calls `POST /api/import/file` with a CSV/JSON file
- **THEN** all imported cards SHALL be created with `user_id` set to the authenticated user's ID

### Requirement: Insights catalog endpoint
The backend SHALL expose `GET /api/insights/catalog` that returns the full list of available insight questions with their metadata (id, label, label_key, keywords, category, icon, response_type, popular).

#### Scenario: Catalog returns all insights
- **WHEN** an authenticated user calls `GET /api/insights/catalog`
- **THEN** the backend SHALL return a JSON array with all 17 insight entries
- **THEN** each entry SHALL contain at minimum: `id`, `label`, `category`, `response_type`, `keywords`

### Requirement: Insights suggestions endpoint
The backend SHALL expose `GET /api/insights/suggestions` that returns the top 5-6 most relevant insight IDs for the authenticated user based on collection signals.

#### Scenario: Suggestions returned for user with collection
- **WHEN** an authenticated user calls `GET /api/insights/suggestions`
- **THEN** the backend SHALL return a JSON array of 5-6 objects, each containing `id` and `label`
- **THEN** the suggestions SHALL be ordered by relevance score (highest first)

#### Scenario: Suggestions for empty collection
- **WHEN** an authenticated user with no cards calls `GET /api/insights/suggestions`
- **THEN** the backend SHALL return fallback suggestions including `total_cards` and `total_value`

### Requirement: Insights execute endpoint
The backend SHALL expose `POST /api/insights/{insight_id}` that executes the specified insight computation and returns a rich typed response.

#### Scenario: Valid insight execution
- **WHEN** an authenticated user calls `POST /api/insights/total_value`
- **THEN** the backend SHALL return HTTP 200 with a JSON object containing `insight_id`, `question`, `answer_text`, `response_type`, and `data`

#### Scenario: Invalid insight ID
- **WHEN** an authenticated user calls `POST /api/insights/nonexistent`
- **THEN** the backend SHALL return HTTP 404

#### Scenario: Unauthenticated request
- **WHEN** an unauthenticated client calls `POST /api/insights/total_value`
- **THEN** the backend SHALL return HTTP 401

