# Card Name Autocomplete

Add card by name: single name field, hybrid autocomplete (collection then Scryfall), resolve full data on selection before create.

### Requirements (compact)

- **Autocomplete:** Name field with debounce. Suggestions: GET /api/cards?search=&limit=10 (collection); if zero and length ≥2, also GET /api/cards/suggest?q= (Scryfall). Optional "Search catalog" to force catalog. Dropdown sections: "In your collection", "Other cards".
- **Selection:** Collection suggestion → use that card’s data for create. Catalog suggestion → GET resolve?name= then create with resolved payload.
- **Form:** Add modal shows only name (with autocomplete) + actions; no manual type, rarity, price, set inputs.
