# Price History

Per-card price observation tracking: every time a card's price is updated from Scryfall, a timestamped record is appended to `price_history`. The time-series is surfaced via a REST endpoint and rendered as a line chart in the card detail modal.

## Storage

Table: `price_history`

| Column       | Type             | Constraints                                |
|--------------|------------------|--------------------------------------------|
| id           | BIGSERIAL        | PRIMARY KEY                                |
| card_id      | BIGINT           | NOT NULL, REFERENCES cards(id) ON DELETE CASCADE |
| recorded_at  | TIMESTAMPTZ      | NOT NULL, DEFAULT NOW() AT TIME ZONE 'utc' |
| source       | TEXT             | NOT NULL, DEFAULT 'scryfall'               |
| currency     | TEXT             | NOT NULL, DEFAULT 'eur'                    |
| price        | NUMERIC(10, 2)   | NOT NULL                                   |

Index: `(card_id, recorded_at DESC)` for efficient per-card time-series queries.

## Recording

- A price history record is inserted whenever `magic_card_processor.update_prices_data_repo()` writes a new `price_eur` value to the `cards` table.
- Non-numeric prices (e.g., `"N/A"`, empty string) are skipped — no history entry is written.
- No deduplication: repeated identical prices are recorded. This preserves a complete time-series showing price stability.
- The base `CollectionRepository` interface exposes `record_price_history()` as a no-op default. Google Sheets mode silently skips recording.

## Retrieval

- `get_price_history(card_id, days=90)` returns all observations for a card within the last `days` days, ordered oldest-first.
- Default window: 90 days. Maximum window: 365 days (enforced at API layer).
- Result shape: list of `{ recorded_at: str (ISO 8601), price: float, source: str, currency: str }`.

## API

**Endpoint:** `GET /api/cards/{id}/price-history`

**Query params:**
- `days` (int, default 90, range 1–365): Time window in days.

**Response:**
```json
{
  "card_id": 42,
  "currency": "eur",
  "points": [
    { "recorded_at": "2026-01-01T12:00:00+00:00", "price": 3.50, "source": "scryfall", "currency": "eur" },
    { "recorded_at": "2026-01-08T12:00:00+00:00", "price": 4.00, "source": "scryfall", "currency": "eur" }
  ]
}
```

- Returns 404 if the card does not exist or does not belong to the requesting user.
- Returns 501 if PostgreSQL is not configured.
- Returns empty `points` array (not an error) if the card exists but has no history yet.

## Frontend

- `PriceChart` component (`frontend/src/components/PriceChart.tsx`) renders a recharts `LineChart` from price history points.
- Rendered inside `CardDetailModal` below the price/set/rarity metadata, visible in view mode (not edit mode).
- Loading state: skeleton animation matching chart dimensions.
- Empty state: text prompt explaining how to populate history ("Run a price update to start tracking").
- `usePriceHistory(cardId, days?)` hook in `frontend/src/hooks/useApi.ts` wraps the API call with TanStack Query (5-minute stale time).

## Constraints

- Price history is Postgres-only. The feature degrades gracefully when `DATABASE_URL` is not set: the API endpoint returns 501, the frontend shows the empty state.
- History is not backfilled on deployment. Data accumulates from the first price update run after migration 014 is applied.
- History records are deleted when their parent card is deleted (`ON DELETE CASCADE`).
