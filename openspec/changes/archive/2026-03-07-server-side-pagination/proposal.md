# Proposal: Server-Side Pagination with Sorting for Card Collection

## Problem

The Dashboard currently requests all cards with `limit: 10000` and paginates client-side in `CardTable.tsx`. Client-side sorting and pagination means:

1. Large collections (1000+ cards) transfer unnecessary data over the network.
2. Sorting is computed in JavaScript on every render.
3. The `TODO` comment at `Dashboard.tsx:34` explicitly acknowledges this technical debt.

The backend already supports `limit`/`offset` pagination and `COUNT(*) OVER()` for efficient total counts, but there is no `sort_by`/`sort_dir` support.

## Proposed Solution

Delegate pagination and sorting to the server:

- **Backend**: Add `sort_by` and `sort_dir` query parameters to `GET /api/cards/`. Whitelist allowed columns to prevent SQL injection. Apply `ORDER BY` in `get_cards_filtered()`.
- **Frontend**: Replace the `limit: 10000` + client-side-sort approach with true server-side pagination (50 cards per page) and server-side sorting. Sort state and page offset live in the Dashboard and are passed as query params to `useCards`.

## Allowed Sort Columns

`name`, `created_at`, `price_eur`, `quantity`, `set_name`, `rarity`, `cmc`

Note: The API column name `price_eur` maps to the frontend `price` column. The route layer will handle this mapping.

## Out of Scope

- Cursor-based pagination (offset is sufficient for this collection size).
- Google Sheets path sorting (Sheets path will continue to return unsorted data; Python-level sorting is not added to keep complexity low).
