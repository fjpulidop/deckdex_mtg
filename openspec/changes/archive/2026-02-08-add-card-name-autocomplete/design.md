## Context

The dashboard has an Add card modal (`CardFormModal`) with manual fields: name, type, rarity, price, set. The backend exposes GET `/api/cards?search=...` (collection, name substring) and POST create for cards; `deckdex` already uses Scryfall via `CardFetcher` (search by name, card data). Scryfall offers a public autocomplete API (`/cards/autocomplete?q=...`) and card-by-name lookups. The goal is to simplify Add card to a single name field with hybrid autocomplete and to resolve type, rarity, price, set from the selected card (collection or Scryfall) instead of asking the user to type them.

## Goals / Non-Goals

**Goals:**
- Add card: one name field with autocomplete; suggestions from collection first, then Scryfall when collection has zero results or user chooses "Search catalog".
- On selection, resolve full card data (type, rarity, set_name, price) from the selected source and create the card via existing POST create API.
- Edit card: keep existing behaviour (all fields editable).

**Non-Goals:**
- Changing how Edit card or Delete card work beyond keeping edit form as-is.
- Storing or exposing Scryfall-specific IDs beyond what the current data model supports.
- Autocomplete for other fields (e.g. set or type) in this change.

## Decisions

### 1. Where to call Scryfall: backend proxy vs frontend direct

- **Chosen:** Backend proxy for Scryfall autocomplete (e.g. GET `/api/cards/suggest?q=...`) and for resolving card-by-name (e.g. GET `/api/cards/resolve?name=...` or similar) so that Scryfall URL and rate limits are handled server-side and CORS is not a concern.
- **Alternative:** Frontend calls Scryfall directly. Rejected to avoid CORS/rate-limit exposure and to centralize Scryfall usage in the backend (consistent with existing card image flow).

### 2. Resolution flow: who fetches full card data

- **Chosen:** Backend exposes a "resolve by name" endpoint that returns full card payload (type, rarity, set_name, price, etc.) from Scryfall (or from collection when the name matches a collection card). Frontend calls this on selection, then POSTs the returned payload to the existing create endpoint. Alternatively, a single "create by name" endpoint could resolve and create in one step; both are valid. This design assumes resolve + create (two calls) for clarity and reuse of existing POST create.
- **Alternative:** Frontend calls Scryfall for resolution. Rejected in favour of keeping Scryfall behind the backend.

### 3. When to show Scryfall suggestions

- **Chosen:** (a) Always show collection suggestions while typing (debounced). (b) When collection returns zero results and query length ≥ 2, automatically show a second section "Other cards" from Scryfall. (c) Additionally show a "Search catalog" control (e.g. link or button) so the user can request Scryfall suggestions even when collection has results.
- **Alternative:** Only show Scryfall after explicit "Search catalog" click. Chosen approach improves discoverability when the card is not in the collection.

### 4. Debounce and request limits

- **Chosen:** Debounce autocomplete requests (collection and Scryfall) by 250–300 ms. Limit suggestion count (e.g. 10 from collection, 10 from Scryfall) to keep responses small. Backend proxy for Scryfall SHALL respect Scryfall rate limits (e.g. one request per user keystroke after debounce is acceptable; avoid burst traffic).

### 5. Add vs Edit form split

- **Chosen:** Add card: single name field with autocomplete; no type, rarity, price, set inputs. Edit card: keep current form with all fields editable so users can correct or override data.

## Risks / Trade-offs

- **[Risk] Scryfall rate limits or downtime** → Mitigation: Backend proxy can cache suggest/resolve results briefly (e.g. 60s TTL per query); show a clear error in the UI if Scryfall is unavailable and allow manual name entry plus optional future "resolve" retry.
- **[Risk] Collection and Scryfall names differ (e.g. language, punctuation)** → Mitigation: When user selects "from collection", use that card's stored data for create; when selecting from Scryfall, use Scryfall response. No cross-source matching required for this change.
- **[Trade-off] Two requests on add (resolve then create)** → Acceptable for simplicity and reuse of existing create endpoint; can be collapsed into one "create by name" endpoint later if needed.

## Migration Plan

- No data migration. Deploy backend with new suggest and resolve endpoints; deploy frontend with updated Add card modal. Rollback: revert frontend to previous modal (name + type + rarity + price + set); backend can leave new endpoints in place (no breaking change).

## Open Questions

- None for MVP. Optional later: cache Scryfall resolve results per name in backend to reduce repeated lookups.
