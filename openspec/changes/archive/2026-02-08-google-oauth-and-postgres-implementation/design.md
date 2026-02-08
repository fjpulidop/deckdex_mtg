# Design: Google OAuth and PostgreSQL Implementation

## Context

The app today uses **Google Sheets** as the single source of truth: the CLI and web backend read/write the same sheet via `SpreadsheetClient`; the processor fetches Scryfall data and writes prices back to the sheet. The data model is storage-agnostic (Card, PriceHistory, SheetRow); Sheets columns are mapped by position. There is no notion of "user" beyond config; a single Sheet is assumed. Moving to PostgreSQL and OAuth-based import allows any user to connect their Google account, import their sheet once (or occasionally), and manage the collection entirely inside the app with full CRUD. Constraints: keep core (`deckdex/`) free of HTTP/framework concerns; backend remains FastAPI; frontend remains React/Vite; no breaking change to the existing Card field set (we add storage, not new domain fields).

## Goals / Non-Goals

**Goals:**

- PostgreSQL as the primary store for cards; single place of truth for list, filter, CRUD, and price updates.
- Repository abstraction in core so the processor and any consumer read/write via an interface (Postgres implementation); Sheets used only during the import flow.
- OAuth 2.0 so any user can connect their Google account and import a chosen spreadsheet into Postgres (one-time or occasional migration).
- Local import (CSV/JSON) from the Settings screen for users who do not use Sheets.
- Full CRUD on cards (create, update, delete) via API and UI, in addition to existing list/filter.
- CLI and web can both run against the same Postgres DB without write conflicts.

**Non-Goals:**

- Full multi-tenant user accounts (login, registration, per-user collections). We only need a minimal "session" or anonymous identity to attach OAuth tokens and optionally scope data later; no auth required to use the dashboard if the app stays single-user/single-collection for now.
- Google Drive file picker UI (we can list spreadsheets by API and let the user choose; no need for the full Drive picker component initially).
- Price history storage in Postgres (optional later); design allows a `price_history` table but implementation can start with current price only on the card row.
- Migrating existing Sheet data automatically on first deploy; migration is a conscious "Import from Google Sheets" action in Settings.

## Decisions

### 1. Postgres schema and card identity

- **Decision:** One `cards` table with columns aligned to the existing Card model (name, english_name, type_line, description, keywords, mana_cost, cmc, colors, color_identity, power, toughness, rarity, set_id, set_name, set_number, release_date, edhrec_rank, scryfall_uri, price_eur, price_usd, price_usd_foil, last_price_update, game_strategy, tier). Add a surrogate primary key `id` (UUID or bigserial) for stable API identity; keep `name` (or Scryfall id if present) for display and optional uniqueness for import deduplication.
- **Rationale:** Existing API and UI use name and a flat list of fields; a 1:1 table keeps mapping simple. Surrogate id avoids coupling API to Sheet row index or Scryfall id as sole key.
- **Alternatives considered:** Use Scryfall id as primary key (clean but not all cards may have it before first Scryfall fetch); keep only name as key (fragile for renames). Surrogate id + optional scryfall_id column is a good balance.

### 2. Repository abstraction in core

- **Decision:** Introduce a `CollectionRepository` (or `CardStore`) interface in `deckdex/` with methods such as: get_all_cards(), get_cards_for_price_update() (name + current price), get_card_by_id(id), create(card), update(id, fields), delete(id), and optionally list_by_ids(). Implement `PostgresCollectionRepository` in core or in a dedicated `deckdex/storage/` (or backend) module that core depends on. The processor and API depend on this interface; `SpreadsheetClient` is not used for main read/write, only by an "import from Sheets" service that reads rows and calls repository.create() or a bulk_upsert.
- **Rationale:** Keeps core testable with in-memory/fake implementations; makes the switch from Sheets to Postgres a single implementation swap for the "source of truth" path.
- **Alternatives considered:** Keep SpreadsheetClient and add a "PostgresClient" with the same interface — possible but the Sheet API is row/range oriented, not CRUD-by-id; a repository interface is cleaner for create/update/delete.

### 3. OAuth flow and redirect target

