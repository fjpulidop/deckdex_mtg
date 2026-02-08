## 1. Backend: Scryfall suggest endpoint

- [x] 1.1 Add GET /api/cards/suggest?q=... route that calls Scryfall autocomplete API and returns JSON array of card names; handle empty/short query (e.g. q length < 2) with empty array or 400
- [x] 1.2 Reuse or wrap deckdex CardFetcher / Scryfall in backend for autocomplete (or call Scryfall HTTP directly); ensure rate limits are respected (no burst)

## 2. Backend: Resolve card by name endpoint

- [x] 2.1 Add GET /api/cards/resolve?name=... (or equivalent) that fetches full card data from Scryfall by name and returns payload matching card model (name, type, rarity, set_name, price, etc.) for client to use in create
- [x] 2.2 Return 404 when card name cannot be resolved (Scryfall and optional collection lookup); map Scryfall response fields to existing card schema

## 3. Frontend: API client for suggest and resolve

- [x] 3.1 Add api.getCardSuggest(query) calling GET /api/cards/suggest?q=... and returning array of names
- [x] 3.2 Add api.resolveCardByName(name) calling GET /api/cards/resolve?name=... and returning full card payload

## 4. Frontend: Add card modal – autocomplete and simplified form

- [x] 4.1 Refactor Add card form to show only name input (and Add/Cancel); remove type, rarity, price, set inputs from Add flow (keep them only for Edit)
- [x] 4.2 Implement debounced (250–300 ms) name input: on change, fetch collection suggestions via GET /api/cards?search=<query>&limit=10; display dropdown with "In your collection" section
- [x] 4.3 When collection returns zero results and query length >= 2, fetch catalog suggestions via api.getCardSuggest(query); display "Other cards" section in same dropdown
- [x] 4.4 Add "Search catalog" control (link or button) that triggers catalog suggestions for current query even when collection has results; show "Other cards" section when used
- [x] 4.5 On selecting a collection suggestion: use that card's data as create payload; call POST create (or resolve if backend returns id); close modal and refresh list
- [x] 4.6 On selecting a catalog suggestion: call api.resolveCardByName(selectedName), then POST create with resolved payload; on 404 show error and keep modal open; on success close modal and refresh list
- [x] 4.7 Keyboard and a11y: arrow keys to move in dropdown, Enter to select, Escape to close dropdown; focus management and aria attributes for combobox/autocomplete

## 5. Verification and edge cases

- [x] 5.1 Handle suggest/resolve API errors (toast or inline message); allow user to retry or type name manually and attempt add with resolve
- [x] 5.2 Ensure Edit card modal still shows and submits all fields (name, type, rarity, price, set) unchanged
