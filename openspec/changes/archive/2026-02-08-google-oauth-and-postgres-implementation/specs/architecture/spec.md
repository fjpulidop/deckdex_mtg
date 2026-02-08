# Architecture (Delta)

Data flow and components updated for Postgres as primary store, OAuth and Settings, and CLI + web both writing to the same DB.

## ADDED Requirements

### Requirement: PostgreSQL SHALL be the primary store for the card collection

The system SHALL use PostgreSQL as the primary store for cards. The CLI and web backend SHALL read and write the collection via a repository (or adapter) backed by Postgres. Google Sheets SHALL NOT be used as the source of truth for the main application flow; Sheets SHALL be used only as an optional import source (see google-oauth-import and settings-screen).

#### Scenario: Collection read from Postgres
- **WHEN** the API or processor needs the list of cards
- **THEN** the data SHALL be read from PostgreSQL via the collection repository

#### Scenario: Collection write to Postgres
- **WHEN** the API or processor creates, updates, or deletes a card or updates prices
- **THEN** the change SHALL be written to PostgreSQL via the collection repository

### Requirement: OAuth and Settings SHALL be part of the architecture

The system SHALL include components for Google OAuth (initiate, callback, token storage, refresh) and a Settings screen in the frontend. OAuth SHALL allow any user to connect their Google account for the purpose of importing from their spreadsheets. Details SHALL be specified in google-oauth-import and settings-screen.

#### Scenario: OAuth flow available
- **WHEN** the user wishes to import from Google Sheets
- **THEN** the system SHALL support initiating OAuth and completing the flow so the user's tokens are stored on the backend and the user can list and import their sheets

### Requirement: CLI and web SHALL be able to run concurrently when using Postgres

When the application uses PostgreSQL as the collection store, the CLI and web processes SHALL be allowed to run simultaneously. Both SHALL read from and write to the same Postgres database; the previous constraint "do not run CLI process and web process simultaneously" SHALL no longer apply when the primary store is Postgres.

#### Scenario: CLI and web both writing to Postgres
- **WHEN** the web app is running and the user runs the CLI (e.g. update prices) against the same Postgres
- **THEN** both SHALL operate without conflicting; writes SHALL be coordinated by the database

## MODIFIED Requirements

### Requirement: Data flow SHALL use Postgres and repository for collection

**Previous:** Config load → ProcessorConfig. Read card names from sheet → queue → per card: cache/Scryfall/optional OpenAI → price delta → batched sheet updates (incremental).

**Updated:** Config load (YAML → ENV → CLI) → ProcessorConfig. Read card names from collection repository (Postgres) → queue → per card: cache/Scryfall/optional OpenAI → price delta → write updated prices to repository (Postgres). Optional import path: user connects Google via OAuth → user selects sheet → backend reads sheet → backend writes to repository (replace collection). Google Sheets is used only during that import flow, not for main read/write.

#### Scenario: Main data flow uses repository
- **WHEN** the processor runs (e.g. update prices) or the API serves cards
- **THEN** the system SHALL read from and write to the collection repository (Postgres), not from Google Sheets

#### Scenario: Import flow uses Sheets only to populate Postgres
- **WHEN** the user imports from Google Sheets via Settings
- **THEN** the backend SHALL read from the user's sheet via Sheets API and SHALL write the result into Postgres (replace collection); Sheets is not the ongoing source of truth

### Requirement: Deployment and concurrency SHALL allow CLI and web with Postgres

**Previous:** Concurrency: do not run CLI process and web process simultaneously (writes conflict). Reads are safe. Sheets limit 600 req/min.

**Updated:** When using PostgreSQL as the primary store: CLI and web MAY run simultaneously; both read and write the same Postgres database. Google Sheets rate limits apply only when using the optional Google Sheets import feature. When using a legacy Sheet-only setup (if still supported), the previous concurrency constraint MAY still apply.

#### Scenario: Concurrency with Postgres
- **WHEN** the primary store is PostgreSQL
- **THEN** the system SHALL allow the CLI and web to run at the same time without document-level write conflicts

## REMOVED Requirements

None. Existing component list and layer boundaries remain; Goals and Integration are extended by the above ADDED and MODIFIED requirements.
