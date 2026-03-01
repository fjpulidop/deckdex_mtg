## 1. Backend: user_settings table and API

- [x] 1.1 Create migration `migrations/012_user_settings.sql`
- [x] 1.2 Create `deckdex/storage/user_settings_repository.py`
- [x] 1.3 Add `get_user_settings_repo()` to `backend/api/dependencies.py`
- [x] 1.4 Add endpoints to `backend/api/routes/settings_routes.py`: `GET /api/settings/external-apis` and `PUT /api/settings/external-apis`
- [ ] 1.5 Run migration against dev database and verify `user_settings` table is created correctly.

## 2. Backend: catalog-first lookup refactor

- [x] 2.1 Refactor `suggest_card_names(q, user_id)` in `scryfall_service.py`: catalog first, Scryfall fallback when enabled.
- [x] 2.2 Refactor `resolve_card_by_name(name, user_id)` in `scryfall_service.py`: catalog first, Scryfall fallback when enabled.
- [x] 2.3 Refactor `get_card_image(card_id, user_id)` in `card_image_service.py`: ImageStore first, Scryfall fallback when enabled.
- [x] 2.4 Refactor `_run_import()` in `importer_service.py`: catalog first, Scryfall fallback when enabled (checked once at start).
- [x] 2.5 Update all route call sites to pass `user_id` (cards.py suggest, resolve, image).

## 3. Frontend: Settings UI update

- [x] 3.1 Add API client methods to `frontend/src/api/client.ts`: `getExternalApisSettings()`, `updateExternalApisSettings()`.
- [x] 3.2 Add "APIs externas" section to `SettingsModal.tsx` with Scryfall toggle.
- [x] 3.3 Style the toggle following existing SettingsModal patterns.

## 4. Tests

- [x] 4.1 Unit tests for `UserSettingsRepository` default/merge logic.
- [x] 4.2 Unit tests for catalog-first suggest, resolve, image, import logic.
- [ ] 4.3-4.6 Integration tests (require full backend/frontend setup).
