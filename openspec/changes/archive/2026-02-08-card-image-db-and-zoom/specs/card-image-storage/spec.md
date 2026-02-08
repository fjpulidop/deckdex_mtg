# Card Image Storage (delta: persist in database)

Backend SHALL persist card images in the database so they are not re-downloaded from Scryfall on every session. The GET endpoint contract is unchanged.

## MODIFIED Requirements

### Requirement: Card images SHALL be stored in the database

The system SHALL store card images in PostgreSQL (e.g. in a `card_images` table keyed by card id, with content type and image data). When a client requests GET `/api/cards/{id}/image`, the system SHALL first look up the image for that card id in the database. If a row exists, the system SHALL return the stored image bytes with the stored content type and status 200. If no image is stored for that card id, the system SHALL attempt to fetch the card by name from Scryfall, download the image, store it in the database (INSERT or upsert), then return it. If the card does not exist or the image cannot be obtained, the system SHALL return an appropriate error (e.g. 404). Stored images SHALL persist across application restarts and deployments. The system MAY additionally write to the filesystem for local caching; the database is the authoritative store for "already fetched" images so that subsequent requests do not call Scryfall again.

#### Scenario: Return stored image from database when available
- **WHEN** client sends GET request to `/api/cards/{id}/image` and an image is already stored in the database for that card id
- **THEN** system returns the stored image from the database with appropriate Content-Type and status 200 without calling Scryfall

#### Scenario: Fetch from Scryfall and store in database when not stored
- **WHEN** client sends GET request to `/api/cards/{id}/image` and no image is stored in the database for that card id
- **THEN** system looks up the card by id to get its name, fetches the card from Scryfall by name, obtains the image URL, downloads the image, stores it in the database, and returns the image with status 200

#### Scenario: Images persist in database for subsequent requests
- **WHEN** an image was stored in the database in a previous request for a given card id
- **THEN** subsequent GET requests to `/api/cards/{id}/image` for that id return the stored image from the database without calling Scryfall again

## Unchanged

- GET `/api/cards/{id}/image` response body, status codes (200 image body, 404 when card not found or image unavailable), and Content-Type behavior remain as before. No API contract change for clients.
