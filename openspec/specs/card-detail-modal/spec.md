# Card Detail Modal

Read-only modal that displays a single card's data (from the collection API) and its image (from the card image endpoint) in a Scryfall-style layout: image on one side, structured text on the other. Used when the user clicks a row in the card table.

### Requirement: Card detail modal SHALL display card image and structured data

The system SHALL provide a modal component that shows the selected card's image and metadata in a fixed layout. The image SHALL be loaded from the backend card image endpoint (by card id). The text content SHALL use data from the application's card model (name, type line, mana cost, description/oracle text, power/toughness, set name, set number, rarity, price) in a structured, Scryfall-like presentation (e.g. image left, text right).

#### Scenario: Modal shows card image from image endpoint
- **WHEN** the modal is open with a card that has an id
- **THEN** the system requests the card image from the backend (e.g. GET `/api/cards/{id}/image`) and displays it in the modal

#### Scenario: Modal shows loading state while image loads
- **WHEN** the image request is in progress
- **THEN** the modal displays a placeholder or skeleton where the image will appear (e.g. loading spinner or gray block)

#### Scenario: Modal shows error state when image unavailable
- **WHEN** the image endpoint returns an error (e.g. 404 or 5xx)
- **THEN** the modal displays a fallback (e.g. message or icon) indicating the image is unavailable, and still shows the card's text data

#### Scenario: Modal displays structured card text
- **WHEN** the modal is open with a card
- **THEN** the system displays at least: name, type line, mana cost, description (oracle text), power/toughness when present, set name, set number, rarity, and price in a clear layout consistent with a Scryfall-style card view

#### Scenario: Modal can be closed
- **WHEN** the user closes the modal (e.g. close button or overlay click)
- **THEN** the modal is dismissed and focus returns to the dashboard; no data is persisted from the modal (read-only)
