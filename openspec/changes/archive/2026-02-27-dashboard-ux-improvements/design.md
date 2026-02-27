## Context

`Dashboard.tsx` owns all filter state in local `useState` (search, rarity, type, setFilter, priceMin, priceMax). It fetches all cards with `useCards({ limit: 10000 })` — the full dataset is already available in memory. Card images are served by the backend at `/api/cards/{id}/image` (Scryfall-cached), exposed via `api.getCardImageUrl(id: number)`. `react-router-dom` is already installed and used for routing; `useSearchParams` is available.

## Goals / Non-Goals

**Goals:**
- Show the top 5 cards by price in a visual strip between `StatsCards` and `Filters`, clicking a card opens its `CardDetailModal`
- Filter state (search, rarity, type, set, priceMin, priceMax) is reflected in the URL and restored on page load/refresh
- Clear Filters resets both local state and URL params

**Non-Goals:**
- No backend changes of any kind
- No pagination or sorting controls within the top-5 widget
- No animation or carousel for the top-5 strip
- Top-5 widget does not respond to active filters (always shows top 5 of the full collection)

## Decisions

### D1: Top 5 derived client-side from already-loaded data

**Decision**: `TopValueCards` receives the `cards` array (already fetched by Dashboard) as a prop, sorts by `parseFloat(price)` descending, and takes the first 5. No additional API call.

**Rationale**: Dashboard already fetches `limit: 10000` cards. Deriving top 5 client-side is O(n) and instant. A dedicated endpoint would add complexity for no benefit.

**Alternative considered**: New `GET /api/stats/top-cards` endpoint. Rejected: overkill; the data is already in the client.

### D2: Top-5 widget ignores active filters

**Decision**: The widget always shows top 5 of the full unfiltered dataset.

**Rationale**: The widget's value is "what are my most valuable cards" — a collection-level truth. Filtering it would make it confusing (e.g. applying a price filter and seeing the widget shift). `StatsCards` already reflects filtered totals; the top-5 widget is complementary context.

### D3: URL sync via `useSearchParams` (react-router)

**Decision**: Replace `useState` for each filter with a pattern that reads initial values from `useSearchParams` and syncs changes back via `setSearchParams`. Use `replace: true` on every update so the browser history does not accumulate filter changes.

**Rationale**: `useSearchParams` from `react-router-dom` (already installed) is the idiomatic solution. No extra library needed. `replace: true` avoids polluting the Back button history with every keystroke.

**Search debounce**: The URL is updated on the debounce resolution (300ms), not on every keystroke, to avoid excessive history entries and URL churn.

### D4: Card image in TopValueCards uses existing `api.getCardImageUrl`

**Decision**: Each card in the top-5 strip uses `api.getCardImageUrl(card.id)` as `<img src>`. Show a neutral placeholder if `card.id` is undefined or image fails to load.

**Rationale**: Reuses the existing Scryfall-cached image endpoint. No new infrastructure.

### D5: Cards with no price are excluded from top-5

**Decision**: Cards where `price` is undefined, null, empty string, or non-numeric are excluded from the top-5 ranking.

**Rationale**: A card with no price cannot be ranked. Showing it with "€0" would be misleading.

## Risks / Trade-offs

- **URL with many params is ugly**: Acceptable — params only appear when filters are active; with no filters the URL stays clean (`/dashboard`)
- **Top-5 requires image loads**: Each card makes a backend request to Scryfall-cache endpoint. With 5 images this is negligible. Images are already cached from previous loads in `CardDetailModal`
- **Stale top-5 after price update**: After a price update job completes, Dashboard invalidates the cards query. The top-5 widget re-derives from the fresh data automatically since it is derived from the same `cards` prop

## Migration Plan

1. Create `TopValueCards.tsx` component
2. Update `Dashboard.tsx` to use `useSearchParams` and pass `cards` to `TopValueCards`
