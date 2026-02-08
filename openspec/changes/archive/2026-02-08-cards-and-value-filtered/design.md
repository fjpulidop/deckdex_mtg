## Context

The dashboard displays Total Cards, Total Value, and Average Price from GET `/api/stats`, which currently returns aggregates over the full collection with no query parameters. Filtering (search, rarity, type, set, price range) is applied client-side to the list returned by GET `/api/cards` (limit 1000). As a result, the stats do not change when the user applies filters, and any future pagination would not affect the requirement that the numbers be correct for the filtered set. The backend uses in-memory collection (e.g. `get_cached_collection()`) and applies search in the cards route; stats are computed from the full collection and cached with a single global key (30s TTL).

## Goals / Non-Goals

**Goals:**

- Stats (total_cards, total_value, average_price) reflect the subset of the collection that matches the current dashboard filters.
- Stats are computed server-side so they remain correct regardless of list limit or pagination.
- No breaking change: when no filter params are sent, behavior equals current (stats for entire collection).

**Non-Goals:**

- Changing GET `/api/cards` to accept rarity/type/set/price params or server-side pagination of filtered results (can be a follow-up).
- Persisting or exposing filter state in the URL (optional later improvement).

## Decisions

### 1. Stats endpoint accepts optional filter query parameters

- **Decision:** GET `/api/stats` accepts optional query params: `search`, `rarity`, `type`, `set_name`, `price_min`, `price_max`. Same semantics as the frontend filters: name contains search (case-insensitive), exact match for rarity/type/set_name, numeric price range inclusive. Price parsing and exclusion of invalid/N/A prices reuse existing stats logic.
- **Rationale:** Single endpoint keeps the API simple; optional params preserve backward compatibility. Aligning param names and semantics with the frontend avoids mapping bugs.
- **Alternative:** Separate endpoint like GET `/api/stats/filtered` with a body or long query string was rejected to keep one stats contract.

### 2. Filtering applied in stats route on the same collection source

- **Decision:** Stats route continues to use the same collection source (e.g. `get_cached_collection()`). After loading the collection, apply the same filter logic (search, rarity, type, set_name, price_min, price_max) in Python before calling `calculate_stats(filtered_list)`. Reuse the same `parse_price` (or shared helper) used for stats so totals and average are consistent.
- **Rationale:** No new data path; behavior stays consistent with how cards are conceptually filtered in the UI. Avoids duplicating filter logic in multiple places long-term by centralizing in a shared helper used by both stats and (if later added) cards list.

### 3. Stats cache key includes filter parameters

- **Decision:** Cache is keyed by a canonical representation of the query params (e.g. normalized string or tuple: search, rarity, type, set_name, price_min, price_max). Unfiltered request and each distinct filter combination have separate cache entries. TTL (e.g. 30s) per entry unchanged.
- **Rationale:** Prevents unfiltered stats from being returned for a filtered request (and vice versa). Cache size is bounded by distinct requests in the TTL window.
- **Alternative:** No cache for filtered requests would be correct but increase load under heavy filter usage; a single global cache was rejected because it would be wrong for any filtered request.

### 4. Frontend passes current filter state into the stats request

- **Decision:** The hook that fetches stats (e.g. `useStats`) accepts an object of current filter values (search, rarity, type, set, priceMin, priceMax). Dashboard passes the same state it uses for the filter bar. GET `/api/stats` is called with the corresponding query params; the returned total_cards, total_value, average_price are displayed in the existing stats cards.
- **Rationale:** One source of truth for “current filters”; stats always match what the user sees as the active filter set. No new UI components required.

## Risks / Trade-offs

- **Cache growth:** Many unique filter combinations in a short window could create many cache entries. Mitigation: keep TTL at 30s and optionally cap cache size (e.g. LRU) if needed later.
- **List vs stats source mismatch:** If GET `/api/cards` is not extended with the same filters, the table can show a subset (e.g. first 1000 by search, then client-filtered) while stats show the full filtered count. Mitigation: acceptable for this change; a follow-up can add server-side filters to the cards list and pagination for full consistency.
- **Price parsing consistency:** Stats and any future server-side price filtering must use the same `parse_price` logic. Mitigation: single shared helper used by stats (and cards route if filters are added there).
