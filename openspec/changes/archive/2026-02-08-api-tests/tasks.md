## 1. Dependencies and harness

- [x] 1.1 Add `httpx` to root `requirements.txt` (or the file used when running `pytest`) if not already present, so that FastAPI `TestClient` is available
- [x] 1.2 Create `tests/test_api.py` that imports `app` from `backend.api.main` and instantiates `TestClient(app)` (or equivalent) for use in tests

## 2. Health endpoint tests

- [x] 2.1 Add test that GET `/api/health` returns status 200
- [x] 2.2 Add test that GET `/api/health` response JSON contains `service`, `version`, and `status` with expected values (e.g. "DeckDex MTG API", "0.1.0", "healthy")

## 3. Stats endpoint tests

- [x] 3.1 Add test that GET `/api/stats` with mocked empty collection returns 200 and body with total_cards 0, total_value 0.0, average_price 0.0, last_updated string (patch `get_cached_collection` in `backend.api.routes.stats`)
- [x] 3.2 Add test that GET `/api/stats` with mocked collection of one or more cards with valid prices returns 200 and total_cards, total_value, average_price, last_updated consistent with mocked data
- [x] 3.3 Add test that GET `/api/stats` with query params (e.g. rarity or set_name) and mocked collection returns 200 and stats for the filtered subset only

## 4. Cards list endpoint tests

- [x] 4.1 Add test that GET `/api/cards` with mocked empty collection returns 200 and JSON array of length 0 (patch `get_cached_collection` in `backend.api.routes.cards`)
- [x] 4.2 Add test that GET `/api/cards` with mocked non-empty collection returns 200 and JSON array of cards consistent with mock (subject to default limit)
- [x] 4.3 Add test that GET `/api/cards?limit=2&offset=1` with mocked collection of at least 3 cards returns 200 and array of at most 2 cards (second and third in order)
- [x] 4.4 Add test that GET `/api/cards` with one or more filter params (e.g. rarity, set_name, search) and mocked collection returns 200 and only cards matching the filter semantics

## 5. Verification

- [x] 5.1 Run `pytest tests/test_api.py` from repo root and ensure all new tests pass
