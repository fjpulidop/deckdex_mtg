## Context

- The `catalog-system` change introduces a local `catalog_cards` table (~400k cards from Scryfall bulk data) and a filesystem-based `ImageStore` for card images. However, no existing code path uses the catalog for lookups yet -- all four call points (`suggest_card_names`, `resolve_card_by_name`, `get_card_image`, `_run_import`) go directly to the Scryfall API.
- There is no per-user settings infrastructure. The only settings today are Scryfall credentials stored globally in a JSON file (`backend/api/settings_store.py` -> `data/settings.json`), with no user scoping.
- Authentication is JWT-based. `get_current_user_id()` (in `backend/api/dependencies.py`) extracts the user ID from the JWT token and is used as a FastAPI dependency across card, deck, import, and analytics routes.
- The existing `SettingsModal.tsx` has two sections: "Scryfall API credentials" (JSON paste/upload) and "Importar coleccion" (link to import page + quick import). A new section will be added for external API toggles.
- Scryfall is a public API (no API key required for card data). The toggle controls whether the app is allowed to make outbound HTTP requests to Scryfall, not whether credentials exist.

## Goals / Non-Goals

**Goals:**

- Store per-user external API preferences in PostgreSQL (`user_settings` table with JSONB).
- Expose REST endpoints for reading and writing the user's external API settings.
- Add "APIs externas" section in `SettingsModal.tsx` with a Scryfall on/off toggle.
- Refactor all four Scryfall call points to check the local catalog first (catalog-first lookup), falling back to Scryfall only when the user has explicitly enabled it.
- When Scryfall is disabled and the card is not in the catalog, return a clear error (not a silent fallback).

**Non-Goals:**

- OpenAI toggle (future addition; the UI structure supports it but this change only implements Scryfall).
- Admin-level API controls (this is per-user only).
- Changing the existing Scryfall credentials section (that stays as-is for users who need it).
- Modifying the catalog sync job (that is part of `catalog-system`).
- Rate limiting or usage tracking for Scryfall calls.

## Decisions

