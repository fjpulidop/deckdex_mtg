## 1. Backend – shared filter logic

- [x] 1.1 Add `backend/api/filters.py` with `parse_price(price_str)` and `filter_collection(collection, search, rarity, type_, set_name, price_min, price_max)` using the same semantics as stats (name contains, exact match for rarity/type/set_name, price range inclusive)
- [x] 1.2 Refactor `backend/api/routes/stats.py` to use `filters.parse_price` and `filters.filter_collection` instead of local implementations; ensure existing stats behavior and tests remain unchanged

## 2. Backend – cards list accepts filters

- [x] 2.1 Extend GET `/api/cards` to accept optional query params: `rarity`, `type`, `set_name`, `price_min`, `price_max` (keep existing `limit`, `offset`, `search`)
- [x] 2.2 In list_cards: get collection, call `filter_collection` with the new params (and search), then apply limit/offset to the filtered result; return that slice

## 3. Frontend – API and hooks pass filters

- [x] 3.1 Extend `api.getCards` in `frontend/src/api/client.ts` to accept optional `rarity`, `type`, `set_name`, `price_min`, `price_max` and send them as query params
- [x] 3.2 Extend `useCards` in `frontend/src/hooks/useApi.ts` to accept a filters object (search, rarity, type, set, priceMin, priceMax) and pass it to `getCards` (map set → set_name, priceMin → price_min, priceMax → price_max for the API)

## 4. Frontend – dashboard uses filtered list

- [x] 4.1 In Dashboard: pass current filter state (search, rarity, type, setFilter, priceMin, priceMax) into `useCards` so the cards request includes filter params
- [x] 4.2 Use the API response as the list to display: remove or make redundant the client-side filter so the table shows exactly the cards returned by the API; derive typeOptions and setOptions from the returned cards (filtered result)
