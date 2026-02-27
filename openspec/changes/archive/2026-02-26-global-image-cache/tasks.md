## 1. Database Migration

- [x] 1.1 Create `migrations/004_global_image_cache.sql`: add `scryfall_id TEXT` column to `cards`, drop `card_images` table, create `card_image_cache` table with `scryfall_id TEXT PRIMARY KEY`, `content_type TEXT NOT NULL`, `data BYTEA NOT NULL`, `cached_at TIMESTAMPTZ DEFAULT NOW()`

## 2. Repository Layer

- [x] 2.1 Add `get_card_image_by_scryfall_id(scryfall_id: str)` to `deckdex/storage/repository.py` — returns `(bytes, str)` or `None`
- [x] 2.2 Add `save_card_image_to_global_cache(scryfall_id: str, content_type: str, data: bytes)` to repository — upsert into `card_image_cache`
- [x] 2.3 Add `update_card_scryfall_id(card_id: int, scryfall_id: str)` to repository — updates `cards.scryfall_id`
- [x] 2.4 Remove old `get_card_image(card_id)` and `save_card_image(card_id, ...)` methods (or keep as deprecated if used elsewhere — verify first)

## 3. Service Layer

- [x] 3.1 Rewrite `backend/api/services/card_image_service.py` to implement the new lookup flow: card_id → scryfall_id → global cache; populate `scryfall_id` lazily on Scryfall fetch; use new repository methods

## 4. Route Layer

- [x] 4.1 Update `GET /api/cards/{id}/image` in `backend/api/routes/cards.py` — remove card-ownership check, keep authentication-only guard (`get_current_user_id` still required for auth, but no ownership query)

## 5. Verification

- [ ] 5.1 Run migration against local DB and confirm schema changes apply cleanly
- [ ] 5.2 Manually test: request image for a card → confirm Scryfall fetch + cache insert
- [ ] 5.3 Manually test: request same card image again → confirm cache hit (no Scryfall call in logs)
- [ ] 5.4 Manually test: request image as a different user → confirm 200 (no ownership error)
- [ ] 5.5 Run existing test suite `pytest tests/` and confirm no regressions

