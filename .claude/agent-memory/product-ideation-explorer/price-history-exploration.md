# Price History Exploration

**Date:** 2026-03-07

## What Exists

### Data Model Spec
- `data-model.md` defines **PriceHistory** entity: `card_id, timestamp, source, currency, price`
- Relationship: Card 1:N PriceHistory
- Cards table already stores `price_eur`, `price_usd`, `price_usd_foil`, `last_price_update` columns (migration `001_cards_table.sql`)

### Price Update Infrastructure (fully functional)
- **Bulk update**: `POST /api/prices/update` -- triggers background job updating all cards via Scryfall
- **Single card update**: `POST /api/prices/update/{card_id}` -- per-card price refresh from card detail modal
- **Processor**: `magic_card_processor.py` has `update_prices_data_repo()` which iterates cards, fetches from Scryfall, and calls `repository.update(card_id, {"price_eur": new_price})` (line 329)
- **Scryfall service**: `scryfall_service.py` extracts `prices.eur` or `prices.usd` from Scryfall API responses
- **Repository**: `get_cards_for_price_update()` returns `(card_id, name, current_price_str)` tuples
- **WebSocket progress**: real-time job tracking works for both bulk and single-card updates
- **Job management**: price update jobs are tracked in-memory with WebSocket callbacks

### Frontend
- **PriceChart.tsx**: Exists but is a **complete placeholder** -- hardcoded mock data, "Coming Soon" message, dashed border placeholder box. Not imported/used anywhere in the app.
- **CardDetailModal.tsx**: Shows current price (EUR), has "Update Price" button triggering single-card update job. No price history display.
- **API client**: `triggerPriceUpdate()` and `triggerSingleCardPriceUpdate(cardId)` exist. No price history fetch endpoint.

### Archived Changes
- `2026-02-08-analytics-dashboard` proposal mentions PriceHistory: "Price history / time-series charts" explicitly deferred from analytics MVP (design.md line 14)
- Analytics dashboard proposal references PriceHistory as future data source

## What's Missing

### Critical Missing Pieces (Nothing exists)

1. **No `price_history` table** -- zero migrations create it. The spec defines PriceHistory but it was never implemented in schema.
2. **No history recording** -- `update_prices_data_repo()` overwrites `price_eur` in-place. Previous prices are permanently lost.
3. **No price history API endpoints** -- no `GET /api/cards/{id}/price-history` or similar.
4. **No price history repository methods** -- `repository.py` has zero references to `price_history`.
5. **No price history service** -- no dedicated service for querying/aggregating price data over time.
6. **PriceChart.tsx is unused** -- never imported in any page or component. Dead code with mock data.
7. **No charting library** -- frontend has no chart dependency (no recharts, chart.js, d3, etc.).
8. **No collection value history** -- total portfolio value over time is not tracked anywhere.

### Design Gaps
- Spec says PriceHistory has `source` field but current price updates only use Scryfall (no multi-source architecture)
- Spec says `currency` field but current system stores EUR/USD in separate columns (price_eur, price_usd) not as currency-tagged rows
- No retention policy defined -- how long to keep history? Every update? Daily snapshots?
- No aggregation strategy -- per-card history vs. collection-level value snapshots vs. both

## Improvement Ideas

