## Context

The dashboard fetches cards via GET `/api/cards` with only `search`, `limit`, and `offset`. Stats are fetched via GET `/api/stats` with the full filter set (search, rarity, type, set_name, price_min, price_max) and the backend filters the collection before aggregating. The frontend then applies rarity/type/set/price filters **client-side** to the card list. Because the card list is a bounded window (e.g. first 1000 cards) and filtering happens on that window, the table can show fewer cards than the stats indicate when the user filters by set (or other dimensions). Example: 4 cards in "Adventures in the Forgotten Realms" with total €1.78, but only 1 of those 4 is in the first 1000 cards returned, so the table shows 1 card (€1.14) and the stats show 4 cards (€1.78).

## Goals / Non-Goals

**Goals:**
- Align list and stats so they always refer to the same filtered subset.
- Reuse the same filter semantics for both endpoints (single source of truth).
- Minimal API surface change: add optional query params to GET `/api/cards`; no new endpoints.

**Non-Goals:**
- Changing how stats work (already correct).
- Changing filter UI or pagination UX.
- Adding new filter dimensions.

## Decisions

1. **Apply filters in GET `/api/cards` before pagination**  
   Filter the full collection with the same logic as GET `/api/stats` (search, rarity, type, set_name, price_min, price_max), then apply limit/offset to the filtered result. This guarantees the list and stats counts match. Alternative: keep client-side filtering but fetch "all" cards when filters are active — rejected because it could be expensive and still requires the backend to support filtered list for consistency.

2. **Share filter logic between cards and stats**  
   Extract the collection-filtering logic (parse_price + filter by search/rarity/type/set_name/price range) into a small shared module (e.g. `backend/api/filters.py`) and use it from both routes. This avoids duplication and ensures semantics stay identical. Alternative: duplicate the logic in cards route — rejected to prevent drift.

3. **Frontend passes current filters to GET `/api/cards`**  
   `useCards` (and the API client) will accept the same filter shape as stats (search, rarity, type, set, price_min, price_max). Dashboard passes the current filter state into the hook so each filter change triggers a new request with the new params. The displayed list is the API response; client-side filter is removed or becomes a no-op so the list is exactly what the API returned.

4. **Options (set/type/rarity dropdowns) from current response**  
   Today options are derived from the unfiltered (or search-only) card list. After the change, options are derived from the filtered list returned by the API. When the user selects e.g. set "Adventures in the Forgotten Realms", the next request returns only those 4 cards, so set options will only contain that set. This is acceptable and keeps one source of data.

## Risks / Trade-offs

- **Extra request when changing filters:** Each filter change refetches cards. Acceptable; list is bounded (limit 1000) and cache (e.g. TanStack Query) mitigates repeated identical requests.
- **Shared filter module:** New file and imports; if filter semantics ever diverge between list and stats, we must remember to keep one implementation. Mitigation: single `filter_collection` (and `parse_price`) used by both routes.
