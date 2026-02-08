# Postgres Storage

PostgreSQL as primary store for the card collection; repository abstraction so core and API are not tied to a specific backend.

## ADDED Requirements

### Requirement: Collection SHALL be stored in PostgreSQL

The system SHALL use PostgreSQL as the primary store for cards. The system SHALL provide a schema (e.g. a `cards` table) with columns aligned to the existing Card model (name, english_name, type_line, description, keywords, mana_cost, cmc, colors, color_identity, power, toughness, rarity, set_id, set_name, set_number, release_date, edhrec_rank, scryfall_uri, price fields, last_price_update, game_strategy, tier). The system SHALL use a surrogate primary key (e.g. UUID or bigserial) for stable API identity.

#### Scenario: Cards persisted in database
- **WHEN** a card is created or updated via the repository
- **THEN** the data SHALL be persisted in PostgreSQL and SHALL be readable by subsequent queries

#### Scenario: Surrogate id returned for new cards
- **WHEN** a new card is inserted
- **THEN** the system SHALL assign and return a stable id (surrogate key) usable for get/update/delete

### Requirement: Repository abstraction SHALL decouple core from storage

The system SHALL expose a collection repository (or card store) interface that supports at least: get all cards, get cards for price update (name + current price), get cards for process (optional only_incomplete: cards with name but no type_line), get card by id, create card, update card by id, delete card by id. The system SHALL provide a Postgres implementation of this interface. Core (processor) and API SHALL use the interface, not SpreadsheetClient, for primary read/write of the collection.

#### Scenario: Processor reads cards from repository
- **WHEN** the processor runs (e.g. update prices)
- **THEN** it SHALL obtain the card list from the repository interface, not directly from Google Sheets

#### Scenario: Processor writes price updates to repository
- **WHEN** the processor updates a card's price
- **THEN** it SHALL write the update through the repository interface to PostgreSQL

### Requirement: Schema and connection SHALL be configurable

The system SHALL support configuration for PostgreSQL connection (e.g. URL or host/port/db/user/password via config or environment). The system SHALL provide migrations (e.g. Alembic or SQL scripts) to create and evolve the schema; migrations SHALL be runnable independently of the application.

#### Scenario: Application connects using config
- **WHEN** the application starts with valid Postgres configuration
- **THEN** it SHALL connect to PostgreSQL and SHALL be able to read/write cards

#### Scenario: Missing or invalid Postgres config
- **WHEN** Postgres is required and configuration is missing or invalid
- **THEN** the system SHALL fail with a clear error indicating the configuration problem
