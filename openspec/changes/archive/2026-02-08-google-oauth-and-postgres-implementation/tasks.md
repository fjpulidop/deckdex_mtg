# Tasks: Google OAuth and PostgreSQL Implementation

## 1. PostgreSQL and schema

- [x] 1.1 Add PostgreSQL dependency and connection config (e.g. DATABASE_URL or host/port/db in config.yaml and env)
- [x] 1.2 Create migrations (Alembic or SQL) for `cards` table with surrogate id and columns aligned to Card model
- [x] 1.3 Create session/token storage table (or schema) for OAuth refresh tokens keyed by session id
- [x] 1.4 Document and run migrations so the app can connect and use the schema

## 2. Repository abstraction

- [x] 2.1 Define CollectionRepository (or CardStore) interface in deckdex with get_all_cards, get_cards_for_price_update, get_card_by_id, create, update, delete
- [x] 2.2 Implement PostgresCollectionRepository that fulfills the interface using the cards table
- [x] 2.3 Add dependency injection or factory so backend and processor can obtain the repository instance

## 3. Backend: collection from Postgres

- [x] 3.1 Replace get_cached_collection (or equivalent) to read from repository instead of SpreadsheetClient
- [x] 3.2 Ensure GET /api/cards and GET /api/cards/{card_name} use repository; add GET /api/cards/{id} by surrogate id
- [x] 3.3 Ensure GET /api/stats computes from Postgres (with optional cache)
- [x] 3.4 Remove or adapt 503 Sheets-quota handling for normal card/stats reads

## 4. Backend: OAuth and session

- [x] 4.1 Implement session middleware or cookie-based session id (create on first request or on OAuth start)
- [x] 4.2 Implement GET /api/auth/google (build Google OAuth URL with state, redirect)
- [x] 4.3 Implement GET /api/auth/callback (exchange code for tokens, store refresh token, redirect to frontend /settings)
- [x] 4.4 Implement GET /api/auth/status (return connected and optional email from session)
- [x] 4.5 Implement POST /api/auth/logout (invalidate session / clear Google tokens)
- [x] 4.6 Add Google OAuth client config (client_id, client_secret, redirect_uri) via env

## 5. Backend: import endpoints

- [x] 5.1 Implement GET /api/google/sheets (use stored access/refresh token to list spreadsheets and worksheets)
- [x] 5.2 Implement POST /api/import/sheets (body: spreadsheet_id, worksheet_id/range; read sheet, map to cards, replace collection in Postgres)
- [x] 5.3 Implement POST /api/import/file or /api/import/upload (accept CSV/JSON, parse, map to cards, replace collection; return count or validation error)

## 6. Backend: card CRUD

- [x] 6.1 Implement POST /api/cards (create card, return with id)
- [x] 6.2 Implement GET /api/cards/{id} (by surrogate id, 404 if not found)
- [x] 6.3 Implement PUT or PATCH /api/cards/{id} (update card, return updated or 404)
- [x] 6.4 Implement DELETE /api/cards/{id} (delete card, 204/200 or 404)

## 7. Processor and CLI

- [x] 7.1 Change MagicCardProcessor to read card list from repository (get_cards_for_price_update) instead of SpreadsheetClient
- [x] 7.2 Change MagicCardProcessor to write price updates through repository instead of Sheet
- [x] 7.3 Wire processor (and CLI) to use Postgres config and repository; ensure CLI can run against same DB as web
- [x] 7.4 Keep SpreadsheetClient usage only in the import-from-Sheets service (backend), not in main processor path

## 8. Frontend: Settings page

- [x] 8.1 Add Settings route (e.g. /settings) and navigation entry
- [x] 8.2 Build "Import from Google Sheets" block: Connect with Google (link to GET /api/auth/google), connected status, list sheets (GET /api/google/sheets), select sheet and Import (POST /api/import/sheets), show result
- [x] 8.3 Build "Import from local file" block: file upload (and optional paste), call POST /api/import/file, show result
- [x] 8.4 Handle OAuth callback redirect (user lands on /settings?import=sheets after callback); call GET /api/auth/status on load

## 9. Frontend: card CRUD UI

- [x] 9.1 Add "Add card" control; form or modal with card fields; submit to POST /api/cards and refresh list
- [x] 9.2 Add edit control per row/card; form or modal pre-filled; submit to PATCH/PUT /api/cards/{id} and refresh
- [x] 9.3 Add delete control per row/card with confirmation; call DELETE /api/cards/{id} and refresh list
- [x] 9.4 Ensure table/list uses card id where needed for update and delete

## 10. Cleanup and docs

- [x] 10.1 Update architecture spec (or docs) to state Postgres as primary store and CLI+web concurrency allowed
- [x] 10.2 Mark Sheet-based config as legacy/import-only in config and README; document OAuth env vars for import
- [x] 10.3 Remove or relax "do not run CLI and web simultaneously" from deployment docs

## 11. Scryfall credentials in Settings

- [x] 11.1 Backend: do not create SpreadsheetClient when using Postgres (update_prices path); return clear error when Google credentials file is missing (not Errno 2)
- [x] 11.2 Backend: store Scryfall credentials JSON internally (app settings file); GET/PUT /api/settings/scryfall-credentials; backend remembers stored JSON for next run
- [x] 11.3 When Scryfall credentials are required and not configured, return message "Scryfall credentials not configured" (not file-not-found)
- [x] 11.4 Frontend Settings: section to paste or upload credentials JSON, Save/Clear; show configured/not configured status

## 12. Process scope and job concurrency

- [x] 12.1 Backend: allow one full process job and one update_prices job to run in parallel; 409 only when same job type is already running
- [x] 12.2 Repository: get_cards_for_process(only_incomplete) — cards with name but no type_line (new/incomplete)
- [x] 12.3 Backend: POST /api/process body { limit?, scope: "all" | "new_only" }; config.process_scope passed to processor
- [x] 12.4 Processor: when process_scope=new_only, process only cards from get_cards_for_process(only_incomplete=True)
- [x] 12.5 Frontend: Process Cards button opens dropdown with "New added cards (with only the name)" and "All cards"; send scope in request
