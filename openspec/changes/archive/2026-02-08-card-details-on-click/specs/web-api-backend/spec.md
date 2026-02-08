# Web API Backend (delta)

## ADDED Requirements

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
