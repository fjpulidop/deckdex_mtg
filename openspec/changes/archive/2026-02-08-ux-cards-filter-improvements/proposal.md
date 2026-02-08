## Why

The card table currently offers only name search and a single "All Rarities" dropdown. Users cannot filter by the other visible dimensions (Type, Set, Price), which limits discoverability and makes it harder to explore the collection. Improving the filter bar with filters for all table columns and clearer feedback (active filter chips, result count) will make filtering enjoyable and aligned with the existing dashboard UI guidelines.

## What Changes

- Add **Type** filter: dropdown (or equivalent) with distinct type values derived from the loaded card data; "All" by default.
- Add **Set** filter: dropdown with distinct set names from the data; "All" by default.
- Add **Price** filter: min/max range (two inputs or equivalent) to filter cards by price; optional quick presets (e.g. &lt; €1, &gt; €10) can be considered.
- Keep existing **name search** and **rarity** filter; ensure they work together with the new filters.
- Show **active filters as removable chips/tags** (e.g. "Rare ×", "Set: Dominaria ×", "€5 – €20 ×") so users can clear individual filters without resetting all.
- Show a **result count** (e.g. "Showing X cards" or "X results") that updates as filters change.
- Preserve **Clear Filters** to reset all filters (search + rarity + type + set + price) in one action.
- **Styling:** Use existing Tailwind patterns (rounded-lg, shadow, focus:ring-blue-500, gray scale) so the filter bar feels consistent with StatsCards, ActionButtons, and the rest of the dashboard. Optional subtle transitions when applying/clearing filters for a polished feel.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- **web-dashboard-ui**: Extend the "card filtering" requirements to include filtering by Type, Set, and Price (range); require visible active-filter chips and a result count; keep name search and rarity filter; retain Clear Filters and current styling guidelines.

## Impact

- **Frontend:** `frontend/src/components/Filters.tsx` (and possibly a small filter-state type/hook) will grow to support type, set, and price filters; UI for chips and result count (could live in Filters or Dashboard).
- **Frontend:** `frontend/src/pages/Dashboard.tsx` will hold filter state for type, set, and price and apply client-side filtering (same approach as current rarity filter) unless backend filtering is introduced later.
- **Backend:** No API contract change required for MVP; filtering remains client-side on the existing cards response (limit 1000). Optional future: add query params for type, set, price_min, price_max if collection size demands server-side filtering.
- **Spec:** `openspec/specs/web-dashboard-ui/spec.md` will receive a delta in this change to document the new filter requirements.