| # | Idea | Description | Value (1-5) | Complexity (1-5) | Ratio |
|---|------|-------------|-------------|-------------------|-------|
| 1 | **price_history table + migration** | Create `price_history(id, card_id FK, price_eur, price_usd, recorded_at)` table. Simpler than spec's source/currency design -- matches actual usage pattern of EUR/USD columns. | 5 | 1 | 5.0 |
| 2 | **Record history on price update** | In `update_prices_data_repo()`, INSERT into price_history before UPDATE cards. One extra INSERT per card per update run. Minimal code change in processor. | 5 | 1 | 5.0 |
| 3 | **GET /api/cards/{id}/price-history endpoint** | Return price history for a card. Query params: `days=30\|90\|365`, `currency=eur\|usd`. Repository method + route + Pydantic model. | 4 | 2 | 2.0 |
| 4 | **Per-card price sparkline in CardDetailModal** | Small inline chart showing price trend in the card detail view. Lightweight -- could use a tiny SVG sparkline library (no heavyweight chart dep). | 4 | 2 | 2.0 |
| 5 | **Collection value snapshots table** | Separate `collection_value_snapshots(id, user_id, total_value, card_count, recorded_at)`. Computed after each bulk price update completes. Much cheaper to query for portfolio charts than aggregating all card histories. | 5 | 2 | 2.5 |
| 6 | **Collection value chart (replace PriceChart.tsx placeholder)** | Wire up PriceChart.tsx with real data from collection_value_snapshots. Add a charting library (recharts is React-native, ~45KB gzipped). Show on Dashboard or Analytics page. | 5 | 3 | 1.7 |
| 7 | **Price change alerts / "movers" panel** | After price update, show cards with biggest price changes (gainers/losers). Could be a dashboard widget. "Your Ragavan went from 45EUR to 62EUR since last update." | 4 | 3 | 1.3 |
| 8 | **Daily automatic price snapshots (cron/scheduler)** | Background scheduler that runs price updates daily and records history. Currently manual-only. Could use APScheduler or simple cron-like background task. | 3 | 3 | 1.0 |
| 9 | **Price history retention policy** | Auto-prune old price history (e.g., keep daily for 90 days, weekly for 1 year, monthly beyond). Prevents unbounded table growth for large collections. | 2 | 2 | 1.0 |
| 10 | **Multi-currency price display toggle** | Cards store price_eur and price_usd already. Let user toggle display currency in settings. Currently hardcoded to EUR throughout frontend. | 3 | 2 | 1.5 |
| 11 | **Price comparison across printings** | Show prices of the same card across different sets/printings. Helps budget players find cheapest version. Requires Scryfall "prints" API call. | 4 | 4 | 1.0 |
| 12 | **Deck value tracking over time** | Aggregate price history for cards in a deck to show deck value trend. Builds on ideas 1-2 + deck feature. | 3 | 3 | 1.0 |
| 13 | **Price history data export (CSV)** | Export price history for a card or entire collection as CSV. Useful for spreadsheet users doing their own analysis. | 2 | 1 | 2.0 |

## Recommended Priority

### Phase 1: Foundation (ideas 1, 2, 5) -- Small effort, massive unlock
These three are prerequisite for everything else and are all low complexity:
- **Migration 014**: Create `price_history` and `collection_value_snapshots` tables
- **Processor change**: One INSERT per card in `update_prices_data_repo()` loop (line 329 of `magic_card_processor.py`)
- **Snapshot after bulk update**: After `update_prices_async()` completes, compute and INSERT collection total

Once Phase 1 ships, data starts accumulating immediately. Every price update run from that point forward builds the historical dataset. This is the most time-sensitive work -- every day without it is lost history.

### Phase 2: API + Basic Visualization (ideas 3, 6)
- Add `GET /api/cards/{id}/price-history` and `GET /api/collection/value-history` endpoints
- Install recharts, replace PriceChart.tsx placeholder with real collection value chart
- Show on Dashboard page (where PriceChart was presumably intended to live)

### Phase 3: Card-level insights (ideas 4, 7, 10)
- Sparkline in CardDetailModal
- Price movers widget on Dashboard
- Currency toggle in settings

### Phase 4: Advanced (ideas 8, 9, 11, 12)
- Automatic scheduling, retention, cross-printing comparison, deck value tracking

## Key Technical Notes

- **price_eur stored as TEXT** -- this is a persistent issue across the codebase. Repository uses `CASE WHEN price_eur ~ '^[0-9]+\.?[0-9]*$' THEN CAST(price_eur AS numeric)` everywhere. The price_history table should use `NUMERIC(10,2)` from day one to avoid inheriting this tech debt.
- **Scryfall rate limit**: 10 requests/second. Bulk updates already respect this. History recording is local-only (no extra API calls).
- **Storage growth**: ~1 row per card per update run. 1000-card collection with weekly updates = ~52K rows/year. Negligible for Postgres.
- **Google Sheets path**: Price history would be Postgres-only. Sheets users don't get history (acceptable -- Sheets is already the limited-feature path).
- **PriceChart.tsx location**: Component exists but is not imported anywhere. Likely intended for Dashboard page but was never wired up.

## Competitive Context

- **MTGGoldfish**: Gold standard for price history -- shows 6-month/1-year/2-year charts for every card. DeckDex cannot compete on data depth (they scrape multiple sources daily) but can offer personalized collection value tracking that MTGGoldfish does not.
- **TCGPlayer**: Shows price history for individual cards but not collection-level portfolio tracking.
- **Moxfield**: Shows current prices for decks but no price history or value tracking over time.
- **Archidekt**: Basic current price display, no history.
- **Differentiation opportunity**: "How has YOUR collection's value changed?" is something none of the deck-building platforms do well. MTGGoldfish tracks market prices, not personal portfolio value.
