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

### Requirement: Card detail modal SHALL offer Update price action when card has id

The system SHALL display an "Update price" action (e.g. button) inside the card detail modal when the displayed card has a non-null id (i.e. the card is persisted in the collection). When the user triggers this action, the system SHALL request a single-card price update from the backend (e.g. POST `/api/prices/update/{card_id}`), SHALL receive a job_id in the response, and SHALL register that job with the global jobs state so it appears in the app-wide jobs bar with a label such as "Update price". The modal MAY remain open; the user SHALL see the job progress and completion in the bottom jobs bar. The action SHALL NOT be shown when the card has no id.

#### Scenario: Update price button visible when card has id
- **WHEN** the card detail modal is open with a card that has an id
- **THEN** the modal displays an "Update price" action (e.g. button) that the user can click

#### Scenario: Update price button not shown when card has no id
- **WHEN** the card detail modal is open with a card that has no id (e.g. null or undefined)
- **THEN** the modal does not display the "Update price" action

#### Scenario: Triggering Update price starts job and shows it in jobs bar
- **WHEN** the user clicks the "Update price" action in the modal for a card with an id
- **THEN** the system sends a request to the backend to start a single-card price update for that card's id, receives a job_id, and adds the job to the global jobs state so it appears in the app-wide jobs bar (e.g. with label "Update price")

### Requirement: System SHALL refresh displayed data when single-card Update price job completes

When the single-card "Update price" job (started from the card detail modal) completes, the system SHALL refresh the following so they reflect the updated price: (1) total value and aggregate stats (e.g. Total Value, Average Price on the dashboard), (2) the price displayed in the card detail modal if the modal is still open for that same card, and (3) the card table rows so the updated price is visible in the list. The refresh SHALL occur when the job completes (e.g. when the job bar reports completion), without requiring the user to close the modal or reload the page.

#### Scenario: Total value and stats refresh when Update price job completes
- **WHEN** a single-card "Update price" job started from the card detail modal completes successfully
- **THEN** the dashboard total value (and any other stats derived from the collection) are refreshed so they reflect the updated price

#### Scenario: Modal price updates when job completes and modal still open for that card
- **WHEN** a single-card "Update price" job completes and the card detail modal is still open for the same card that was updated
- **THEN** the price shown in the modal is updated to the new value without the user closing or reopening the modal

#### Scenario: Card table rows show updated price after job completes
- **WHEN** a single-card "Update price" job completes
- **THEN** the card table (list) is refreshed so the row for that card displays the updated price
