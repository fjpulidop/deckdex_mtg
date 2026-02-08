## Why

The dashboard shows Total Cards, Total Value, and Average Price at the top, but these stats are currently global (whole collection) and do not change when the user applies filters. Users expect these numbers to reflect the filtered set—and to be correct regardless of pagination or the 1000-card limit on the list. To guarantee correct, filter-aware stats independent of what is on screen, the backend must compute aggregates using the same filter criteria as the card list.

## What Changes

- **Backend:** Extend GET `/api/stats` to accept optional query parameters that mirror the collection filters (e.g. `search`, `rarity`, `type`, `set_name`, `price_min`, `price_max`). When provided, the backend returns `total_cards`, `total_value`, and `average_price` for the subset of the collection that matches those filters (same semantics as list endpoint). Without parameters, behavior remains unchanged (stats for entire collection).
- **Frontend:** When filters are applied, the dashboard calls the stats endpoint with the current filter values and displays the returned totals and average. The stats cards (Total Cards, Total Value, Avg) thus always show correct numbers for the active filter set, independent of pagination or list limit.

## Capabilities

### New Capabilities

None. This change extends existing API and UI behavior.

### Modified Capabilities

- **web-api-backend:** Stats endpoint SHALL accept optional filter query parameters and return aggregates computed over the filtered collection (same filter semantics as GET `/api/cards`). Cache key (if any) SHALL include filter params so filtered and unfiltered stats do not overwrite each other.
- **web-dashboard-ui:** Dashboard SHALL request stats with the current filter parameters (search, rarity, type, set, price range) and SHALL display the returned total_cards, total_value, and average_price in the stats cards so that the numbers reflect the filtered set and remain correct regardless of pagination or list limit.

## Impact

- **Backend:** Stats route and service layer (reuse or align with collection filter logic); cache key for stats if 30s cache is kept.
- **Frontend:** Stats fetch (e.g. `useStats`) must accept filter params and pass them to the API; Dashboard must pass current filter state into the stats hook so the displayed totals and average update when filters change.
