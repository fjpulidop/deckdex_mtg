# Pagination & Performance Exploration (2026-03-06)

## Executive Summary

DeckDex currently loads the **entire collection into memory** for every request path: cards list, stats, and all 5 analytics endpoints. Filtering and pagination happen in Python after the full dataset is loaded. This architecture works acceptably for small collections (< 1,000 cards) but will degrade significantly as collections grow. The most impactful improvements involve pushing filtering and aggregation down to SQL, introducing proper server-side pagination with total counts, and consolidating the analytics endpoints into a single request.

---

## Current Architecture: How Data Flows

### 1. Collection Loading (dependencies.py)

**Pattern:** `get_cached_collection()` loads ALL cards from Postgres (or Google Sheets) into a Python list-of-dicts, cached for 30 seconds.

```
Browser request
  -> FastAPI route
    -> get_cached_collection(user_id)
      -> repo.get_all_cards(user_id)  # SELECT * FROM cards WHERE user_id = :user_id
      -> cache in _collection_cache['data'] (global, 30s TTL)
    -> filter_collection(entire_list, ...)  # Python-side filtering
    -> Python-side pagination (list slicing)
  -> JSON response
```

**Key observation:** The cache is a single global dict, NOT keyed by user_id. In a multi-user scenario, user A's cached collection could be served to user B (if within TTL). This is a **correctness bug**, not just a performance issue.

**Rating:**
- **Impact of fixing:** HIGH (correctness + performance)
- **Effort:** LOW (key cache by user_id)

### 2. Cards List (routes/cards.py)

```python
collection = get_cached_collection(user_id=user_id)  # ALL cards
filtered = filter_collection(collection, ...)          # Python filtering
paginated = filtered[offset : offset + limit]          # Python slicing
return paginated  # No total_count returned!
```

**Problems identified:**
- a) Full collection loaded even for paginated requests
- b) No `total_count` returned to frontend -- frontend cannot render pagination controls
- c) `limit` defaults to 100 but Dashboard sets it to 10,000 (effectively "give me everything")
- d) Filtering is pure Python iteration (no SQL WHERE clauses)

**Rating:**
- **Impact:** HIGH (performance scales linearly with collection size; no pagination UX possible without total)
- **Effort:** MEDIUM (need SQL-level LIMIT/OFFSET/WHERE + total count response wrapper)

### 3. Stats (routes/stats.py)

```python
collection = get_cached_collection(user_id=user_id)  # ALL cards
filtered = filter_collection(collection, ...)          # Python filtering
stats = calculate_stats(filtered)                      # Python aggregation
```

Stats has its own 30s cache keyed by filter params. But the underlying data still requires loading all cards.

**What stats really needs:** `SELECT COUNT(*), SUM(price_eur * quantity), ... FROM cards WHERE <filters>`
This is a single SQL query, no need to load rows.

**Rating:**
- **Impact:** HIGH (stats is the most frequently called endpoint -- loaded on every Dashboard visit and every Analytics drill-down)
- **Effort:** MEDIUM (SQL aggregation query + filter translation)

### 4. Analytics (routes/analytics.py)

Five separate endpoints: `/rarity`, `/color-identity`, `/cmc`, `/sets`, `/type`

Each endpoint:
1. Loads all cards via `get_cached_collection()`
2. Filters in Python via `filter_collection()`
3. Iterates through all filtered cards to build a Counter
4. Sorts and returns

**Analytics page fires ALL 5 + stats = 6 parallel requests on load**, each loading and filtering the same dataset. The 30s collection cache mitigates the DB hit, but the Python filtering and aggregation runs 6 times.

Analytics also has its own per-endpoint cache (`_analytics_cache`, 30s TTL) keyed by (endpoint, filter_params). So on initial load: 1 DB query + 6 Python filter+aggregate passes. On repeat within 30s: 0 work.

**What analytics really needs:** `SELECT rarity, SUM(quantity) FROM cards WHERE <filters> GROUP BY rarity`
Each endpoint is a single SQL GROUP BY query.

**Rating:**
- **Impact:** HIGH (6 redundant filter passes; could be 5 SQL queries or even 1 combined query)
- **Effort:** MEDIUM (SQL GROUP BY queries) to HIGH (combined endpoint)

### 5. Filtering (filters.py)

Pure Python filtering: iterates the full list for each active filter, creating new lists each time. Filters applied sequentially (not composed):

```python
result = collection
if search: result = [c for c in result if ...]
if rarity: result = [c for c in result if ...]
if type_:  result = [c for c in result if ...]
# ... etc
```

For N cards and M active filters, this is O(N * M) with M list allocations.

**Rating:**
- **Impact:** MEDIUM (Python iteration is fast for < 5k cards; becomes noticeable at 10k+)
- **Effort:** MEDIUM (need to build SQL WHERE clauses from the same filter params)

### 6. Frontend: Dashboard (pages/Dashboard.tsx)

```typescript
const { data: cards } = useCards({
  ...filters,
  limit: 10000,  // <-- Requests up to 10,000 cards!
});
```

