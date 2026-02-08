# Web Dashboard UI (delta)

## ADDED Requirements

### Requirement: Card table rows SHALL be clickable to open card detail modal

The system SHALL allow the user to click on a card table row to open a read-only card detail modal. Clicks on row actions (Edit, Delete) SHALL NOT open the detail modal; only clicking the row itself SHALL trigger opening the modal.

#### Scenario: Clicking a row opens card detail modal
- **WHEN** the user clicks on a card row in the table (and not on Edit or Delete)
- **THEN** the system opens the card detail modal with that card's data and loads its image

#### Scenario: Clicking Edit does not open detail modal
- **WHEN** the user clicks the Edit button on a row
- **THEN** the system performs the edit action (e.g. opens edit form) and does NOT open the card detail modal

#### Scenario: Clicking Delete does not open detail modal
- **WHEN** the user clicks the Delete button on a row
- **THEN** the system performs the delete action and does NOT open the card detail modal

#### Scenario: Dashboard wires table to card detail modal
- **WHEN** the dashboard renders the card table
- **THEN** the table is configured with a row-click handler that opens the card detail modal for the clicked card, and the modal receives the selected card and uses the image API for that card's id
