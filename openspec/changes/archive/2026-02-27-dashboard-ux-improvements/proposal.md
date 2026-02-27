## Why

The dashboard is purely informational today: two stat cards plus a filterable table. Two small but impactful improvements make it noticeably better for collectors:

1. **Top 5 most valuable cards** — collectors want at a glance "what are my crown jewels". The data is already loaded (Dashboard fetches all cards); deriving the top 5 client-side costs nothing. The widget gives the dashboard visual richness and immediate collector value.

2. **URL-persistent filters** — applying a filter (e.g. "Mythic, > €20") and then refreshing the page loses all state. Bookmarking a filtered view is impossible. Sharing a search with someone requires re-explaining the filters. Persisting filters to URL params solves all of this with a minimal change confined to `Dashboard.tsx`.

## What Changes

- New `TopValueCards` component renders the top 5 cards by price as a visual strip with card image, name, set, and price. Placed below `StatsCards` in the Dashboard.
- `Dashboard.tsx` reads initial filter state from `URLSearchParams` on mount and writes filter changes back to the URL using `useSearchParams` (react-router). Clear Filters also clears the URL.
- No backend changes — all data is already available from existing API calls.

## Capabilities

### New Capabilities

- `top-value-cards-widget`: A visual strip showing the collector's 5 most valuable cards (by current price), with card image, name, set, rarity badge, and price. Derived from the already-loaded cards list — no extra API call.

### Modified Capabilities

- `filters-ui`: Filter state (search, rarity, type, set, priceMin, priceMax) is now reflected in the URL as query parameters and initialized from them on page load. Shareable and bookmark-friendly.

## Impact

- **Frontend only**: `Dashboard.tsx`, new `TopValueCards.tsx` component
- **No backend changes**
- **No new dependencies**: `useSearchParams` is already available from `react-router-dom`
