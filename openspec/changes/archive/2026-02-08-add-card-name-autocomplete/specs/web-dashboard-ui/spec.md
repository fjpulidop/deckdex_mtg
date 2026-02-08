# Web Dashboard UI (delta)

Add card form SHALL expose only a name field with autocomplete; type, rarity, price, set SHALL be resolved on selection and SHALL NOT be manual inputs on add. Edit card form SHALL retain editable type, rarity, price, set.

## ADDED Requirements

### Requirement: Add card form SHALL have only name input with autocomplete

The Add card modal SHALL display a single required field for card name. The name field SHALL support autocomplete with suggestions from the collection and, when applicable, from the catalog (Scryfall). The form SHALL NOT display input fields for type, rarity, price, or set when adding a card; those values SHALL be obtained by the system when the user selects a suggestion (from collection or catalog) and SHALL be sent in the create request. The Edit card modal SHALL continue to display and allow editing of name, type, rarity, price, and set for existing cards.

#### Scenario: Add card modal shows only name field
- **WHEN** the user opens the Add card modal
- **THEN** the form SHALL show one text input for card name (with autocomplete) and Add/Cancel actions; it SHALL NOT show inputs for type, rarity, price, or set

#### Scenario: Name field shows debounced autocomplete dropdown
- **WHEN** the user types in the Add card name field
- **THEN** after a short debounce (e.g. 250–300 ms) the system SHALL show a dropdown with suggestions (collection and optionally catalog), with sections labeled e.g. "In your collection" and "Other cards" when both are present

#### Scenario: Edit card modal still has all fields
- **WHEN** the user opens the Edit card modal for an existing card
- **THEN** the form SHALL show editable fields for name, type, rarity, price, and set as today; behaviour SHALL be unchanged from current Edit card flow
