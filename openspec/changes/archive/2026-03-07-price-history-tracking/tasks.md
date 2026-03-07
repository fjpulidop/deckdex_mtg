# Tasks: Price History Tracking

Ordered by layer dependency. Each task is atomic and independently verifiable.

---

## Group 1: Database

### Task 1 — [x] Migration: create price_history table

**File:** `migrations/014_price_history.sql`

Create the migration file with the following content:

```sql
-- DeckDex MTG: price_history table
-- Records every price observation per card for time-series tracking.

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

**Acceptance criteria:**
- File exists at `migrations/014_price_history.sql`.
- Applying it against an existing Postgres DB succeeds idempotently (`IF NOT EXISTS`).
- Table has correct column types, FK constraint with CASCADE, and composite index.
- Running it a second time does not error.

---

## Group 2: Core — Repository

### Task 2 — [x] Add abstract price history methods to CollectionRepository

**File:** `deckdex/storage/repository.py`

Add two methods to the `CollectionRepository` abstract base class, after `update_card_scryfall_id`:

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
) -> List[Dict[str, Any]]:
    """Return price history for card_id over the last `days` days.

    Returns list of dicts: [{"recorded_at": str (ISO 8601), "price": float, "source": str, "currency": str}]
    Ordered oldest-first. Empty list if no history or unsupported backend.
    """
    return []
```

**Acceptance criteria:**
- Both methods exist on `CollectionRepository` with correct signatures and no-op/empty-list defaults.
- Existing Google Sheets or mock repositories are unaffected (they inherit the no-ops).

### Task 3 — [x] Implement price history methods in PostgresCollectionRepository

**File:** `deckdex/storage/repository.py`

Add to `PostgresCollectionRepository`, after `update_card_scryfall_id`:

```python
def record_price_history(
    self,
    card_id: int,
    price: float,
    source: str = "scryfall",
    currency: str = "eur",
) -> None:
    from sqlalchemy import text
    engine = self._get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO price_history (card_id, price, source, currency)
                VALUES (:card_id, :price, :source, :currency)
            """),
            {"card_id": card_id, "price": price, "source": source, "currency": currency},
        )
        conn.commit()

def get_price_history(
    self,
    card_id: int,
    days: int = 90,
) -> List[Dict[str, Any]]:
    from sqlalchemy import text
    engine = self._get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"""
                SELECT recorded_at, price, source, currency
                FROM price_history
                WHERE card_id = :card_id
                  AND recorded_at >= NOW() AT TIME ZONE 'utc' - INTERVAL '{int(days)} days'
                ORDER BY recorded_at ASC
            """),
            {"card_id": card_id},
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

Note: `days` is formatted as `int(days)` in the f-string to prevent injection. It is always validated as int before this method is called.

**Acceptance criteria:**
- `record_price_history(card_id=1, price=3.50)` inserts a row with correct values.
- `get_price_history(card_id=1, days=90)` returns rows in ascending `recorded_at` order.
- `get_price_history` returns `[]` when no history exists.
- `get_price_history(card_id=1, days=7)` only returns rows within the last 7 days.

**Depends on:** Task 1 (table must exist), Task 2.

---

## Group 3: Core — Processor

### Task 4 — [x] Record price history in update_prices_data_repo

**File:** `deckdex/magic_card_processor.py`

In `update_prices_data_repo`, in the loop that processes batch results (around line 328), after calling `self.collection_repository.update(card_id, {"price_eur": new_price})`, add history recording:

```python
for card_id, _name, new_price in batch_results:
    self.collection_repository.update(card_id, {"price_eur": new_price})
    try:
        price_val = float(str(new_price).replace(",", "."))
        self.collection_repository.record_price_history(card_id, price_val)
    except (ValueError, TypeError):
        pass  # Non-numeric price — skip history entry
    total_prices_updated += 1
