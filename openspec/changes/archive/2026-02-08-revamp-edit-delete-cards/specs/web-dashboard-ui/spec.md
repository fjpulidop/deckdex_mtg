# Web Dashboard UI (delta: revamp-edit-delete-cards)

## MODIFIED Requirements

### Requirement: Card table rows SHALL be clickable to open card detail modal

The system SHALL allow the user to click on a card table row to open the card detail modal (view, edit, and delete are performed in that modal). The card table SHALL NOT display an Actions column; there SHALL be no Edit or Delete buttons on table rows. The only way to open the card detail modal from the table SHALL be by clicking a row.

#### Scenario: Clicking a row opens card detail modal
- **WHEN** the user clicks on a card row in the table
- **THEN** the system opens the card detail modal with that card's data and loads its image

#### Scenario: Card table has no Actions column
- **WHEN** the dashboard renders the card table
- **THEN** the table does not display an Actions column and does not show Edit or Delete buttons on rows

#### Scenario: Dashboard wires table to card detail modal
- **WHEN** the dashboard renders the card table
- **THEN** the table is configured with a row-click handler that opens the card detail modal for the clicked card, and the modal receives the selected card and uses the image API for that card's id

### Requirement: Add card form SHALL have only name input with autocomplete

The Add card modal SHALL display a single required field for card name. The name field SHALL support autocomplete with suggestions from the collection and, when applicable, from the catalog (Scryfall). The form SHALL NOT display input fields for type, rarity, price, or set when adding a card; those values SHALL be obtained by the system when the user selects a suggestion (from collection or catalog) and SHALL be sent in the create request. Editing of existing cards SHALL be performed inside the card detail modal (inline edit with Save and Cancel), not in a separate Edit card modal.

#### Scenario: Add card modal shows only name field
- **WHEN** the user opens the Add card modal
- **THEN** the form SHALL show one text input for card name (with autocomplete) and Add/Cancel actions; it SHALL NOT show inputs for type, rarity, price, or set

#### Scenario: Name field shows debounced autocomplete dropdown
- **WHEN** the user types in the Add card name field
- **THEN** after a short debounce (e.g. 250–300 ms) the system SHALL show a dropdown with suggestions (collection and optionally catalog), with sections labeled e.g. "In your collection" and "Other cards" when both are present

#### Scenario: Edit is in card detail modal with Save and Cancel
- **WHEN** the user opens the card detail modal for an existing card and clicks Edit
- **THEN** the modal SHALL show editable fields for name, type, rarity, price, and set (and other card fields as appropriate), with Save and Cancel actions; there is no separate Edit card modal

## REMOVED Requirements

### Requirement: Row actions (Edit, Delete) distinct from opening detail modal

**Reason:** Edit and Delete are moved into the card detail modal; the table no longer has an Actions column.

**Migration:** Open a card via row click, then use Edit or Delete inside the card detail modal.
