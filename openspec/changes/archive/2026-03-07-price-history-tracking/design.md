# Design: Price History Tracking

## Overview

This design adds end-to-end price history tracking: a new `price_history` table captures every price observation on update, a repository layer surfaces it via a clean interface, a FastAPI endpoint exposes it to the UI, and the card detail modal renders it as an interactive recharts line chart.

The implementation is additive-only — no existing tables, columns, or endpoints are modified. The price history table is strictly append-only (INSERT only, no UPDATE/DELETE by application code).

---

## Layer 1: Database — Migration 014

**File:** `migrations/014_price_history.sql`

```sql
CREATE TABLE IF NOT EXISTS price_history (
    id          BIGSERIAL PRIMARY KEY,
    card_id     BIGINT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    source      TEXT NOT NULL DEFAULT 'scryfall',
    currency    TEXT NOT NULL DEFAULT 'eur',
    price       NUMERIC(10, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_price_history_card_id_recorded_at
    ON price_history (card_id, recorded_at DESC);
```

Design decisions:
- `NUMERIC(10, 2)`: Exact decimal type, not TEXT. Avoids the current `price_eur TEXT` anti-pattern. 10 digits total, 2 decimal places — more than sufficient for card prices (max ~€10,000 in practice).
- `ON DELETE CASCADE`: When a card is deleted from the collection, its history is also deleted. This preserves referential integrity without orphaned rows.
- `REFERENCES cards(id)`: Enforces FK at DB level.
- Composite index on `(card_id, recorded_at DESC)`: The primary access pattern is "give me the history for card X, most recent first." This index covers that pattern without a full scan.
- No `user_id` column: History belongs to a card, and cards already carry `user_id`. Querying `price_history JOIN cards` with a `cards.user_id` filter is sufficient for user-scoped access. Adding `user_id` to `price_history` would be denormalization.
- `source` defaults to `'scryfall'` since that is the only current source. Future sources (e.g., TCGPlayer) can use different values without a schema change.

---

## Layer 2: Core — Repository

**File:** `deckdex/storage/repository.py`

Add two methods to `CollectionRepository` (abstract base, with no-op defaults) and implement them in `PostgresCollectionRepository`.

### Abstract interface additions

```python
def record_price_history(
    self,
    card_id: int,
    price: float,
    source: str = "scryfall",
    currency: str = "eur",
) -> None:
    """Insert a price observation into price_history. No-op for non-Postgres repos."""
    pass

def get_price_history(
    self,
    card_id: int,
    days: int = 90,
) -> list[dict]:
    """Return price history for card_id over the last `days` days.

    Returns list of dicts: [{"recorded_at": str (ISO), "price": float, "source": str, "currency": str}]
    Ordered oldest-first for chart rendering. Empty list if no history.
    """
    return []
```

### PostgresCollectionRepository implementation

```python
def record_price_history(self, card_id, price, source="scryfall", currency="eur"):
    from sqlalchemy import text
    engine = self._get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO price_history (card_id, price, source, currency)
                VALUES (:card_id, :price, :source, :currency)
            """),
            {"card_id": card_id, "price": float(price), "source": source, "currency": currency},
        )
        conn.commit()

def get_price_history(self, card_id, days=90):
    from sqlalchemy import text
    engine = self._get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT recorded_at, price, source, currency
                FROM price_history
                WHERE card_id = :card_id
                  AND recorded_at >= NOW() AT TIME ZONE 'utc' - INTERVAL ':days days'
                ORDER BY recorded_at ASC
            """),
            {"card_id": card_id, "days": days},
        ).fetchall()
    return [
        {
            "recorded_at": row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
            "price": float(row[1]),
            "source": row[2],
            "currency": row[3],
        }
        for row in rows
    ]
```

Note on the INTERVAL parameter: SQLAlchemy text() does not support parameterized intervals directly in all drivers. Use Python string formatting for the integer `days` value (safe since it is validated as int in the route layer before reaching the repository):