1. **Per-user settings table with JSONB**
   - **Decision:** New `user_settings` table with columns `user_id` (FK to users, unique), `settings` (JSONB), `created_at`, `updated_at`. The JSONB column stores a nested structure like `{"external_apis": {"scryfall_enabled": false}}`. One row per user, created on first write (upsert).
   - **Rationale:** JSONB allows adding new settings without schema migrations. Per-user (not global) because different users may want different external API policies. Single JSONB column avoids a column-per-setting explosion.
   - **Alternatives:** Column-per-setting (rigid, requires migration for each new setting); global toggle (doesn't support multi-user scenarios); store in the existing JSON file (not user-scoped, not DB-backed).

2. **Default: Scryfall disabled**
   - **Decision:** When a user has no row in `user_settings` or the `scryfall_enabled` key is missing, the default is `false` (Scryfall disabled). The catalog is the sole data source until the user explicitly enables Scryfall fallback.
   - **Rationale:** Catalog-first is the whole point of this change. Users who want external calls must opt in. This also means newly created users work fully offline with just the catalog.
   - **Alternatives:** Default enabled (defeats the purpose of catalog-first); prompt on first login (adds UX complexity).

3. **UserSettingsRepository in deckdex/storage/**
   - **Decision:** New `deckdex/storage/user_settings_repository.py` with `UserSettingsRepository` class. Methods: `get_external_apis_settings(user_id) -> dict`, `update_external_apis_settings(user_id, settings: dict)`, and a lower-level `get_user_settings(user_id) -> dict` / `upsert_user_settings(user_id, settings: dict)`. Uses SQLAlchemy `text()` queries like the existing `CollectionRepository`.
   - **Rationale:** Follows the existing repository pattern (all DB ops through repository classes in `deckdex/storage/`). Keeps the core package framework-free. Separate from `CollectionRepository` because user settings are a different domain.
   - **Alternatives:** Extend `CollectionRepository` (muddies the interface); add to `settings_store.py` (that's a JSON file store, not DB-backed); raw SQL in the route (breaks conventions).

4. **API endpoints on existing settings router**
   - **Decision:** Add `GET /api/settings/external-apis` and `PUT /api/settings/external-apis` to the existing `backend/api/routes/settings_routes.py`. Both require authentication (`Depends(get_current_user_id)`). GET returns `{"scryfall_enabled": bool}`. PUT accepts `{"scryfall_enabled": bool}` and returns the same shape. The router already has prefix `/api/settings`.
   - **Rationale:** Reuse the existing settings router rather than creating a new one. The URL pattern is clear: `/api/settings/scryfall-credentials` (existing) vs `/api/settings/external-apis` (new). Both are settings, logically grouped.
   - **Alternatives:** New router (unnecessary, adds registration overhead); nest under `/api/users/me/settings` (inconsistent with existing pattern).

5. **Catalog-first lookup: inject user_id into service functions**
   - **Decision:** The four service functions (`suggest_card_names`, `resolve_card_by_name`, `get_card_image`, `_run_import`) are modified to accept a `user_id` parameter. Each function: (1) queries the catalog first via `CatalogRepository`, (2) if found, returns catalog data, (3) if not found, checks user settings via `UserSettingsRepository`, (4) if Scryfall enabled, falls back to Scryfall API call, (5) if Scryfall disabled, raises an appropriate error. Routes pass `user_id` from `Depends(get_current_user_id)`.
   - **Rationale:** The user_id is needed to look up the per-user Scryfall toggle. Passing it as a parameter keeps the services testable (no hidden dependencies). The catalog check is always first regardless of the toggle setting.
   - **Alternatives:** Global setting check (not per-user); middleware that sets a context var (implicit, harder to test); decorator on service functions (adds magic).

6. **Frontend: "APIs externas" section with toggle**
   - **Decision:** New section in `SettingsModal.tsx` between "Scryfall API credentials" and "Importar coleccion". Section title: "APIs externas". Contains a labeled toggle (checkbox or switch) for "Scryfall" with description text explaining what it does. Toggle state is loaded from `GET /api/settings/external-apis` on mount and saved via `PUT /api/settings/external-apis` on change (debounced or on explicit save). The section is generic: adding a future OpenAI toggle means adding another row, not restructuring.
   - **Rationale:** "APIs externas" is a generic section name that accommodates future API toggles. Positioned logically between credentials (which configure APIs) and import (which uses APIs). Toggle is a simple boolean control matching the backend model.
   - **Alternatives:** Separate settings page (overkill for one toggle); inline toggle next to each API call point (scattered, confusing); radio buttons (only two states, toggle is clearer).

7. **Error handling when Scryfall is disabled and card not in catalog**
   - **Decision:** When a card is not found in the catalog and Scryfall is disabled: autocomplete returns empty list (graceful degradation), resolve returns 404 with message "Card not found in catalog. Enable Scryfall in Settings to search online.", image returns 404 with similar message, import marks the card as `not_found` in the import result (same as today's behavior when Scryfall fails).
   - **Rationale:** Autocomplete returning empty is standard UX (no results). For explicit lookups (resolve, image), a clear error message guides the user to the fix. Import already handles `not_found` cards.
   - **Alternatives:** Return a special HTTP status (non-standard); silently skip (confusing); block import entirely (too aggressive).

## Risks / Trade-offs

- **Risk:** The catalog may not be synced yet when a new deployment starts. Users with Scryfall disabled will get no results for any card. **Mitigation:** The Settings UI should show a note when the catalog is empty or not synced, suggesting the admin trigger a sync. This is informational only (not blocking).
- **Risk:** Per-user settings add a DB query to every card lookup (to check if Scryfall is enabled). **Mitigation:** The `user_settings` table is tiny (one row per user). The query is a simple PK lookup on `user_id`. Can be cached in-memory per request or with a short TTL if needed, but not required for MVP.
- **Trade-off:** Passing `user_id` to service functions changes their signatures. All call sites (routes) must be updated. **Mitigation:** There are only four call sites, all in backend routes that already have `Depends(get_current_user_id)` available.
- **Trade-off:** The toggle is per-user but the catalog is global. A user who disables Scryfall still benefits from another user's Scryfall fallback populating the catalog (if the admin syncs). This is by design -- the toggle controls outbound calls from the user's session, not catalog population.

## Migration Plan

1. Migration 012 (or next available): Create `user_settings` table (`user_id` integer UNIQUE NOT NULL REFERENCES users(id), `settings` JSONB NOT NULL DEFAULT '{}', `created_at` TIMESTAMPTZ DEFAULT now(), `updated_at` TIMESTAMPTZ DEFAULT now()`).
2. Deploy backend with new `UserSettingsRepository`, updated settings routes, and refactored service functions. The catalog-first lookup is active immediately (catalog check runs, then checks user setting for Scryfall fallback).
3. Deploy frontend with the new "APIs externas" section in SettingsModal.
4. No data migration needed -- the default (Scryfall disabled) applies to all existing users until they change it.

## Open Questions

- None. All decisions finalized.
