# Proposal: Google OAuth and PostgreSQL Implementation

## Why

The app currently uses Google Sheets as the single source of truth for the card collection. That creates a hard dependency on Google, quota limits, and prevents users from managing their data fully inside the app. Moving the collection into PostgreSQL and letting any user import from their own Google account (via OAuth) gives a self-contained app, one-time migration from Sheets, and full CRUD on cards without leaving the product.

## What Changes

- **PostgreSQL as primary store** for cards and (optionally) price history. Schema, migrations, and connection config; core and API read/write the DB instead of Sheets.
- **Repository abstraction** in core: a collection/card store interface with a Postgres implementation, so the processor and API are not tied to a specific backend. Sheets client remains only for the import flow.
- **Settings screen** (new route, e.g. `/settings`): dedicated area for “Import from Google Sheets” and “Import from local file”. Replaces the need to configure a single shared Sheet.
- **Google OAuth 2.0** so any user can connect their own Google account, list their spreadsheets, and import a chosen sheet into Postgres (one-time or occasional). Tokens stored securely on the backend; no service-account-only limitation.
- **Import from local**: upload or paste CSV/JSON to import cards into Postgres from the Settings screen.
- **Full CRUD on cards**: create, read, update, delete via API and UI (dashboard or cards view). List and filter remain; add create, edit, and delete actions.
- **CLI and web** both use Postgres when running; the “do not run CLI and web at the same time” constraint (due to conflicting Sheet writes) is removed. **BREAKING** for current “single Sheet” deployment: existing Sheet-based setup becomes optional (import source only).
- **Processor / update-prices**: reads card list from Postgres, fetches prices from Scryfall, writes updated prices back to Postgres (no Sheet writes in the main path).

## Capabilities

### New Capabilities

- **postgres-storage**: PostgreSQL as primary store for cards; schema, migrations, connection config; repository (or adapter) abstraction so core and API use the DB instead of SpreadsheetClient as source of truth.
- **google-oauth-import**: OAuth 2.0 for any user; connect Google account; list user’s spreadsheets/worksheets; import a chosen sheet into Postgres (mapping columns to card model); token storage and refresh on the backend.
- **local-import**: Import cards from local file (CSV or JSON) into Postgres via the Settings screen (upload or paste); column/field mapping consistent with card model.
- **settings-screen**: Settings page (new route) with “Import from Google Sheets” (connect, choose sheet, import) and “Import from local file” (upload/paste); clear states for connected/disconnected and import result.
- **cards-crud**: Full CRUD API (create, update, delete card by id or stable key) and UI (add card, edit card, delete card) in addition to existing list and filter.

### Modified Capabilities

- **architecture**: Data flow and components: Postgres as primary store; OAuth and Settings as new components; CLI and web both write to the same DB; Sheets only as optional import source.
- **web-api-backend**: Data served from Postgres (not Sheets); new auth endpoints (e.g. initiate OAuth, callback, status, logout); new import endpoints (list sheets, run import from Sheets, import from file); new CRUD endpoints for cards (create, update, delete); error handling and response shapes for new flows.
- **web-dashboard-ui**: New Settings screen and navigation entry; “Import from Google Sheets” and “Import from local” flows with clear states; CRUD actions on cards (create, edit, delete) in the dashboard or cards view.

## Impact

- **Core (`deckdex/)`**: New repository/adapter for collection backed by Postgres; MagicCardProcessor and price-update logic use this store instead of SpreadsheetClient for main read/write. SpreadsheetClient (or a thin wrapper) used only when performing a Sheets import.
- **Backend (`backend/api/)`**: New routes for auth (OAuth initiate, callback, status, logout), Google Sheets listing and import, local file import, and card CRUD; dependency on Postgres and session/token storage; collection data from DB with optional caching strategy.
- **Frontend**: New Settings route and components; OAuth redirect handling; card create/edit/delete UI (forms or modals) and API calls.
- **CLI**: Can be updated to use Postgres for update-prices and any card operations, or remain Sheet-only for legacy; either way, no conflict with web when both use Postgres.
- **Deployment**: PostgreSQL becomes a required (or default) dependency for the app; Google credentials only needed for the OAuth import feature (client ID/secret for OAuth, not only service account).
- **Existing specs**: architecture, web-api-backend, and web-dashboard-ui will need delta specs to reflect the new requirements and flows.