```

**Acceptance criteria:**
- After a price update run, `price_history` contains one row per updated card per run.
- Non-numeric values (e.g., `"N/A"`, `""`) do not cause errors and do not produce history rows.
- The `update()` call behavior is unchanged.

**Depends on:** Task 2, Task 3.

---

## Group 4: Backend — API

### Task 5 — [x] Add PriceHistoryPoint and PriceHistoryResponse Pydantic models

**File:** `backend/api/routes/cards.py`

Add after the existing `FilterOptions` model (around line 75):

```python
class PriceHistoryPoint(BaseModel):
    recorded_at: str
    price: float
    source: str
    currency: str

class PriceHistoryResponse(BaseModel):
    card_id: int
    currency: str
    points: List[PriceHistoryPoint]
```

**Acceptance criteria:**
- Models exist and are importable.
- `PriceHistoryResponse` with empty `points` list serializes correctly.

### Task 6 — [x] Add GET /api/cards/{id}/price-history endpoint

**File:** `backend/api/routes/cards.py`

Add the endpoint after `get_card_image` (around line 285) and BEFORE `get_card`. This order is critical — the catch-all `/{card_id_or_name}` must remain last.

```python
@router.get("/{id}/price-history", response_model=PriceHistoryResponse)
async def get_card_price_history(
    id: int,
    days: int = Query(default=90, ge=1, le=365),
    user_id: int = Depends(get_current_user_id),
):
    """
    Return price history for a card over the last `days` days (default: 90, max: 365).
    Points are ordered oldest-first for chart rendering.
    Returns empty points list (not an error) if card exists but has no history yet.
    Requires PostgreSQL. Returns 501 if DATABASE_URL is not set.
    """
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Price history requires PostgreSQL. Set DATABASE_URL.",
        )
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

**Acceptance criteria:**
- `GET /api/cards/42/price-history` returns 200 with `{ card_id: 42, currency: "eur", points: [] }` when card 42 has no history.
- Returns populated `points` after price updates have run.
- Returns 404 for a non-existent card id.
- Returns 501 when no `DATABASE_URL` is set.
- `?days=7` limits results to the last 7 days.
- `?days=0` returns 422 (FastAPI validation, ge=1).
- `?days=366` returns 422 (FastAPI validation, le=365).
- Route does not interfere with `GET /api/cards/42/image` or `GET /api/cards/42`.

**Depends on:** Task 5, Task 3.

---

## Group 5: Frontend

### Task 7 — [x] Add PriceHistory types to API client

**File:** `frontend/src/api/client.ts`

Add after the existing `JobHistoryItem` interface (around line 137):

```typescript
export interface PriceHistoryPoint {
  recorded_at: string;
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

Add to the `api` object after `getJobHistory`:

```typescript
getPriceHistory: async (cardId: number, days = 90): Promise<PriceHistoryResponse> => {
  const response = await apiFetch(`${API_BASE}/cards/${cardId}/price-history?days=${days}`);
  if (!response.ok) throw new Error('Failed to fetch price history');
  return response.json();
},
```

**Acceptance criteria:**
- Types compile without errors in strict TypeScript.
- `api.getPriceHistory(42)` calls `GET /api/cards/42/price-history?days=90`.
- `api.getPriceHistory(42, 30)` calls `GET /api/cards/42/price-history?days=30`.

### Task 8 — [x] Add usePriceHistory hook

**File:** `frontend/src/hooks/useApi.ts`

Add at the end of the file, after `useInsightExecute`:

```typescript
export function usePriceHistory(cardId: number | null | undefined, days = 90) {
  return useQuery<PriceHistoryResponse>({
    queryKey: ['price-history', cardId, days],
    queryFn: () => api.getPriceHistory(cardId!, days),
    enabled: cardId != null,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

Also add `PriceHistoryResponse` to the import from `'../api/client'` at line 3.

**Acceptance criteria:**
- Hook is exported and compiles.
- When `cardId` is null or undefined, the query does not fire (`enabled: false`).
- Returns `{ data, isLoading, error }` as expected by TanStack Query.

**Depends on:** Task 7.

### Task 9 — [x] Replace PriceChart with real recharts implementation

**File:** `frontend/src/components/PriceChart.tsx`

Replace the entire file with the recharts-based implementation:

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
      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Price History</div>
        <div className="h-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Price History</div>
        <div className="h-20 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded border border-dashed border-gray-300 dark:border-gray-600">
          No price history yet — run a price update to start tracking.
        </div>
      </div>
    );
  }

  const currencySymbol = currency === 'eur' ? '\u20AC' : '$';
  const chartData = points.map(p => ({
    date: formatDate(p.recorded_at),
    price: p.price,
  }));

  return (
    <div className="mt-4">
      <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Price History</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: 'currentColor' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: 'currentColor' }}
            tickFormatter={(v: number) => `${currencySymbol}${v}`}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value: number) => [`${currencySymbol}${value.toFixed(2)}`, 'Price']}
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