- **Decision:** OAuth redirect_uri points to the **backend** (e.g. `https://api.example.com/api/auth/callback` or `http://localhost:8000/api/auth/callback`). Backend exchanges code for tokens, stores refresh token, then redirects the browser to the frontend (e.g. `http://localhost:5173/settings?import=sheets`) with optional session cookie. Frontend never sees the authorization code or tokens.
- **Rationale:** Simplifies Google Cloud configuration (one redirect URI per environment); keeps tokens only on the server; avoids CORS and token exposure in the SPA.
- **Alternatives considered:** Redirect to frontend with code, frontend POSTs code to backend — equivalent but adds a frontend route and one more round-trip; both are valid.

### 4. Token and session storage

- **Decision:** Store refresh token (encrypted or in a table with restricted access) keyed by a **session id** stored in an HTTP-only cookie. No full user table required initially: session id is created when the user first hits the app (or when they start OAuth). Session holds: session_id, google_refresh_token (encrypted), optional google_email, created_at, expires_at. Access token is obtained when needed (e.g. list sheets, import) and not persisted long-term.
- **Rationale:** Allows "any user with their Google account" without building login/registration; one browser = one session; revoking the cookie effectively disconnects Google for that session.
- **Alternatives considered:** Per-user table with user_id — better for multi-tenant later but out of scope; anonymous session is enough for single-collection use.

### 5. Import policy (Sheets or local)

- **Decision:** Default: **replace** the entire collection on import (delete all existing cards, insert imported rows). Document this clearly in the UI ("This will replace your current collection"). Option to support "merge" (upsert by name or scryfall_id) can be added later as an option in the import API.
- **Rationale:** Simplest to implement and reason about; avoids ambiguous merge rules in v1. Users doing a one-time migration expect "this sheet becomes my collection."
- **Alternatives considered:** Merge by name — requires conflict rules (e.g. last-write-wins); append-only — would grow unbounded without deduplication. Replace is clear and safe for the primary "migrate from Sheets" scenario.

### 6. Card CRUD API shape

- **Decision:** REST-style: `POST /api/cards` (body: card payload), `GET /api/cards/:id`, `PUT /api/cards/:id` or `PATCH /api/cards/:id`, `DELETE /api/cards/:id`. List remains `GET /api/cards` with query params (limit, offset, search, filters). Use the surrogate `id` (UUID or integer) in URLs for get/update/delete so names can change without breaking links.
- **Rationale:** Aligns with existing list/get-by-name; add create/update/delete by id for stability. Existing `GET /api/cards/{card_name}` can remain for backward compatibility or be deprecated in favor of get-by-id.

### 7. Settings screen and OAuth entry point

- **Decision:** New route `/settings` (or `/ajustes` if keeping Spanish in URLs). "Import from Google Sheets" shows "Connect with Google" when not connected; after OAuth callback, user is back on Settings with "Choose sheet" (backend calls Sheets API to list spreadsheets); user selects one (and worksheet if needed), clicks Import; backend reads sheet, maps columns to Card, replaces collection in Postgres. "Import from local" is a separate block: file upload or paste area, same replace policy.
- **Rationale:** Single place for all "data source" operations; OAuth entry is a link/button to `GET /api/auth/google`; no need for a separate "login" page.

### 8. Backend auth and import endpoints

- **Decision:** Endpoints as sketched in exploration: `GET /api/auth/google` (redirect to Google), `GET /api/auth/callback` (exchange code, store token, redirect to frontend), `GET /api/auth/status` (returns { connected: bool, email?: string }), `POST /api/auth/logout` (invalidate session/token). `GET /api/google/sheets` (list spreadsheets/worksheets for the connected account), `POST /api/import/sheets` (body: spreadsheet_id, worksheet_id or range; backend reads via Sheets API, maps to cards, replace in DB). `POST /api/import/upload` or `POST /api/import/file` for CSV/JSON upload; same replace policy.
- **Rationale:** Keeps auth and import in one place; frontend only triggers redirects and calls these APIs; no token handling in the browser.

### 9. Scryfall credentials in app settings

