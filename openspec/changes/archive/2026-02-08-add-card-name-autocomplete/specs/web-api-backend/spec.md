# Web API Backend (delta)

Backend SHALL provide a way for the client to get card name suggestions from Scryfall and SHALL support obtaining full card data by name so the client can create a card with resolved type, rarity, price, set.

## ADDED Requirements

### Requirement: Backend SHALL provide card name suggest endpoint

The system SHALL expose GET `/api/cards/suggest?q=<query>` (or equivalent) that returns a list of card names matching the query from Scryfall's autocomplete API. The endpoint SHALL proxy or call Scryfall and SHALL return a JSON array of name strings (or equivalent) for the client to display in the Add card autocomplete dropdown. The backend SHALL respect Scryfall rate limits (e.g. debouncing or caching is acceptable).

#### Scenario: GET suggest returns names from Scryfall
- **WHEN** client sends GET request to `/api/cards/suggest?q=lotus`
- **THEN** system returns a JSON array of card names (e.g. from Scryfall autocomplete) that match "lotus"

#### Scenario: Suggest handles empty or short query
- **WHEN** client sends GET request to `/api/cards/suggest` with missing or very short q (e.g. length < 2)
- **THEN** system returns an empty array or 400 without calling Scryfall

### Requirement: Backend SHALL provide resolve card by name endpoint

The system SHALL expose an endpoint (e.g. GET `/api/cards/resolve?name=<card_name>`) that, given a card name, returns full card data (type, rarity, set_name, price, and other fields needed for create) from Scryfall. If the name matches a card in the collection, the system MAY return that card's data instead. The response SHALL be suitable for the client to send as the body of POST create (or the backend MAY accept a create-by-name variant). This allows the Add card flow to resolve type, rarity, price, set without the user entering them.

#### Scenario: GET resolve returns full card data for name
- **WHEN** client sends GET request to `/api/cards/resolve?name=Black%20Lotus` (or equivalent)
- **THEN** system returns JSON with at least name, type, rarity, set_name, price (and other fields as per card model) suitable for creating a card

#### Scenario: Resolve returns 404 when card not found
- **WHEN** client sends GET request to resolve with a name that Scryfall (and collection) cannot resolve
- **THEN** system returns 404 (or appropriate error) so the client can show an error or allow manual retry
