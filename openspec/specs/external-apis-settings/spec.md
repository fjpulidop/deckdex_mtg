# External APIs Settings

Per-user settings for controlling external API access. Provides a `user_settings` table (JSONB), a `UserSettingsRepository`, REST endpoints for reading/writing preferences, a frontend toggle in SettingsModal, and catalog-first lookup refactoring across all Scryfall call points. Default: Scryfall disabled (catalog-only). Generic structure supports future API toggles (e.g. OpenAI).

## Requirements

### Requirement: user_settings table

The system SHALL store per-user preferences in a `user_settings` table with JSONB. Each user has at most one row. The JSONB structure supports nested keys for extensibility.

#### Scenario: Table schema

- **WHEN** the migration has been applied
- **THEN** the `user_settings` table SHALL exist with columns: `user_id` (integer, UNIQUE, NOT NULL, FK to `users.id`), `settings` (JSONB, NOT NULL, DEFAULT `'{}'`), `created_at` (TIMESTAMPTZ, DEFAULT now()), `updated_at` (TIMESTAMPTZ, DEFAULT now())

#### Scenario: Default for new user

- **WHEN** a user has no row in `user_settings`
- **THEN** the system SHALL treat all settings as their defaults
- **AND** `external_apis.scryfall_enabled` SHALL default to `false`

#### Scenario: Row created on first write

- **WHEN** a user updates their external APIs settings for the first time
- **THEN** the system SHALL insert a new row in `user_settings` with `user_id` and the provided settings (upsert)
- **AND** subsequent updates SHALL update the existing row and set `updated_at` to current timestamp

### Requirement: UserSettingsRepository

The system SHALL provide a `UserSettingsRepository` class in `deckdex/storage/user_settings_repository.py` for all `user_settings` table operations. No raw SQL outside this repository.

#### Scenario: Read external APIs settings

- **WHEN** `get_external_apis_settings(user_id)` is called
- **THEN** the repository SHALL return a dict with at least `{"scryfall_enabled": bool}`
- **AND** if the user has no row or the key is missing, return `{"scryfall_enabled": false}`

#### Scenario: Write external APIs settings

- **WHEN** `update_external_apis_settings(user_id, {"scryfall_enabled": true})` is called
- **THEN** the repository SHALL upsert the user's row, merging `external_apis` into the existing JSONB settings
- **AND** return the updated external APIs settings dict

### Requirement: GET /api/settings/external-apis endpoint

The system SHALL expose an authenticated endpoint to read the current user's external API preferences.

#### Scenario: Read settings (user has settings)

- **WHEN** an authenticated user calls `GET /api/settings/external-apis`
- **THEN** the system SHALL return HTTP 200 with body `{"scryfall_enabled": <bool>}`
- **AND** the value reflects what the user previously saved

#### Scenario: Read settings (user has no settings)

- **WHEN** an authenticated user with no `user_settings` row calls `GET /api/settings/external-apis`
- **THEN** the system SHALL return HTTP 200 with body `{"scryfall_enabled": false}`

#### Scenario: Unauthenticated request

- **WHEN** an unauthenticated client calls `GET /api/settings/external-apis`
- **THEN** the system SHALL return HTTP 401

### Requirement: PUT /api/settings/external-apis endpoint

The system SHALL expose an authenticated endpoint to update the current user's external API preferences.

#### Scenario: Enable Scryfall

- **WHEN** an authenticated user calls `PUT /api/settings/external-apis` with body `{"scryfall_enabled": true}`
- **THEN** the system SHALL persist `scryfall_enabled = true` for that user
- **AND** return HTTP 200 with body `{"scryfall_enabled": true}`

#### Scenario: Disable Scryfall

- **WHEN** an authenticated user calls `PUT /api/settings/external-apis` with body `{"scryfall_enabled": false}`
- **THEN** the system SHALL persist `scryfall_enabled = false` for that user
- **AND** return HTTP 200 with body `{"scryfall_enabled": false}`

#### Scenario: Invalid body

- **WHEN** a client sends a PUT request with missing or invalid `scryfall_enabled` field
- **THEN** the system SHALL return HTTP 422 (validation error)

