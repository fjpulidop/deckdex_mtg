## Architecture

Dual-path pattern: Postgres path uses SQL-level filtering/aggregation; Google Sheets path keeps existing Python in-memory approach. The routing decision is made at the service boundary by checking if a `CollectionRepository` is available.

```
GET /api/cards
  ├── Postgres: repo.get_cards_filtered(user_id, filters, limit, offset) → (cards, total)
  │   └── SELECT COUNT(*) OVER(), * FROM cards WHERE <dynamic> LIMIT :limit OFFSET :offset
  └── Sheets: get_cached_collection() + filter_collection() + slice → wrap in CardPage

GET /api/stats
  ├── Postgres: repo.get_stats_aggregated(user_id, filters) → Stats
  │   └── SELECT COUNT(*), SUM(price_eur * quantity), AVG(price_eur) FROM cards WHERE <dynamic>
  └── Sheets: get_cached_collection() + filter_collection() + calculate_stats()

GET /api/analytics/<dimension>
  ├── Postgres: repo.get_analytics_grouped(user_id, filters, dimension) → [(label, count)]
  │   └── SELECT <dimension_col>, SUM(quantity) FROM cards WHERE <dynamic> GROUP BY <dimension_col>
  └── Sheets: get_cached_collection() + filter_collection() + Counter loop
```

## Data Model Changes

No schema changes. New repository methods only.

**New `CollectionRepository` abstract methods:**
```python
def get_cards_filtered(
    self,
    user_id: Optional[int],
    filters: CardFilters,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Dict], int]:
    """Returns (cards, total_count). Postgres: SQL-level. Sheets: Python fallback."""

def get_stats_aggregated(
    self,
    user_id: Optional[int],
    filters: CardFilters,
) -> Dict[str, Any]:
    """Returns {total_cards, total_value, average_price}. Postgres: SQL aggregation."""

def get_analytics_grouped(
    self,
    user_id: Optional[int],
    filters: CardFilters,
    dimension: str,  # 'rarity' | 'color_identity' | 'cmc' | 'set_name' | 'type_line'
    limit: Optional[int] = None,
) -> List[Tuple[str, int]]:
    """Returns [(label, count)] sorted by count DESC. Postgres: GROUP BY."""

def get_filter_options(
    self,
    user_id: Optional[int],
) -> Dict[str, List[str]]:
    """Returns {types: [...], sets: [...]} for filter dropdowns."""
```

**`CardFilters` dataclass** (in `deckdex/storage/repository.py`):
```python
@dataclass
class CardFilters:
    search: Optional[str] = None
    rarity: Optional[str] = None
    type_: Optional[str] = None
    color_identity: Optional[str] = None
    set_name: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
```

## SQL Design

**Filtered cards with total count (single query):**
```sql
SELECT COUNT(*) OVER() AS total, *
FROM cards
WHERE user_id = :user_id
  AND (:search IS NULL OR LOWER(name) LIKE :search_pat)
  AND (:rarity IS NULL OR LOWER(rarity) = :rarity)
  AND (:type IS NULL OR LOWER(type_line) LIKE :type_pat)
  AND (:set_name IS NULL OR set_name = :set_name)
  AND (:price_min IS NULL OR price_eur >= :price_min)
  AND (:price_max IS NULL OR price_eur <= :price_max)
ORDER BY created_at DESC NULLS LAST, id DESC
LIMIT :limit OFFSET :offset
```

**Stats aggregation:**
```sql
SELECT
  COALESCE(SUM(quantity), 0) AS total_cards,
  COALESCE(SUM(price_eur * quantity), 0) AS total_value,
  COALESCE(AVG(price_eur), 0) AS average_price
FROM cards
WHERE user_id = :user_id
  -- same filter conditions as above
```

**Analytics GROUP BY (rarity example):**
```sql
SELECT COALESCE(rarity, 'Unknown') AS label, SUM(quantity) AS count
FROM cards
WHERE user_id = :user_id
  -- same filter conditions
GROUP BY rarity
ORDER BY count DESC
```

**Filter options:**
```sql
SELECT DISTINCT type_line FROM cards WHERE user_id = :uid AND type_line IS NOT NULL ORDER BY type_line;
SELECT DISTINCT set_name FROM cards WHERE user_id = :uid AND set_name IS NOT NULL ORDER BY set_name;
```

Note: color_identity filtering with SQL LIKE on string representation (e.g., `color_identity LIKE '%W%'`) since values are stored as text/list-repr. This matches the current Python logic.

## API Changes

**`GET /api/cards` response (BREAKING):**
```json
{
  "items": [...],
  "total": 1234,
  "limit": 100,
  "offset": 0
}
```

**New `GET /api/cards/filter-options`:**
```json
{
  "types": ["Artifact", "Creature", ...],
  "sets": ["Dominaria United", ...]
}
```
Requires authentication. Returns 200 with empty arrays if no data. 30-second cache keyed by user_id.

## Cache Strategy

`_collection_cache` in `dependencies.py` changes from:
```python
_collection_cache = {'data': None, 'timestamp': None, 'ttl': 30}
```
to:
```python
_collection_cache: dict[int, dict] = {}  # keyed by user_id
```

For the Postgres path, the collection cache is bypassed (SQL queries are the source of truth). The cache is only used for Google Sheets (where loading all rows is the only option).

Stats and analytics caches (`_stats_cache`, `_analytics_cache`) remain but must include `user_id` in the cache key. Currently they only key by filter params — this must be fixed to prevent cross-user leakage.

## Frontend Changes

**`CardPage` interface in `api/client.ts`:**
```typescript
export interface CardPage {
  items: Card[];
  total: number;
  limit: number;
  offset: number;
}
```

**`getCards` updated return type:**
```typescript
getCards: async (...): Promise<CardPage>
```

**New `getFilterOptions`:**
```typescript
getFilterOptions: async (): Promise<{ types: string[]; sets: string[] }>
```

**`useCards` hook** returns `CardPage` instead of `Card[]`. Dashboard accesses `data.items` for the card list and `data.total` for display.

**`Dashboard.tsx` changes:**
- Remove `limit: 10000`
- Add `useFilterOptions` hook for type/set dropdown options
- Pass `serverTotal={data?.total}` to `CardTable`

**`CardTable.tsx` changes:**
- Accept optional `serverTotal?: number` prop
- When provided, display "X total cards" using server total instead of `cards.length`
- Keep existing client-side sort and pagination

## Implementation Order

1. `deckdex/storage/repository.py` — `CardFilters` dataclass + `get_cards_filtered`, `get_stats_aggregated`, `get_analytics_grouped`, `get_filter_options` on `PostgresCollectionRepository`
2. `backend/api/dependencies.py` — fix cache user isolation (`_collection_cache` keyed by user_id)
3. `backend/api/routes/stats.py` — SQL aggregation path for Postgres
4. `backend/api/routes/analytics.py` — SQL GROUP BY path for all 5 endpoints
5. `backend/api/routes/cards.py` — use `get_cards_filtered`; return `CardPage`; add `filter-options` endpoint
6. `frontend/src/api/client.ts` — `CardPage` type; updated `getCards`; `getFilterOptions`
7. `frontend/src/hooks/useApi.ts` — updated `useCards` return type; new `useFilterOptions`
8. `frontend/src/pages/Dashboard.tsx` — use paginated response; use filter options hook
9. `frontend/src/components/CardTable.tsx` — accept `serverTotal` prop