Dashboard requests limit=10000, then renders all cards in `CardTable`. No virtual scrolling, no infinite scroll, no server-side pagination controls. Type/set filter options are derived client-side from the full result set.

**Rating:**
- **Impact:** HIGH (10k cards = large JSON payload + DOM rendering bottleneck)
- **Effort:** HIGH (requires pagination UI, server-side total count, rethinking filter option derivation)

### 7. Frontend: Analytics (pages/Analytics.tsx)

Fires 5 analytics queries + 1 stats query in parallel using TanStack Query with 30s staleTime. Each query is independent -- no batching. Drill-down re-fires all 6 queries.

**Rating:**
- **Impact:** MEDIUM (6 small requests vs 1 combined; latency from round-trips)
- **Effort:** MEDIUM (combined analytics endpoint + single query hook)

### 8. Frontend: API Client (api/client.ts)

`getCards()` returns `Promise<Card[]>` -- flat array, no pagination metadata. No `total_count`, no `next_page`, no cursor. Would need a response wrapper like `{ items: Card[], total: number }` for proper pagination.

**Rating:**
- **Impact:** HIGH (blocking issue for implementing pagination UI)
- **Effort:** LOW (change response type; update hook)

### 9. Repository (storage/repository.py)

`get_all_cards()` does `SELECT * FROM cards ORDER BY created_at DESC`. No parameterized filtering, no LIMIT/OFFSET at SQL level. All other repo methods are single-card CRUD.

**No SQL-level pagination primitives exist.**

**Rating:**
- **Impact:** HIGH (this is the root cause -- everything else is downstream)
- **Effort:** MEDIUM (add `get_cards_paginated(filters, limit, offset) -> (cards, total)`)

### 10. Collection Cache Correctness Bug

The `_collection_cache` is a **single global dict** shared across all users:

```python
_collection_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 30
}
```

`get_cached_collection(user_id=1)` caches the result. Within 30s, `get_cached_collection(user_id=2)` returns user 1's cards. The `user_id` parameter is only passed to the repo but NOT used as a cache key.

**Rating:**
- **Impact:** CRITICAL (data leaks between users in multi-user deployment)
- **Effort:** LOW (key cache by user_id)

---

## Spec Analysis

### analytics-dashboard/spec.md
- Specifies filter params, drill-down, chart types
- Does NOT mention pagination or performance requirements
- Does NOT specify response size limits or batching

### web-api-backend/spec.md
- Cards list: "filter then paginate (limit/offset)"
- Stats: "cache 30s per filter combination"
- Analytics: "same filter params as stats; JSON arrays for charts"
- Does NOT specify total count in response
- Does NOT specify SQL-level optimization requirements

---

## Prioritized Improvement Ideas

### Priority 1: Fix Collection Cache User Isolation (CRITICAL)

| Dimension | Rating |
|-----------|--------|
| Impact    | CRITICAL |
| Effort    | LOW |
| Risk      | LOW |

Key the `_collection_cache` by `user_id`. Simplest fix: change from single dict to `dict[int, CacheEntry]`.

### Priority 2: SQL-Level Stats Aggregation

| Dimension | Rating |
|-----------|--------|
| Impact    | HIGH |
| Effort    | MEDIUM |
| Risk      | LOW |

Replace `get_cached_collection() + filter_collection() + calculate_stats()` with a single SQL query:
```sql
SELECT COUNT(*) as total_cards,
       SUM(price_eur * quantity) as total_value,
       AVG(price_eur) as avg_price
FROM cards
WHERE user_id = :uid AND <dynamic_filters>
```
Eliminates loading all cards just to count them.

### Priority 3: SQL-Level Analytics Aggregation

| Dimension | Rating |
|-----------|--------|
| Impact    | HIGH |
| Effort    | MEDIUM |
| Risk      | LOW |

Replace Python Counter loops with SQL GROUP BY:
```sql
SELECT rarity, SUM(quantity) as count FROM cards
WHERE user_id = :uid AND <filters>
GROUP BY rarity ORDER BY count DESC
```
One query per analytics dimension instead of loading all cards + Python iteration.

### Priority 4: Paginated Cards Response with Total Count

| Dimension | Rating |
|-----------|--------|
| Impact    | HIGH |
| Effort    | MEDIUM |
| Risk      | MEDIUM (breaking API change) |

Change `/api/cards` response from `Card[]` to `{ items: Card[], total: number, limit: number, offset: number }`. This enables proper pagination UI. Requires frontend migration (update type, update hooks, update CardTable).

Consider: use SQL `SELECT COUNT(*) OVER() as total, * FROM cards WHERE ... LIMIT :limit OFFSET :offset` for efficient single-query pagination.

### Priority 5: SQL-Level Filtering in Repository

| Dimension | Rating |
|-----------|--------|
| Impact    | HIGH |
| Effort    | MEDIUM |
| Risk      | MEDIUM (SQL injection if not parameterized carefully) |

