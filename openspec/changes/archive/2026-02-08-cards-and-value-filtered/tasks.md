## 1. Backend – filter params and stats logic

- [x] 1.1 Add optional query parameters to GET `/api/stats`: `search`, `rarity`, `type`, `set_name`, `price_min`, `price_max` (all optional; same names as design).
- [x] 1.2 Implement collection filter logic (search: name contains case-insensitive; rarity, type, set_name: exact match; price_min/price_max: inclusive range using existing `parse_price`). Apply to collection before calling `calculate_stats`.
- [x] 1.3 Key the stats cache by a canonical representation of the filter params (e.g. tuple or sorted query string). Store one cache entry per distinct param set; keep 30s TTL per entry. Ensure `clear_stats_cache()` clears all entries (or document that it clears only the “unfiltered” entry if that’s the chosen behavior).
- [x] 1.4 When no filter params are provided, preserve current behavior: single “unfiltered” cache entry and return stats for full collection.

## 2. Frontend – stats request with filters

- [x] 2.1 Extend API client: `getStats(params?: { search?, rarity?, type?, set_name?, price_min?, price_max? })` building query string from present params; retain existing response type.
- [x] 2.2 Change `useStats` to accept an optional filter object (search, rarity, type, set, priceMin, priceMax) and pass it to `getStats`; include the filter object in the TanStack Query key so stats refetch when filters change.
- [x] 2.3 In Dashboard, pass current filter state (search, rarity, type, setFilter, priceMin, priceMax) into `useStats`. Ensure StatsCards receives and displays the returned total_cards, total_value, average_price (no change to layout; only data source is filter-aware).

## 3. Verification

- [x] 3.1 Manually verify: with no filters, stats match current global totals; with filters applied, Total Cards / Total Value / Avg update and match the filtered set (and are independent of table pagination/limit).
- [x] 3.2 Confirm cache: same filter params within 30s return cached stats; changing a filter yields new request and updated numbers.
