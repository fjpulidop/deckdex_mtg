# Cards CRUD

Full CRUD API (create, update, delete card by id) and UI (add card, edit card, delete card) in addition to existing list and filter.

## ADDED Requirements

### Requirement: API SHALL support creating a new card

The system SHALL provide an endpoint (e.g. POST /api/cards) that accepts a card payload (name and other Card fields) and SHALL create a new card in the repository. The response SHALL include the created card with its assigned id. The system SHALL validate required fields (e.g. name) and SHALL return 400 for invalid input.

#### Scenario: Successful card creation
- **WHEN** the client sends a valid POST request with card data (at least name and any required fields)
- **THEN** the system SHALL create the card in Postgres and SHALL return the card including its id and 201 (or 200) status

#### Scenario: Creation with invalid or missing required data
- **WHEN** the client sends a request with missing or invalid required fields (e.g. empty name)
- **THEN** the system SHALL respond with 400 and SHALL NOT create a card

### Requirement: API SHALL support updating a card by id

The system SHALL provide an endpoint (e.g. PUT or PATCH /api/cards/{id}) that accepts the card id and a payload of fields to update, and SHALL update the card in the repository. The response SHALL include the updated card or 404 if the id does not exist. The system SHALL validate input and SHALL return 400 for invalid data.

#### Scenario: Successful card update
- **WHEN** the client sends a valid update request for an existing card id
- **THEN** the system SHALL update the card in Postgres and SHALL return the updated card

#### Scenario: Update non-existent card
- **WHEN** the client sends an update request for an id that does not exist
- **THEN** the system SHALL respond with 404

### Requirement: API SHALL support deleting a card by id

The system SHALL provide an endpoint (e.g. DELETE /api/cards/{id}) that accepts the card id and SHALL remove the card from the repository. The system SHALL return 204 (or 200) on success and 404 if the id does not exist.

#### Scenario: Successful card deletion
- **WHEN** the client sends a delete request for an existing card id
- **THEN** the system SHALL remove the card from Postgres and SHALL return success (204 or 200)

#### Scenario: Delete non-existent card
- **WHEN** the client sends a delete request for an id that does not exist
- **THEN** the system SHALL respond with 404

### Requirement: List and get endpoints SHALL use the repository

The existing list (GET /api/cards) and get-by-id or get-by-name endpoints SHALL read from the collection repository (Postgres), not from Google Sheets. Pagination, search, and filter behavior SHALL be preserved; only the data source SHALL change.

#### Scenario: List cards from Postgres
- **WHEN** the client requests the card list (with optional limit, offset, search)
- **THEN** the system SHALL return cards from the Postgres repository and SHALL apply the same filtering/pagination semantics as before

### Requirement: UI SHALL allow adding a new card

The dashboard (or cards view) SHALL provide a way to add a new card (e.g. "Add card" button opening a form or modal). The form SHALL include fields for the card (at least name; other fields as needed). On submit, the UI SHALL call the create API and SHALL refresh or update the list on success; on error, the UI SHALL display the error.

#### Scenario: User adds a card from the UI
- **WHEN** the user fills the add-card form and submits
- **THEN** the system SHALL send the data to the create endpoint and SHALL add the new card to the list on success

### Requirement: UI SHALL allow editing an existing card

The dashboard (or cards view) SHALL provide a way to edit an existing card (e.g. edit action or row click opening a form or modal). The form SHALL be pre-filled with the card data. On submit, the UI SHALL call the update API by id and SHALL refresh or update the list on success; on error, the UI SHALL display the error.

#### Scenario: User edits a card from the UI
- **WHEN** the user opens the edit form for a card, changes fields, and submits
- **THEN** the system SHALL send the update to the update endpoint and SHALL reflect the changes in the list on success

### Requirement: UI SHALL allow deleting a card

The dashboard (or cards view) SHALL provide a way to delete a card (e.g. delete button with confirmation). On confirm, the UI SHALL call the delete API by id and SHALL remove the card from the list on success; on error, the UI SHALL display the error.

#### Scenario: User deletes a card from the UI
- **WHEN** the user confirms deletion of a card
- **THEN** the system SHALL call the delete endpoint and SHALL remove the card from the list on success
