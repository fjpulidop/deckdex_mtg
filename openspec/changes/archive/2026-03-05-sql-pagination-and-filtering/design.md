## Design: SQL-Level Filtering, Aggregation, and Paginated API Responses

### Architecture Decision: Dual Path

Keep the Python-in-memory path for Google Sheets compatibility. Optimize only the Postgres path. Detection: if `get_collection_repo()` returns a non-None value, use SQL path.

---

### A. Cache User Isolation Fix

**File**: `backend/api/dependencies.py`

Change `_collection_cache` from a single dict to a per-user dict:

```python
# Before
_collection_cache = {'data': None, 'timestamp': None, 'ttl': 30}

# After
_collection_cache: dict[int, dict] = {}  # keyed by user_id
```

`get_cached_collection(user_id)` reads from `_collection_cache[user_id]` and `clear_collection_cache()` clears all entries (or specific user if user_id passed).

---

### B. Repository: SQL-Level Filtering

**File**: `deckdex/storage/repository.py`

Add two new methods to `PostgresCollectionRepository`:

**`get_cards_filtered(user_id, filters, limit, offset) -> tuple[list, int]`**

Uses `SELECT COUNT(*) OVER() as total_count, * FROM cards WHERE <dynamic> ORDER BY created_at DESC LIMIT :limit OFFSET :offset`. Window function returns total in same query — no second COUNT(*) query needed.

Filter → SQL clause mapping:
- `search` → `LOWER(name) LIKE :search` (prefix `%` suffix `%`)
- `rarity` → `LOWER(rarity) = :rarity`
- `type_` → `LOWER(type_line) LIKE :type` (contains)
- `color_identity` → text LIKE matching (keep simple, JSONB not guaranteed)
- `set_name` → `set_name = :set_name` (exact)
- `price_min` → `price_eur >= :price_min`
- `price_max` → `price_eur <= :price_max`
- `cmc` → special: `"7+"` → `cmc >= 7`, `"Unknown"` → `cmc IS NULL`, else `FLOOR(cmc) = :cmc`

All parameters are bound values (no string interpolation) — SQL injection safe.

**`get_cards_stats(user_id, filters) -> dict`**

```sql
SELECT
  COALESCE(SUM(quantity), 0) as total_cards,
  COALESCE(SUM(price_eur * quantity), 0) as total_value,
  CASE WHEN SUM(CASE WHEN price_eur IS NOT NULL THEN quantity ELSE 0 END) > 0
       THEN SUM(price_eur * quantity) / SUM(CASE WHEN price_eur IS NOT NULL THEN quantity ELSE 0 END)
       ELSE 0 END as average_price
FROM cards WHERE <dynamic filters>
```

**`get_cards_analytics(user_id, filters, dimension, limit) -> list[dict]`**

Dimension → SQL:
- `rarity` → `SELECT COALESCE(rarity, 'Unknown') as label, SUM(quantity) as count FROM cards WHERE ... GROUP BY rarity ORDER BY count DESC`
- `color_identity` → same but `color_identity`
- `set_name` → same with LIMIT for top-N
- `type_line` → uses CASE expression to extract primary type (no regex in SQL; use WHERE type_line LIKE patterns)
- `cmc` → bucket in SQL: `CASE WHEN cmc IS NULL THEN 'Unknown' WHEN cmc >= 7 THEN '7+' ELSE FLOOR(cmc)::text END`

For type distribution: delegate primary type extraction to Python (one query, in-memory aggregation of ~8 type categories is fast and avoids complex SQL CASE chains).

---

### C. Cards Route: Paginated Response

**File**: `backend/api/routes/cards.py`

New Pydantic response model:
```python
class CardListResponse(BaseModel):
    items: List[Card]
    total: int
    limit: int
    offset: int
```

`GET /api/cards/` returns `CardListResponse` instead of `List[Card]`.

For Postgres path: call `repo.get_cards_filtered()` directly (bypasses collection cache).
For Sheets path: call `get_cached_collection()` + `filter_collection()` + Python slice, then wrap in `CardListResponse`.

New endpoint: `GET /api/cards/filter-options`
```python
class FilterOptions(BaseModel):
    types: List[str]
    sets: List[str]
```
Returns `SELECT DISTINCT type_line FROM cards WHERE user_id = :uid ORDER BY type_line` and same for set_name. For Sheets: derive from cached collection.

**Route ordering**: `/filter-options` must be registered BEFORE `/{card_id_or_name}` to avoid path conflict.

---

### D. Stats Route: SQL Aggregation

**File**: `backend/api/routes/stats.py`

For Postgres path: call `repo.get_cards_stats(user_id, filters)` → single SQL query.
For Sheets path: keep existing `get_cached_collection() + filter_collection() + calculate_stats()` path.

Keep the `_stats_cache` but key it by `(user_id, *filter_params)`.

---

### E. Analytics Route: SQL GROUP BY

**File**: `backend/api/routes/analytics.py`

For Postgres path: call `repo.get_cards_analytics(user_id, filters, dimension)`.
For Sheets path: keep existing Python Counter path.

- `rarity`, `color_identity`, `set_name`: pure SQL GROUP BY
- `cmc`: SQL CASE bucketing
- `type`: SQL query + Python primary-type extraction (avoids complex SQL)

Keep `_analytics_cache` keyed by `(user_id, endpoint, *filter_params)`.

---

### F. Frontend Updates

**`api/client.ts`**:
- Add `CardListResponse` interface: `{ items: Card[]; total: number; limit: number; offset: number }`
- Change `getCards()` return type to `Promise<CardListResponse>`
- Add `getFilterOptions()` returning `Promise<{ types: string[]; sets: string[] }>`

**`hooks/useApi.ts`**:
- Update `useCards` to return `{ data: CardListResponse | undefined, ... }`
- Add `useFilterOptions()` hook

**`pages/Dashboard.tsx`**:
- Remove `limit: 10000` from `useCards` call
- Use `useFilterOptions()` for type/set dropdown options instead of deriving from card list

**`components/CardTable.tsx`**:
- Accept `total?: number` prop for display
- Show "Showing X of Y cards" indicator when total is provided

---

### Implementation Order

1. Fix cache user isolation (dependencies.py)
2. Add repository methods (repository.py)
3. Update stats route (routes/stats.py)
4. Update analytics route (routes/analytics.py)
5. Update cards route + add filter-options (routes/cards.py)
6. Update frontend types (api/client.ts)
7. Update hooks (hooks/useApi.ts)
8. Update Dashboard (pages/Dashboard.tsx)
9. Update CardTable (components/CardTable.tsx)