### Requirement: Settings UI - "APIs externas" section

The SettingsModal SHALL include a new "APIs externas" section with a toggle for Scryfall. The section is generic and prepared for future API toggles.

#### Scenario: Section visible in SettingsModal

- **WHEN** the user opens the SettingsModal
- **THEN** the modal SHALL display an "APIs externas" section
- **AND** the section SHALL appear between the "Scryfall API credentials" section and the "Importar coleccion" section

#### Scenario: Scryfall toggle loads current state

- **WHEN** the "APIs externas" section renders
- **THEN** the system SHALL call `GET /api/settings/external-apis`
- **AND** display a labeled toggle for "Scryfall" reflecting the current `scryfall_enabled` value
- **AND** show a description explaining that enabling Scryfall allows the app to make external API calls as a fallback when cards are not found in the local catalog

#### Scenario: Toggle Scryfall on

- **WHEN** the user toggles Scryfall to "on"
- **THEN** the system SHALL call `PUT /api/settings/external-apis` with `{"scryfall_enabled": true}`
- **AND** update the toggle state to reflect the saved value

#### Scenario: Toggle Scryfall off

- **WHEN** the user toggles Scryfall to "off"
- **THEN** the system SHALL call `PUT /api/settings/external-apis` with `{"scryfall_enabled": false}`
- **AND** update the toggle state to reflect the saved value

#### Scenario: Error saving toggle

- **WHEN** the PUT request fails
- **THEN** the system SHALL show an error message in the modal
- **AND** revert the toggle to its previous state

### Requirement: Catalog-first autocomplete

The `suggest_card_names()` function in `backend/api/services/scryfall_service.py` SHALL check the local catalog first. Scryfall autocomplete is used only as a fallback when the user has enabled it.

#### Scenario: Cards found in catalog

- **WHEN** `suggest_card_names(q, user_id)` is called
- **AND** `catalog_cards` contains cards matching the query
- **THEN** the system SHALL return card names from the catalog
- **AND** SHALL NOT make a Scryfall API request

#### Scenario: No catalog match, Scryfall enabled

- **WHEN** `suggest_card_names(q, user_id)` is called
- **AND** `catalog_cards` contains no cards matching the query
- **AND** the user has `scryfall_enabled = true`
- **THEN** the system SHALL fall back to the Scryfall autocomplete API
- **AND** return the Scryfall results

#### Scenario: No catalog match, Scryfall disabled

- **WHEN** `suggest_card_names(q, user_id)` is called
- **AND** `catalog_cards` contains no cards matching the query
- **AND** the user has `scryfall_enabled = false`
- **THEN** the system SHALL return an empty list
- **AND** SHALL NOT make a Scryfall API request

### Requirement: Catalog-first card resolution

The `resolve_card_by_name()` function in `backend/api/services/scryfall_service.py` SHALL check the local catalog first. Scryfall lookup is used only as a fallback when the user has enabled it.

#### Scenario: Card found in catalog

- **WHEN** `resolve_card_by_name(name, user_id)` is called
- **AND** `catalog_cards` contains an exact or fuzzy match for the name
- **THEN** the system SHALL return card data from the catalog
- **AND** SHALL NOT make a Scryfall API request

#### Scenario: Card not in catalog, Scryfall enabled

- **WHEN** `resolve_card_by_name(name, user_id)` is called
- **AND** the card is not found in `catalog_cards`
- **AND** the user has `scryfall_enabled = true`
- **THEN** the system SHALL fall back to Scryfall `search_card()` via `CardFetcher`
- **AND** return the Scryfall result mapped to the card model

#### Scenario: Card not in catalog, Scryfall disabled

- **WHEN** `resolve_card_by_name(name, user_id)` is called
- **AND** the card is not found in `catalog_cards`
- **AND** the user has `scryfall_enabled = false`
- **THEN** the system SHALL raise `CardNotFoundError` with message indicating the card is not in the catalog and Scryfall is disabled

### Requirement: Catalog-first image fetch

The `get_card_image()` function in `backend/api/services/card_image_service.py` SHALL check the ImageStore first. Scryfall image download is used only as a fallback when the user has enabled it.

