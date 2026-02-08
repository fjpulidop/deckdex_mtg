# Card Image Storage

Backend behavior to resolve a card's image by surrogate card id: return stored image if present; otherwise fetch the card by name from Scryfall, download the image, persist it to the filesystem, then serve it. Defines the GET endpoint contract and storage semantics.

### Requirement: Backend SHALL provide card image endpoint by card id

The system SHALL expose GET `/api/cards/{id}/image` where `id` is the surrogate card id (integer). The response SHALL be the card's image (e.g. image/jpeg or image/png). If no image is stored for that card, the system SHALL attempt to fetch the card by name from Scryfall, download the image, store it, then return it. If the card does not exist or the image cannot be obtained, the system SHALL return an appropriate error (e.g. 404).

#### Scenario: Return stored image when available
- **WHEN** client sends GET request to `/api/cards/{id}/image` and an image is already stored for that card id
- **THEN** system returns the stored image with appropriate Content-Type (e.g. image/jpeg) and status 200

#### Scenario: Fetch from Scryfall and store when not stored
- **WHEN** client sends GET request to `/api/cards/{id}/image` and no image is stored for that card id
- **THEN** system looks up the card by id to get its name, fetches the card from Scryfall by name, obtains the image URL (e.g. from image_uris), downloads the image, stores it in the configured storage (e.g. filesystem), and returns the image with status 200

#### Scenario: Return 404 when card not found
- **WHEN** client sends GET request to `/api/cards/{id}/image` and no card exists with that id
- **THEN** system returns 404 (or 404 when image cannot be obtained after a valid card lookup, per product choice)

#### Scenario: Images persist for subsequent requests
- **WHEN** an image was stored in a previous request for a given card id
- **THEN** subsequent GET requests to `/api/cards/{id}/image` for that id return the stored image without calling Scryfall again
