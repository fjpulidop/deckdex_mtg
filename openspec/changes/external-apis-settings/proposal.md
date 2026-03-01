## Why

Every card lookup in DeckDex (autocomplete, resolve-by-name, image fetch, import enrichment) currently calls the Scryfall API in real time. With the `catalog-system` change landing, we now have a local catalog of ~400k cards and their images. However, no code path actually prefers the catalog yet -- all four call points still go directly to Scryfall, making the catalog unused for lookups.

Users should be able to decide whether the app is allowed to make external API calls at all. Some users want a fully offline/catalog-only experience; others want Scryfall as a fallback for cards not yet in the catalog. There is no per-user settings infrastructure today (Scryfall credentials are stored globally in a JSON file), and no UI for toggling external API access.

This change introduces per-user external API settings, refactors all card lookup points to check the local catalog first, and only falls back to Scryfall when the user has explicitly enabled it.

## What Changes

- New **user_settings** table storing per-user preferences as JSONB, with `external_apis.scryfall_enabled` (boolean, default false) as the first setting.
- New **UserSettingsRepository** in the storage layer for reading/writing user settings.
- New **Settings API endpoints**: `GET /api/settings/external-apis` and `PUT /api/settings/external-apis` for reading/writing the user's external API preferences.
- New **"APIs externas" section** in the existing `SettingsModal.tsx` frontend component, with a toggle for Scryfall (on/off). The section is generic and prepared for future toggles (e.g. OpenAI).
- **Catalog-first lookup refactor** across four backend call points:
  1. `scryfall_service.py` `suggest_card_names()` -- search `catalog_cards` first, fallback to Scryfall autocomplete if enabled.
  2. `scryfall_service.py` `resolve_card_by_name()` -- search `catalog_cards` first, fallback to Scryfall `search_card()` if enabled.
  3. `card_image_service.py` `get_card_image()` -- check `ImageStore` first, fallback to Scryfall image download if enabled.
  4. `importer_service.py` `_run_import()` -- enrich from `catalog_cards` first, fallback to Scryfall if enabled.

## Capabilities

### New Capabilities

- `external-apis-settings`: Per-user settings for external API access. Includes `user_settings` table (JSONB), `UserSettingsRepository`, REST endpoints (`GET/PUT /api/settings/external-apis`), and frontend toggle UI in SettingsModal. Default: Scryfall disabled. Generic structure supports future API toggles.

### Modified Capabilities

- `card-name-autocomplete`: `suggest_card_names()` now queries `catalog_cards` first; only falls back to Scryfall when the requesting user has `scryfall_enabled = true`. Returns error if not in catalog and Scryfall is disabled.
- `card-detail-modal` (resolve): `resolve_card_by_name()` now queries `catalog_cards` first; only falls back to Scryfall when enabled.
- `card-image-storage`: `get_card_image()` now checks `ImageStore` first; only downloads from Scryfall when enabled.
- `web-api-backend` (import enrichment): `_run_import()` now enriches cards from catalog data first; only falls back to Scryfall when enabled.

## Impact

- **Database**: New migration for `user_settings` table (user_id FK, settings JSONB, created_at, updated_at).
- **Core (deckdex/)**: New `deckdex/storage/user_settings_repository.py` with `UserSettingsRepository`.
- **Backend**: New endpoints in `settings_routes.py`. Modified `scryfall_service.py`, `card_image_service.py`, `importer_service.py` to accept user_id and check settings before calling Scryfall. New dependency in `dependencies.py` for `UserSettingsRepository`.
- **Frontend**: New "APIs externas" section in `SettingsModal.tsx` with Scryfall toggle. New API methods in `api/client.ts` (`getExternalApisSettings`, `updateExternalApisSettings`).
- **Specs**: New `external-apis-settings` spec. Delta updates to autocomplete, image, and import specs.
