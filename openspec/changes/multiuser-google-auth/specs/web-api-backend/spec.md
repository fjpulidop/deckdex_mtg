## ADDED Requirements

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