```python
text(f"""
    SELECT recorded_at, price, source, currency
    FROM price_history
    WHERE card_id = :card_id
      AND recorded_at >= NOW() AT TIME ZONE 'utc' - INTERVAL '{days} days'
    ORDER BY recorded_at ASC
""")
```

`days` is validated as `int` in the FastAPI route (Query param with `ge=1, le=365`), so this interpolation is safe from injection.

---

## Layer 3: Core — Processor

**File:** `deckdex/magic_card_processor.py`

**Method:** `update_prices_data_repo` (line ~328)

Current code:
```python
for card_id, _name, new_price in batch_results:
    self.collection_repository.update(card_id, {"price_eur": new_price})
    total_prices_updated += 1
```

Change to:
```python
for card_id, _name, new_price in batch_results:
    self.collection_repository.update(card_id, {"price_eur": new_price})
    # Record price history — safe even if price_history table doesn't exist yet
    try:
        price_val = float(str(new_price).replace(",", "."))
        self.collection_repository.record_price_history(card_id, price_val)
    except (ValueError, TypeError):
        pass  # Non-numeric price (e.g. "N/A") — skip history entry
    total_prices_updated += 1
```

Design decisions:
- Wrapped in `try/except`: If `new_price` is non-numeric (e.g., `"N/A"`, empty string), we skip recording history. We do NOT fail the price update for this.
- The `record_price_history` call is outside the ThreadPoolExecutor — it happens in the main thread after batch futures resolve. This avoids connection pool pressure from concurrent history inserts.
- No deduplication: If a price hasn't changed, we still record it. This gives a complete time-series that shows price stability — useful for the chart. If storage becomes a concern, a dedup policy can be added later.

---

## Layer 4: Backend — API Endpoint

**File:** `backend/api/routes/cards.py`

Add after the existing `get_card_image` endpoint and before `get_card`:

### Pydantic models

```python
class PriceHistoryPoint(BaseModel):
    recorded_at: str   # ISO 8601 timestamp
    price: float
    source: str
    currency: str

class PriceHistoryResponse(BaseModel):
    card_id: int
    currency: str
    points: list[PriceHistoryPoint]
```

### Endpoint

```python
@router.get("/{id}/price-history", response_model=PriceHistoryResponse)
async def get_price_history(
    id: int,
    days: int = Query(default=90, ge=1, le=365),
    user_id: int = Depends(get_current_user_id),
):
    """
    Return price history for a card over the last `days` days (default: 90).
    Requires PostgreSQL. Returns empty points list if no history exists yet.
    Points are ordered oldest-first for direct use in chart rendering.
    """
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Price history requires PostgreSQL. Set DATABASE_URL.",
        )
    # Verify card exists and belongs to user
    card = repo.get_card_by_id(id, user_id=user_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Card id {id} not found")
    try:
        points = repo.get_price_history(id, days=days)
        return PriceHistoryResponse(
            card_id=id,
            currency="eur",
            points=[PriceHistoryPoint(**p) for p in points],
        )
    except Exception as e:
        logger.error("Error fetching price history for card %s: %s", id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch price history")
```

**Route ordering**: The new endpoint is `/{id}/price-history` where `id` is an int path segment. The existing `/{card_id_or_name}` catch-all route uses a string. FastAPI matches more specific paths first, so `/{id}/price-history` must be registered BEFORE `/{card_id_or_name}`. This is already true for `/{id}/image` — follow the same placement.

---

## Layer 5: Frontend

### 5a. API client

**File:** `frontend/src/api/client.ts`

Add interface and method to the `api` object:

```typescript
export interface PriceHistoryPoint {
  recorded_at: string;  // ISO 8601
  price: number;
  source: string;
  currency: string;
}

export interface PriceHistoryResponse {
  card_id: number;
  currency: string;
  points: PriceHistoryPoint[];
}
```

