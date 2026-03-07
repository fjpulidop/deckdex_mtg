## Why

Every price update run silently overwrites `price_eur` in the `cards` table with no audit trail. Users have no way to see whether a card's value increased, declined, or held steady over time — historical context that is essential for collection management decisions. The data exists (Scryfall supplies it on every run) but is immediately discarded. `frontend/src/components/PriceChart.tsx` was pre-built as a placeholder with a "Coming Soon" label and hardcoded mock data, signaling original intent that was never fulfilled.

## What Changes

- Add a `price_history` table that persists every price observation per card with timestamp, source, and currency.
- Modify `magic_card_processor.py` to INSERT a `price_history` row alongside every `cards.price_eur` update.
- Add `GET /api/cards/{id}/price-history?days=90` endpoint returning time-series price data.
- Replace the dead `PriceChart.tsx` placeholder with a real recharts `LineChart` rendered inside `CardDetailModal`, showing the card's price over the last 90 days.
- Update data model and web-api-backend specs to reflect the new table and endpoint.

## Capabilities

### New Capabilities

- `price-history`: Per-card price history storage, retrieval API, and time-series chart visualization in the card detail modal.

### Modified Capabilities

- `data-model`: Add `price_history` table definition to the data model spec.
- `web-api-backend`: Add `GET /api/cards/{id}/price-history` endpoint specification.

## Impact

- **Database**: New migration `014_price_history.sql`. No changes to existing tables.
- **Core** (`deckdex/storage/repository.py`): New `PriceHistoryRepository` mixin with `record()` and `get_history()` on `PostgresCollectionRepository`.
- **Core** (`deckdex/magic_card_processor.py`): Insert price history row after each successful `price_eur` update in `update_prices_data_repo`.
- **Backend** (`backend/api/routes/cards.py`): New endpoint and Pydantic response model.
- **Frontend** (`frontend/src/api/client.ts`, `frontend/src/hooks/useApi.ts`): New `getPriceHistory` API function and `usePriceHistory` hook.
- **Frontend** (`frontend/src/components/PriceChart.tsx`): Complete replacement — real recharts LineChart replacing mock/placeholder.
- **Frontend** (`frontend/src/components/CardDetailModal.tsx`): Import and render `PriceChart` in the card detail view.
- **Dependencies**: `recharts` is already installed (`^3.7.0`); no new dependencies needed.
- **Tests**: New tests for repository methods and the API endpoint.

## Non-goals

- Collection-level value snapshots (daily aggregate across all cards) — valuable but a separate feature.
- Backfilling historical prices from before this migration — no Scryfall bulk history API exists; data starts accumulating from first run after deployment.
- Price alerts or notifications when a card crosses a threshold.
- Multi-currency support beyond EUR (the current tracking currency); USD fields exist in `cards` but are not surfaced in the UI yet.
