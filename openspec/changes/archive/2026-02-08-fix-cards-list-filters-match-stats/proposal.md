## Why

When the user filters the collection by set (e.g. "Adventures in the Forgotten Realms"), the stats cards correctly show 4 cards and €1.78 total value because GET `/api/stats` applies filters server-side. The card table, however, only shows one card (e.g. Feign Death, €1.14) because the list is fetched with only `search` and `limit`; the frontend then filters that subset client-side. So the list and the stats use different data: stats see the full filtered set, the table only sees the filtered subset of the first N cards returned. This mismatch confuses users and is incorrect. The list endpoint must apply the same filters as the stats endpoint so the table and the stats always match.

## What Changes

- **Backend:** Extend GET `/api/cards` to accept the same optional filter query parameters as GET `/api/stats`: `search`, `rarity`, `type`, `set_name`, `price_min`, `price_max`. Apply these filters to the collection **before** pagination (limit/offset), using the same semantics as stats (name contains, exact match for rarity/type/set_name, price range inclusive). Without filter params, behavior is unchanged.
- **Frontend:** When fetching cards for the dashboard, pass the current filter values (search, rarity, type, set, price range) to GET `/api/cards`. Use the API response as the list to display; do not apply the same filters again client-side (or keep client-side filter as no-op for consistency). Stats and list will then always reflect the same subset.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- **web-api-backend:** GET `/api/cards` SHALL accept optional query parameters `rarity`, `type`, `set_name`, `price_min`, `price_max` (in addition to existing `limit`, `offset`, `search`). When provided, the system SHALL filter the collection using the same semantics as GET `/api/stats` (name contains search, exact match for rarity/type/set_name, price in [price_min, price_max]) and SHALL apply pagination (limit/offset) to the filtered result so that the returned list and the stats for the same filters are consistent.
- **web-dashboard-ui:** The dashboard SHALL request GET `/api/cards` with the current filter parameters (search, rarity, type, set, price_min, price_max) so that the displayed card list matches the subset used for Total Cards, Total Value, and Average Price. The list SHALL be the API response (no redundant client-side filter that could cause mismatch).

## Impact

- **Backend:** Cards route (`GET /api/cards`): add filter query params; reuse or share filter logic with stats (e.g. shared filter module or same semantics).
- **Frontend:** `useCards` and API client `getCards`: accept and pass filter params; Dashboard: pass current filter state into the cards fetch so the list is pre-filtered by the API.
