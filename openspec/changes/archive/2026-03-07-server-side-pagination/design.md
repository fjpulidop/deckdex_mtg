# Design: Server-Side Pagination with Sorting

## Architecture Overview

```
Dashboard (page, sortBy, sortDir state)
  → useCards({ limit:50, offset, sortBy, sortDir })
    → api.getCards({ sort_by, sort_dir, limit, offset, ...filters })
      → GET /api/cards/?sort_by=name&sort_dir=asc&limit=50&offset=0
        → repo.get_cards_filtered(..., sort_by="name", sort_dir="asc")
          → SQL ORDER BY name ASC LIMIT 50 OFFSET 0
```

## Backend Changes

### `backend/api/routes/cards.py`

Add two new optional query parameters to `list_cards`:

```python
sort_by: Optional[str] = Query(default="created_at", pattern="^(name|created_at|price_eur|quantity|set_name|rarity|cmc)$")
sort_dir: Optional[str] = Query(default="desc", pattern="^(asc|desc)$")
```

Using `pattern=` regex validation on the `Query` object is the FastAPI idiomatic way to whitelist values. This prevents SQL injection at the HTTP boundary.

Pass `sort_by` and `sort_dir` into the `filters` dict (or as separate params) to `repo.get_cards_filtered()`.

### `deckdex/storage/repository.py`

Extend the abstract `get_cards_filtered()` signature to accept `sort_by` and `sort_dir`:

```python
def get_cards_filtered(
    self,
    user_id: Optional[int],
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Tuple[List[Dict[str, Any]], int]:
```

The `PostgresCollectionRepository` implementation replaces the hardcoded `ORDER BY created_at DESC NULLS LAST, id DESC` with a dynamic clause:

```python
SORT_COLUMN_MAP = {
    "name": "name",
    "created_at": "created_at",
    "price_eur": "price_eur",
    "quantity": "quantity",
    "set_name": "set_name",
    "rarity": "rarity",
    "cmc": "cmc",
}

col = SORT_COLUMN_MAP.get(sort_by, "created_at")
direction = "ASC" if sort_dir == "asc" else "DESC"
nulls = "NULLS LAST" if direction == "DESC" else "NULLS FIRST"
order_clause = f"ORDER BY {col} {direction} {nulls}, id {direction}"
```

The column map acts as a second layer of defense (whitelist before string interpolation).

## Frontend Changes

### `frontend/src/api/client.ts`

Add `sort_by` and `sort_dir` to the `getCards` params type.

### `frontend/src/hooks/useApi.ts`

Add `sortBy` and `sortDir` to `CardsParams` interface and map to snake_case for the API call.

### `frontend/src/pages/Dashboard.tsx`

- Replace `limit: 10000` with `limit: 50`
- Add `page` state (starts at 1), compute `offset = (page - 1) * 50`
- Add `sortBy` state (default `"created_at"`) and `sortDir` state (default `"desc"`)
- Pass all four to `useCards`
- Pass `onSortChange`, `page`, `totalPages` (derived from `cardPage.total`) to `CardTable`
- Reset page to 1 when filters or sort change

### `frontend/src/components/CardTable.tsx`

- Remove `sortedCards` computation (client-side sort)
- Remove `totalPages` / `startIndex` computed from local `sortedCards`
- Add props: `sortBy`, `sortDir`, `onSortChange`, `page`, `totalPages`, `onPageChange`
- Render `paginatedCards = cards` directly (cards are already the current page from server)
- Keep header sort indicators and click handlers, but delegate to `onSortChange` callback
- Use server-provided `serverTotal` for pagination footer

## Column Mapping

The frontend uses `price` as the card field name; the sort column sent to the API must be `price_eur` (the DB column). Dashboard will map `"price"` → `"price_eur"` when constructing the `sortBy` param.

## No i18n changes needed

The existing keys (`cardTable.showing`, `cardTable.page`, `common.previous`, `common.next`) already cover the pagination footer.

## Backwards Compatibility

`sort_by` and `sort_dir` default to `created_at` / `desc` — same order as current hardcoded SQL. No breaking change.