**Acceptance criteria:**
- File compiles with TypeScript strict mode (no `any`, proper types).
- Loading state renders a skeleton (pulse animation).
- Empty state renders informative message.
- With one or more points, renders a recharts LineChart.
- `recharts` is imported from the already-installed package — no `npm install` needed.

**Depends on:** Task 7.

### Task 10 — [x] Integrate PriceChart into CardDetailModal

**File:** `frontend/src/components/CardDetailModal.tsx`

1. Add imports at the top:
   ```typescript
   import { PriceChart } from './PriceChart';
   import { usePriceHistory } from '../hooks/useApi';
   ```

2. Inside the component body, after the existing hooks (after `const { t } = useTranslation();`), add:
   ```typescript
   const { data: priceHistoryData, isLoading: priceHistoryLoading } = usePriceHistory(cardId);
   ```

3. In the JSX, inside the `!isEditing` branch, after the `<div className="space-y-1 ...">` metadata block (the block containing set, rarity, price — ends around line 350), add:
   ```typescript
   <PriceChart
     points={priceHistoryData?.points ?? []}
     currency={priceHistoryData?.currency ?? 'eur'}
     isLoading={priceHistoryLoading}
   />
   ```
   The condition `cardId != null` is already guaranteed by context (the metadata block is inside the modal which always has a card).

**Acceptance criteria:**
- `CardDetailModal` renders without TypeScript errors.
- In view mode (not editing), the price chart section appears below the metadata block.
- In edit mode, the price chart is not rendered.
- Loading state visible while `usePriceHistory` fetches.
- Empty state visible for cards with no price history.
- Chart renders with data after price update runs have populated history.

**Depends on:** Task 8, Task 9.

---

## Group 6: Tests

### Task 11 — [x] Repository unit tests for price history

**File:** `tests/test_price_history_repository.py` (new file)

Write pytest tests covering:

1. `test_record_price_history_inserts_row`: After calling `record_price_history(card_id, 3.50)`, a row exists in `price_history` with correct values.
2. `test_get_price_history_empty`: `get_price_history(card_id)` returns `[]` when no rows exist.
3. `test_get_price_history_returns_points_oldest_first`: After inserting two rows at different times, returned list is ordered ascending by `recorded_at`.
4. `test_get_price_history_respects_days_window`: Rows older than `days` are excluded.
5. `test_record_price_history_cascade_delete`: Deleting a card removes its price history rows.

Use the existing Postgres test fixture pattern from other tests in `tests/`. If no Postgres fixture exists, use SQLite or mock the engine — match the existing test patterns.

**Acceptance criteria:**
- All 5 tests pass with `pytest tests/test_price_history_repository.py`.
- Tests do not depend on external services.

**Depends on:** Task 1, Task 2, Task 3.

### Task 12 — [x] API endpoint tests for price history

**File:** `tests/test_price_history_api.py` (new file)

Write pytest tests with FastAPI TestClient covering:

1. `test_get_price_history_empty`: Returns 200 with `{ points: [] }` for a card with no history.
2. `test_get_price_history_with_data`: Returns 200 with populated points after inserting history rows.
3. `test_get_price_history_404_unknown_card`: Returns 404 for a non-existent card id.
4. `test_get_price_history_days_param`: `?days=7` limits results correctly.
5. `test_get_price_history_days_validation`: `?days=0` returns 422; `?days=366` returns 422.

**Acceptance criteria:**
- All 5 tests pass with `pytest tests/test_price_history_api.py`.
- Tests use the FastAPI TestClient (follow patterns in existing route tests).

**Depends on:** Task 5, Task 6.
