# Card Name Autocomplete

End-to-end behaviour for finding and adding a card by name: hybrid autocomplete (collection first, then Scryfall when needed), simplified Add card form (name-only input with suggestions), and resolving full card data from Scryfall or collection on selection before calling the create API.

### Requirement: Add card flow SHALL use hybrid name autocomplete

The Add card flow SHALL provide a single name field with autocomplete. Suggestions SHALL come first from the current collection (GET `/api/cards?search=...&limit=10`). When the collection returns zero results and the user has entered at least two characters, the system SHALL also request and display suggestions from the catalog (Scryfall) via the backend suggest endpoint. The UI SHALL offer an explicit "Search catalog" control so the user can request catalog suggestions even when collection has results. The dropdown SHALL present two sections when both sources are used: "In your collection" and "Other cards".

#### Scenario: Typing in name field requests collection suggestions
- **WHEN** the user types in the Add card name field (with debounce applied)
- **THEN** the system requests GET `/api/cards?search=<query>&limit=10` and displays matching card names in a dropdown

#### Scenario: Zero collection results triggers catalog suggestions
- **WHEN** the collection returns zero results for the current query and the query length is at least 2
- **THEN** the system requests catalog suggestions (e.g. GET `/api/cards/suggest?q=<query>`) and displays them in an "Other cards" section of the dropdown

#### Scenario: Search catalog control requests catalog suggestions
- **WHEN** the user activates the "Search catalog" control (e.g. link or button)
- **THEN** the system requests catalog suggestions for the current query and displays them (e.g. in "Other cards" section) even if collection already has results

#### Scenario: Selecting a collection suggestion uses that card's data
- **WHEN** the user selects a suggestion that came from the collection
- **THEN** the system uses that card's stored data (name, type, rarity, set_name, price, etc.) as the payload and SHALL call the create API with it (or resolve endpoint first if backend returns full row)

#### Scenario: Selecting a catalog suggestion resolves then creates
- **WHEN** the user selects a suggestion that came from the catalog (Scryfall)
- **THEN** the system calls the backend resolve-by-name endpoint to obtain full card data, then SHALL call the create API with the resolved payload

#### Scenario: Add form does not show type, rarity, price, set as inputs
- **WHEN** the Add card modal is open
- **THEN** the form SHALL display only the card name field (with autocomplete) and actions (e.g. Add, Cancel); type, rarity, price, and set SHALL NOT be manual input fields
