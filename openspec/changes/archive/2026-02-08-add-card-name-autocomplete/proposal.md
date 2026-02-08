## Why

Adding a new card in the dashboard currently requires typing the full card name and optionally filling type, rarity, price, and set by hand. This is error-prone and slow. Users should be able to find the card by partial name (autocomplete) and have the system fill the rest of the data from the catalog (Scryfall) or from the existing collection, so that the Add card flow is faster and more accurate.

## What Changes

- **Add card modal:** The "Add card" form SHALL be simplified to a single primary field: **card name**, with hybrid autocomplete. Type, rarity, price, and set SHALL NOT be user-filled on add; they SHALL be resolved when the user selects a card (from collection or Scryfall) and SHALL be sent to the create API automatically.
- **Hybrid autocomplete:** While the user types in the name field, the UI SHALL suggest card names from (1) the current collection (existing GET `/api/cards?search=...`), and (2) when collection returns zero results (and optionally via an explicit "Search catalog" control), from Scryfall's autocomplete so that any MTG card can be added.
- **Card resolution:** When the user confirms a selected card (from either source), the system SHALL obtain full card data (type, rarity, set_name, price where available) from Scryfall (or from the collection row when the suggestion came from the collection) and SHALL create the card via the existing create API with those fields populated.
- **Edit card:** The Edit card modal SHALL continue to allow editing type, rarity, price, and set for existing cards (no change to edit behaviour).

## Capabilities

### New Capabilities

- **card-name-autocomplete**: End-to-end behaviour for finding and adding a card by name: hybrid autocomplete (collection first, then Scryfall when needed), simplified Add card form (name-only input with suggestions), and resolving full card data from Scryfall or collection on selection before calling the create API.

### Modified Capabilities

- **web-dashboard-ui**: Add card form SHALL expose only a name field with autocomplete; type, rarity, price, set SHALL be resolved on selection and SHALL NOT be manual inputs on add. Edit card form SHALL retain editable type, rarity, price, set.
- **web-api-backend**: SHALL provide a way for the client to get card name suggestions from Scryfall (e.g. GET `/api/cards/suggest?q=...` proxying Scryfall autocomplete) and SHALL support creating a card with full data resolved from Scryfall (e.g. endpoint that accepts a card name and returns or persists resolved Scryfall data, or the client resolves and POSTs full payload to existing POST create endpoint).

## Impact

- **Frontend:** `CardFormModal` (or equivalent Add card form) will be refactored: name input gains autocomplete UI (dropdown with two sections: "In your collection" and "Other cards" from Scryfall); type, rarity, price, set inputs removed for Add flow; on selection, client (or backend) resolves full card data and submits to POST create.
- **Backend:** New endpoint(s) for Scryfall autocomplete proxy and/or card-by-name resolution; reuse of existing POST create card endpoint with full payload. Possible use of existing `deckdex` CardFetcher/Scryfall integration.
- **Dependencies:** Scryfall API (autocomplete, card by name); existing collection API for suggestions. No new runtime dependencies beyond current stack.
