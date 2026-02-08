## Context

The dashboard card table currently has a `Filters` component with a text search (name, debounced, sent to API) and a rarity dropdown (client-side). Filter state lives in `Dashboard.tsx`; cards are fetched with `useCards({ search, limit: 1000 })` and rarity is applied in memory. The backend `/api/cards` accepts only `limit`, `offset`, and `search`. Table columns are Name, Type, Rarity, Price, Set. Styling uses Tailwind (rounded-lg, shadow, focus:ring-blue-500, gray scale). This change adds Type, Set, and Price filters, active-filter chips, and a result count without changing the API.

## Goals / Non-Goals

**Goals:**

- Add Type, Set, and Price filters that work together with existing name search and rarity.
- Derive Type and Set options from the currently loaded card data (no new API).
- Show active filters as removable chips and a live result count.
- Keep one "Clear Filters" action; style consistently with existing dashboard components.

**Non-Goals:**

- Server-side filtering (type, set, price) or new API query params.
- Persisting filter state to URL or localStorage.
- Full-text search beyond name; search in type/set text fields.

## Decisions

**1. Client-side filtering for type, set, and price**

- **Choice:** Apply type, set, and price filters in the frontend on the same list used for rarity (after the initial fetch).
- **Rationale:** Current pattern already uses client-side rarity filter and a 1000-card cap; adding more dimensions the same way keeps the change small and avoids backend work. If the collection grows and 1000 becomes too limiting, we can add query params later.
- **Alternative:** Add `type`, `set_name`, `price_min`, `price_max` to `/api/cards`. Rejected for this change to limit scope.

**2. Type and Set options from loaded data**

- **Choice:** Build dropdown options by collecting distinct `type` and `set_name` values from the cards returned by the current query (after name search). Sort options alphabetically; "All" as default.
- **Rationale:** No new endpoints; options always match what can be shown. If search narrows the set, type/set options narrow accordingly, which is acceptable.
- **Alternative:** Separate "facets" or config endpoint. Rejected for MVP.

**3. Price filter: min/max inputs**

- **Choice:** Two optional number inputs (min price, max price). Empty means no bound. Parse as decimal; invalid or negative treated as "no bound" for that side. Currency remains EUR (€).
- **Rationale:** Simple, clear, and consistent with "filter by column". Presets (e.g. "< €1") can be added later if needed.
- **Alternative:** Single slider with two handles. Rejected for simplicity and accessibility (keyboard, screen readers).

**4. Where filter state and chips live**

- **Choice:** Keep all filter state in `Dashboard.tsx` (single source of truth). `Filters` component receives callbacks and optional "active" values; it can render chips and count in the same bar or just below, and emit events to clear one filter or all.
- **Rationale:** Matches current pattern (search/rarity in Dashboard). Chips and count are part of the filter UX, so either extend `Filters` to accept and display them or add a small sibling (e.g. `FilterChips`). Prefer extending `Filters` to avoid prop drilling and keep one cohesive bar.
- **Alternative:** Lift state into a small context or custom hook. Rejected for this scope; can refactor later if needed.

**5. Result count placement**

- **Choice:** Show "Showing X cards" (or "X results") near the filter bar—e.g. right-aligned on the same row as chips or on a second row below the controls. Update on every filter change (derived from filtered list length).
- **Rationale:** Gives immediate feedback and matches the proposal. No extra API call.

## Risks / Trade-offs

- **Type/Set options depend on current result set:** If the user applies a strict name search, type/set dropdowns may have few options. Acceptable; we can document or add a hint. Mitigation: label dropdowns as "Type (in results)" if we want to make this explicit later.
- **Price parsing:** Different locales use comma vs dot for decimals. We use dot for now; if we later support comma, we need a small parser. Mitigation: document expected format (e.g. "Use . for decimals" in placeholder).
- **No URL state:** Refreshing the page resets filters. Mitigation: none for this change; can add query params in a follow-up.

## Migration Plan

- Frontend-only change. Deploy updated `Filters.tsx` and `Dashboard.tsx`. No backend or DB changes. Rollback: revert frontend commit.

## Open Questions

- None blocking. Optional: add price presets (e.g. "Under €1", "Over €10") in a later iteration.