```typescript
getPriceHistory: async (cardId: number, days = 90): Promise<PriceHistoryResponse> => {
  const response = await apiFetch(`${API_BASE}/cards/${cardId}/price-history?days=${days}`);
  if (!response.ok) throw new Error('Failed to fetch price history');
  return response.json();
},
```

### 5b. Hook

**File:** `frontend/src/hooks/useApi.ts`

```typescript
export function usePriceHistory(cardId: number | null | undefined, days = 90) {
  return useQuery<PriceHistoryResponse>({
    queryKey: ['price-history', cardId, days],
    queryFn: () => api.getPriceHistory(cardId!, days),
    enabled: cardId != null,
    staleTime: 5 * 60 * 1000, // 5 minutes — history does not change frequently
  });
}
```

### 5c. PriceChart component

**File:** `frontend/src/components/PriceChart.tsx`

Complete replacement. The existing file is dead code (never imported, mock data, "Coming Soon" label).

```typescript
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { PriceHistoryPoint } from '../api/client';

interface PriceChartProps {
  points: PriceHistoryPoint[];
  currency?: string;
  isLoading?: boolean;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function PriceChart({ points, currency = 'eur', isLoading = false }: PriceChartProps) {
  if (isLoading) {
    return (
      <div className="h-48 flex items-center justify-center">
        <div className="w-full h-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
        No price history yet. Run a price update to start tracking.
      </div>
    );
  }

  const currencySymbol = currency === 'eur' ? '€' : '$';
  const chartData = points.map(p => ({
    date: formatDate(p.recorded_at),
    price: p.price,
  }));

  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
        Price History
      </h3>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-gray-200 dark:text-gray-700" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 10 }}
            tickFormatter={v => `${currencySymbol}${v}`}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value: number) => [`${currencySymbol}${value.toFixed(2)}`, 'Price']}
            labelStyle={{ color: '#374151' }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

Design decisions:
- `recharts` is already a dependency (`^3.7.0`). No new packages needed.
- Height is 160px — compact enough to sit below the card detail text without dominating the modal.
- `dot={false}` on the Line: avoids visual clutter with many data points (daily for 90 days = 90 dots).
- `ResponsiveContainer` handles modal width changes.
- Empty state is informative: tells users what to do, not just "no data."

### 5d. CardDetailModal integration

**File:** `frontend/src/components/CardDetailModal.tsx`

In the view mode (non-editing) section, after the price/set/rarity metadata block, add the `PriceChart`. The chart is only shown when the card has an id (Postgres-backed) and is NOT in edit mode.

```typescript
// Add import at top:
import { PriceChart } from './PriceChart';
import { usePriceHistory } from '../hooks/useApi';

// Inside the component, after existing hooks:
const { data: priceHistoryData, isLoading: priceHistoryLoading } = usePriceHistory(cardId);

// In the JSX, after the metadata <div className="space-y-1 ..."> block, inside the !isEditing branch:
{cardId != null && (
  <PriceChart
    points={priceHistoryData?.points ?? []}
    currency={priceHistoryData?.currency ?? 'eur'}
    isLoading={priceHistoryLoading}
  />
)}
```

The modal layout is `flex-col md:flex-row` with `overflow-y-auto` on the right panel — the chart fits naturally in the scrollable right column below the existing metadata.

---

## Threading and Concurrency Notes

- `record_price_history` is called from the main thread in `update_prices_data_repo` after batch futures complete. It uses the SQLAlchemy connection pool via `_get_engine()`, which is safe for concurrent access.
- Each call opens and commits its own connection — no transactions span multiple calls.
- The base class no-op default means Google Sheets mode silently skips history recording. This is correct behavior — Sheets mode has no `price_history` table.

---

## Migration Safety

Migration 014 is backward-compatible. Deploying it against an existing database:
1. Creates `price_history` table (IF NOT EXISTS).
2. Creates composite index.
3. No data migrations or column changes to `cards`.

History accumulates from the first price update run after deployment. There is no backfill.