Add `get_cards_filtered(filters, limit, offset)` to repository that builds parameterized SQL WHERE clauses. Replaces `get_all_cards() + filter_collection()` pattern.

Filter mapping:
- `search` -> `WHERE LOWER(name) LIKE :search`
- `rarity` -> `WHERE LOWER(rarity) = :rarity`
- `type_` -> `WHERE LOWER(type_line) LIKE :type`
- `color_identity` -> `WHERE color_identity @> :colors` (JSONB) or text matching
- `set_name` -> `WHERE set_name = :set_name`
- `price_min/max` -> `WHERE price_eur BETWEEN :min AND :max`
- `cmc` -> `WHERE cmc = :cmc` or `WHERE cmc >= 7`

### Priority 6: Combined Analytics Endpoint

| Dimension | Rating |
|-----------|--------|
| Impact    | MEDIUM |
| Effort    | MEDIUM |
| Risk      | LOW |

Add `GET /api/analytics/all` that returns all 5 distributions in a single response. Frontend fires 1 request instead of 5. Could execute 5 SQL queries in parallel server-side.

```json
{
  "rarity": [...],
  "color_identity": [...],
  "cmc": [...],
  "sets": [...],
  "type": [...]
}
```

### Priority 7: Dashboard Pagination UI

| Dimension | Rating |
|-----------|--------|
| Impact    | HIGH |
| Effort    | HIGH |
| Risk      | MEDIUM |

Replace `limit: 10000` with proper pagination:
- Page size selector (25, 50, 100)
- Page navigation (prev/next/first/last)
- "Showing X-Y of Z cards" indicator
- Requires Priority 4 (total count from server)

Alternative: virtual scrolling (react-window/react-virtualized) to handle large lists without pagination. Lower UX change, still needs all data loaded.

### Priority 8: Filter Options from Separate Endpoint

| Dimension | Rating |
|-----------|--------|
| Impact    | MEDIUM |
| Effort    | LOW |
| Risk      | LOW |

Dashboard derives type/set filter options from the card list:
```typescript
const typeOptions = Array.from(new Set(cards.map(c => c.type).filter(Boolean)));
```
This only works because ALL cards are loaded. With pagination, need a separate `GET /api/cards/filter-options` endpoint:
```sql
SELECT DISTINCT type_line FROM cards WHERE user_id = :uid ORDER BY type_line
SELECT DISTINCT set_name FROM cards WHERE user_id = :uid ORDER BY set_name
```

### Priority 9: Smarter Caching Strategy

| Dimension | Rating |
|-----------|--------|
| Impact    | MEDIUM |
| Effort    | LOW-MEDIUM |
| Risk      | LOW |

Current: 30s TTL, invalidated only by `clear_collection_cache()`. Consider:
- Cache invalidation on write (create/update/delete card)
- ETags for conditional requests
- Longer TTL for analytics (aggregations change less frequently)
- Redis/memcached for multi-process deployments (future)

---

## Recommended Implementation Order

1. **Fix cache user isolation** (Priority 1) -- correctness bug, do immediately
2. **SQL-level stats** (Priority 2) -- highest frequency endpoint, biggest perf win
3. **SQL-level analytics** (Priority 3) -- eliminates 6x redundant filtering
4. **Paginated response wrapper** (Priority 4) -- enables all frontend pagination work
5. **SQL-level filtering** (Priority 5) -- foundation for everything above
6. **Filter options endpoint** (Priority 8) -- unblocks Dashboard pagination
7. **Dashboard pagination UI** (Priority 7) -- biggest visible UX improvement
8. **Combined analytics endpoint** (Priority 6) -- reduces network round-trips
9. **Smarter caching** (Priority 9) -- polish

Note: Priorities 2, 3, and 5 are closely related. SQL-level filtering (Priority 5) is a prerequisite for SQL-level stats (2) and analytics (3). The natural implementation order is: 1 -> 5 -> 2 -> 3 -> 4 -> 8 -> 7 -> 6 -> 9.

---

## Architecture Decision: Google Sheets Compatibility

A key constraint: the app supports Google Sheets as a storage backend, where SQL-level filtering/aggregation is impossible. Options:

**Option A: Dual path** -- SQL optimization for Postgres, keep Python path for Sheets.
- Pro: Best performance for Postgres users
- Con: Two code paths to maintain

**Option B: Postgres-only optimization** -- Keep Python path as universal fallback, optimize only Postgres.
- Pro: Simpler; Sheets is a legacy/fallback path
- Con: None significant (Sheets users likely have small collections anyway)

**Recommendation:** Option B. Google Sheets collections are inherently small (API quotas limit ~5k rows practical max). The Python-in-memory approach is fine for that scale. Optimize Postgres path only.

---

## Metrics to Track (if implemented)

- P95 response time for `/api/stats` with/without SQL optimization
- P95 response time for `/api/analytics/*` with/without SQL optimization
- Dashboard initial load time (Time to Interactive)
- JSON payload size for `/api/cards` (before/after pagination)
- Memory usage of backend process (before/after eliminating full-collection caching)
