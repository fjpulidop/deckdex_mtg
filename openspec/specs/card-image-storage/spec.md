# Card Image Storage

Resolve image by card id via global cache keyed by `scryfall_id`. Any authenticated user may request any card image. GET /api/cards/{id}/image contract.

### Requirement: Storage
PostgreSQL `card_image_cache` table (keyed by `scryfall_id`) is authoritative. Stored images persist across restarts; no repeat Scryfall calls for the same card printing across any user.

#### Scenario: Cache persists across restarts
- **WHEN** the backend restarts
- **THEN** previously cached images SHALL still be available without re-fetching from Scryfall

### Requirement: Flow
`GET /api/cards/{id}/image` → verify user is authenticated (401 if not); lookup card by `id` to get `name` and `scryfall_id`; if `scryfall_id` known and image in `card_image_cache` → 200 + bytes + Content-Type; if `scryfall_id` unknown or cache miss → fetch card from Scryfall by name, extract `scryfall_id`, update `cards` row, check cache again, download if still missing, store in cache, return 200; card not found or image unavailable → 404. Card ownership is NOT required — any authenticated user may request any card image.

#### Scenario: Authenticated user retrieves cached image
- **WHEN** an authenticated user requests `GET /api/cards/{id}/image` and the image is in `card_image_cache`
- **THEN** the system SHALL return 200 with image bytes and correct Content-Type header

#### Scenario: Unauthenticated request rejected
- **WHEN** an unauthenticated request hits `GET /api/cards/{id}/image`
- **THEN** the system SHALL return 401

#### Scenario: Card not found returns 404
- **WHEN** an authenticated user requests an image for a non-existent card id
- **THEN** the system SHALL return 404

#### Scenario: User can access another user's card image
- **WHEN** an authenticated user requests an image for a card_id that belongs to a different user
- **THEN** the system SHALL return 200 with the image (ownership check is not performed)
