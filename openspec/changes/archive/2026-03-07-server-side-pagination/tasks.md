# Tasks: Server-Side Pagination with Sorting

## Backend

- [ ] Add `sort_by` and `sort_dir` query params to `list_cards` in `backend/api/routes/cards.py`
- [ ] Extend `get_cards_filtered()` signature in abstract `CollectionRepository` with `sort_by` and `sort_dir` params
- [ ] Implement dynamic ORDER BY in `PostgresCollectionRepository.get_cards_filtered()`
- [ ] Add `SORT_COLUMN_MAP` whitelist constant to repository

## Frontend

- [ ] Add `sort_by` / `sort_dir` to `getCards()` params in `frontend/src/api/client.ts`
- [ ] Add `sortBy` / `sortDir` to `CardsParams` in `frontend/src/hooks/useApi.ts` and map to snake_case
- [ ] Add sort + page state to `Dashboard.tsx`, change `limit: 10000` → `limit: 50`, compute `offset`
- [ ] Remove TODO comment at Dashboard.tsx line ~34
- [ ] Pass sort/page props to `CardTable`
- [ ] Remove client-side sort from `CardTable.tsx`, accept sort/page as props, emit callbacks
- [ ] Keep keyboard navigation (ArrowUp/Down) working with server-paginated data