- **Decision:** Scryfall credentials are stored as **JSON content** in app settings (e.g. `data/settings.json`), not as a file path. Backend exposes `GET /api/settings/scryfall-credentials` (returns { configured: boolean }; raw JSON not returned) and `PUT /api/settings/scryfall-credentials` (body: { credentials: object | null }). When using Postgres, the processor does **not** create a SpreadsheetClient for the update_prices path, so Google credentials are not required for price updates. When Google credentials are needed (e.g. import from Sheets) and the file is missing, the backend returns a clear message (e.g. "Google API credentials not configured") instead of a raw file-not-found error.
- **Rationale:** Users can configure Scryfall from the UI without placing files on the server; backend remembers credentials for the next run. Avoids confusing Errno 2 when only updating prices with Postgres.

### 10. Process and update_prices job concurrency

- **Decision:** A **full process** job and an **update_prices** job may run **in parallel**. Only one job of each type at a time: 409 Conflict when starting a second full process while one is running, or a second update_prices while one is running.
- **Rationale:** Users may want to refresh prices while a full process is running (or vice versa); per-type locking avoids unnecessary blocking.

### 11. Process scope (all cards vs new/incomplete only)

- **Decision:** Full process job accepts a **scope** in the request body: `"all"` (default) or `"new_only"`. When `scope=new_only`, the processor runs only on cards that have a name but no type_line (cards added with just the name). Repository provides `get_cards_for_process(only_incomplete=True)` for this. Frontend offers a dropdown when triggering "Process Cards": "New added cards (with only the name)" and "All cards".
- **Rationale:** After adding a few new cards manually, users can enrich only those without reprocessing the entire collection.

## Risks / Trade-offs

- **[Risk] OAuth consent screen verification:** Google may require app verification for sensitive scopes or large user counts. **Mitigation:** Use minimal scope (e.g. `spreadsheets.readonly` or `drive.readonly`); document that for personal/small use verification may not be required; plan for verification if the app grows.
- **[Risk] Token storage compromise:** If the DB or session store is compromised, refresh tokens could be used to access users' Sheets. **Mitigation:** Store refresh tokens encrypted at rest; use short-lived access tokens; support "disconnect" so users can revoke access from Google and we clear the token.
- **[Risk] Import replaces collection without undo:** User might accidentally replace a large collection. **Mitigation:** Clear UI warning ("This will replace your current collection"); optional future: backup export before replace or "confirm with typing collection size."
- **[Trade-off] No multi-user:** Session-scoped Google link means one collection per deployment (or per session). Supporting multiple users with separate collections would require a user model and scoping cards by user_id; deferred.

## Migration Plan

1. **Add Postgres and schema:** Introduce PostgreSQL (local/docker and config); add migration (e.g. Alembic or SQL scripts) creating `cards` table and, if needed, `sessions` (or equivalent) for OAuth. Do not remove Sheet code yet.
2. **Repository and wiring:** Implement `PostgresCollectionRepository` and wire it in the backend for GET/POST/PUT/DELETE cards; keep existing list endpoint reading from repository. Processor not yet switched.
3. **OAuth and import from Sheets:** Implement auth endpoints, session/token storage, and Sheets listing + import endpoint; implement Settings screen with "Import from Google Sheets" flow. Users can populate Postgres via import.
4. **Switch processor and CLI:** Change MagicCardProcessor (and CLI) to use the repository for reading card list and writing price updates; remove or bypass Sheet writes in the main path. Optional: keep CLI flag to read from Sheet for one-off migration if needed.
5. **CRUD UI:** Add create/edit/delete card in the dashboard (or cards view); wire to new API.
6. **Deprecate Sheet as source of truth:** Update docs and config; mark Sheet-based config as "legacy" or "import only." Remove "do not run CLI and web simultaneously" from architecture spec.
7. **Rollback:** If critical issues arise, feature-flag or config can point the repository back to a Sheet adapter (if one is kept) or restore from DB backup; Postgres is the new source of truth so rollback implies restoring a DB snapshot and redeploying.

## Open Questions

- **Multi-collection or single collection:** If the app remains single-user, one collection per instance is enough. If we later add users, should cards be scoped by a user_id (or session_id) from the start? Schema can add a nullable `owner_id` or `session_id` column to cards to allow future scoping without a big migration.
- **Price history:** Store only current price on `cards` for v1, or add a `price_history` table and write a row on each update? Design allows either; decision can be made during implementation.
- **Local import format:** Agree on exact CSV column names or headers (match Sheet column names) and JSON shape (array of Card-like objects) so backend and docs are consistent.