#### Scenario: Image found in ImageStore

- **WHEN** `get_card_image(card_id, user_id)` is called
- **AND** the card's image exists in `ImageStore` (by `scryfall_id`)
- **THEN** the system SHALL return the image from ImageStore
- **AND** SHALL NOT make a Scryfall API request

#### Scenario: Image not in store, Scryfall enabled

- **WHEN** `get_card_image(card_id, user_id)` is called
- **AND** the image is not in ImageStore
- **AND** the user has `scryfall_enabled = true`
- **THEN** the system SHALL fall back to downloading the image from Scryfall
- **AND** store the downloaded image in ImageStore for future use

#### Scenario: Image not in store, Scryfall disabled

- **WHEN** `get_card_image(card_id, user_id)` is called
- **AND** the image is not in ImageStore
- **AND** the user has `scryfall_enabled = false`
- **THEN** the system SHALL raise `FileNotFoundError` with a message indicating the image is not available locally and Scryfall is disabled

### Requirement: Catalog-first import enrichment

The `_run_import()` method in `backend/api/services/importer_service.py` SHALL enrich cards from the catalog first. Scryfall enrichment is used only as a fallback when the user has enabled it. The `CardFetcher` SHALL be instantiated with `(config.scryfall, config.openai)` arguments.

#### Scenario: CardFetcher instantiation
- **WHEN** `_run_import()` creates a `CardFetcher` for Scryfall fallback
- **THEN** it SHALL pass `config.scryfall` and `config.openai` as arguments (not the entire config object)
- **AND** the CardFetcher SHALL be functional for `search_card()` calls

#### Scenario: Card found in catalog during import

- **WHEN** `_run_import()` processes a parsed card
- **AND** the card name is found in `catalog_cards`
- **THEN** the system SHALL use catalog data for enrichment
- **AND** SHALL NOT make a Scryfall API request for that card

#### Scenario: Card not in catalog during import, Scryfall enabled

- **WHEN** `_run_import()` processes a parsed card
- **AND** the card is not in `catalog_cards`
- **AND** the importing user has `scryfall_enabled = true`
- **THEN** the system SHALL fall back to Scryfall `search_card()` for enrichment

#### Scenario: Card not in catalog during import, Scryfall disabled

- **WHEN** `_run_import()` processes a parsed card
- **AND** the card is not in `catalog_cards`
- **AND** the importing user has `scryfall_enabled = false`
- **THEN** the system SHALL add the card name to the `not_found` list in the import result
- **AND** SHALL NOT make a Scryfall API request for that card

### Requirement: Frontend API client methods

The frontend API client (`frontend/src/api/client.ts`) SHALL provide methods for the external APIs settings endpoints.

#### Scenario: getExternalApisSettings method

- **WHEN** the frontend calls `api.getExternalApisSettings()`
- **THEN** it SHALL send `GET /api/settings/external-apis` with auth headers
- **AND** return `{ scryfall_enabled: boolean }`

#### Scenario: updateExternalApisSettings method

- **WHEN** the frontend calls `api.updateExternalApisSettings({ scryfall_enabled: boolean })`
- **THEN** it SHALL send `PUT /api/settings/external-apis` with the JSON body and auth headers
- **AND** return `{ scryfall_enabled: boolean }`

### Requirement: External APIs integration tests
The system SHALL have integration tests for the external-apis-settings flow using FastAPI TestClient with mocked dependencies.

#### Scenario: GET settings endpoint tested
- **WHEN** `GET /api/settings/external-apis` is called via TestClient with authentication
- **THEN** the test SHALL verify 200 response with `{"scryfall_enabled": bool}`

#### Scenario: PUT settings endpoint tested
- **WHEN** `PUT /api/settings/external-apis` is called with `{"scryfall_enabled": true}`
- **THEN** the test SHALL verify 200 response with the updated value

#### Scenario: CardFetcher bug regression test
- **WHEN** `_run_import()` is called and a card is not in the catalog
- **AND** Scryfall is enabled
- **THEN** the test SHALL verify `CardFetcher` is instantiated with `(config.scryfall, config.openai)` (not `config` alone)
