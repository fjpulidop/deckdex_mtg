# Delta Spec: Server-Side Pagination with Sorting

## GET /api/cards/ — Updated Query Parameters

| Parameter | Type | Default | Validation | Description |
|-----------|------|---------|------------|-------------|
| `limit` | int | 100 | 1–10000 | Max items to return |
| `offset` | int | 0 | ≥0 | Row offset |
| `sort_by` | str | `created_at` | Enum: name, created_at, price_eur, quantity, set_name, rarity, cmc | Sort column |
| `sort_dir` | str | `desc` | Enum: asc, desc | Sort direction |

All existing filter parameters remain unchanged.

## Repository Interface Change

`CollectionRepository.get_cards_filtered()` gains two new keyword parameters with defaults:

- `sort_by: str = "created_at"`
- `sort_dir: str = "desc"`

Default values maintain backwards compatibility.

## SQL Sort Column Whitelist

Only the following DB columns may appear in `ORDER BY`:
`name`, `created_at`, `price_eur`, `quantity`, `set_name`, `rarity`, `cmc`

Any value not in this list MUST fall back to `created_at`.

## Frontend API Parameters

`api.getCards()` accepts two new optional string parameters:
- `sort_by`: one of the allowed column names
- `sort_dir`: `"asc"` or `"desc"`

## Frontend State

Dashboard owns:
- `sortBy: string` (default `"created_at"`)
- `sortDir: "asc" | "desc"` (default `"desc"`)
- `page: number` (default `1`)

Derived: `offset = (page - 1) * PAGE_SIZE` where `PAGE_SIZE = 50`

## CardTable Props Change

New props:
- `sortBy: string` — current sort key (from server state)
- `sortDir: "asc" | "desc"` — current sort direction
- `onSortChange: (key: string, dir: "asc" | "desc") => void` — callback when header clicked
- `page: number` — current page number
- `totalPages: number` — total pages derived from server total
- `onPageChange: (page: number) => void` — callback when page changes

Removed internal state:
- `sortKey` / `sortDirection` local state removed
- `currentPage` local state removed
- `itemsPerPage` constant removed
- Client-side sort computation removed
