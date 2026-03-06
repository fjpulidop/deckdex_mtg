# SQL Filtering and Pagination Spec

## Overview

SQL-level parameterized filtering, LIMIT/OFFSET pagination with total count, and dedicated filter-options endpoint for the PostgreSQL storage path.

## Requirements

### Repository

- `PostgresCollectionRepository.get_cards_filtered(user_id, filters, limit, offset)` must:
  - Accept filter dict with keys: `search`, `rarity`, `type_`, `color_identity`, `set_name`, `price_min`, `price_max`, `cmc`
  - Build parameterized SQL WHERE clauses (no string interpolation of user input)
  - Return `(cards: list[dict], total: int)` where total is the count of all matching rows before LIMIT
  - Use `COUNT(*) OVER()` window function for single-query pagination

- `PostgresCollectionRepository.get_cards_stats(user_id, filters)` must:
  - Accept the same filter dict
  - Return `{ total_cards, total_value, average_price }` from a single SQL aggregation query

- `PostgresCollectionRepository.get_cards_analytics(user_id, filters, dimension, limit)` must:
  - Support dimensions: `rarity`, `color_identity`, `set_name`, `cmc`
  - Return list of `{ label: str, count: int }` sorted by count DESC

### API Endpoints

#### GET /api/cards/

- Response changes from `Card[]` to:
  ```json
  { "items": Card[], "total": integer, "limit": integer, "offset": integer }
  ```
- Postgres path: uses `get_cards_filtered()` directly (bypasses collection cache)
- Sheets path: uses cached collection + Python filtering, wrapped in same response shape

#### GET /api/cards/filter-options

- New endpoint returning distinct filter values for UI dropdowns
- Response: `{ "types": string[], "sets": string[] }`
- Postgres: `SELECT DISTINCT type_line FROM cards WHERE user_id = :uid` and same for set_name
- Sheets: derive from cached collection
- Must be registered before `/{card_id_or_name}` route to avoid conflict

### Cache

- `_collection_cache` in `dependencies.py` must be keyed by `user_id` (integer)
- Stats cache key must include `user_id`
- Analytics cache key must include `user_id`

## Non-requirements

- The Google Sheets path is not required to use SQL — Python-in-memory filtering is acceptable
- Cursor-based pagination is not required (offset-based is sufficient)
- Full-text search (PostgreSQL tsvector) is not required — ILIKE is sufficient
