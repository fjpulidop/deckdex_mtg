# Card Detail Modal (delta: revamp-edit-delete-cards)

## ADDED Requirements

### Requirement: Card detail modal SHALL offer Edit and Delete actions when card has id

The system SHALL display Edit and Delete actions (e.g. buttons) inside the card detail modal when the displayed card has a non-null id (i.e. the card is persisted in the collection). Edit SHALL switch the modal into inline edit mode (editable fields and Save/Cancel). Delete SHALL open a confirmation flow. These actions SHALL NOT be shown when the card has no id. The existing "Update price" action SHALL remain and SHALL be available alongside Edit and Delete when the card has an id.

#### Scenario: Edit and Delete buttons visible when card has id
- **WHEN** the card detail modal is open with a card that has an id
- **THEN** the modal displays Edit and Delete actions (e.g. buttons) that the user can click

#### Scenario: Edit and Delete not shown when card has no id
- **WHEN** the card detail modal is open with a card that has no id (e.g. null or undefined)
- **THEN** the modal does not display Edit or Delete actions

### Requirement: Card detail modal SHALL support inline edit mode with Save and Cancel

The system SHALL support two modes in the card detail modal: view (read-only) and edit (editable fields). In view mode, the modal SHALL show an Edit button. When the user clicks Edit, the modal SHALL switch to edit mode: displayed text fields (e.g. name, type line, mana cost, oracle text, power, toughness, set name, set number, rarity, price) SHALL become editable in place; the Edit button SHALL be replaced by Save and Cancel buttons. Save SHALL persist changes via PUT `/api/cards/{id}` and SHALL then return the modal to view mode (and MAY refresh card data). Cancel SHALL discard in-memory edits and SHALL return the modal to view mode without calling the API.

#### Scenario: Clicking Edit switches to edit mode
- **WHEN** the user clicks the Edit action in the card detail modal
- **THEN** the modal switches to edit mode: fields become editable, Edit is replaced by Save and Cancel

#### Scenario: Save persists changes and returns to view mode
- **WHEN** the user edits one or more fields and clicks Save
- **THEN** the system sends PUT `/api/cards/{id}` with the current form values, and on success returns the modal to view mode and MAY refresh the displayed card and list

#### Scenario: Cancel discards edits and returns to view mode
- **WHEN** the user is in edit mode and clicks Cancel
- **THEN** the system discards in-memory edits, returns the modal to view mode, and does not call the update API

### Requirement: Card detail modal SHALL confirm before deleting a card

When the user clicks the Delete action in the card detail modal, the system SHALL show a confirmation (e.g. dialog) with the message equivalent to "Are you sure you want to delete this card?" and options for Yes and No. If the user chooses No, the confirmation SHALL close and the modal SHALL remain open in its current state. If the user chooses Yes, the system SHALL call DELETE `/api/cards/{id}`, SHALL close the card detail modal, and SHALL refresh or invalidate the card list (and stats) so the deleted card is no longer shown.

#### Scenario: Delete shows confirmation
- **WHEN** the user clicks the Delete action in the card detail modal
- **THEN** the system shows a confirmation with Yes and No (or equivalent) options

#### Scenario: Confirmation No keeps modal open
- **WHEN** the user chooses No in the delete confirmation
- **THEN** the confirmation closes and the card detail modal remains open; the card is not deleted

#### Scenario: Confirmation Yes deletes card and closes modal
- **WHEN** the user chooses Yes in the delete confirmation
- **THEN** the system sends DELETE `/api/cards/{id}`, closes the card detail modal, and updates the list so the card disappears
