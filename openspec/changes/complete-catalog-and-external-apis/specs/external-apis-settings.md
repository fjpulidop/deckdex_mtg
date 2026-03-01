# External APIs Settings — Delta Spec

## Changed Requirements

### Requirement: Catalog-first import enrichment (BUG FIX)

The `_run_import()` method in `importer_service.py` SHALL correctly instantiate `CardFetcher` with the proper config parameters.

#### Scenario: CardFetcher instantiation

- **WHEN** `_run_import()` creates a `CardFetcher` for Scryfall fallback
- **THEN** it SHALL pass `config.scryfall` and `config.openai` as arguments (not the entire config object)
- **AND** the CardFetcher SHALL be functional for `search_card()` calls

### Requirement: External APIs integration tests (NEW)

The system SHALL have integration tests for the external-apis-settings flow using FastAPI TestClient with mocked dependencies.

#### Scenario: GET settings endpoint tested

- **WHEN** `GET /api/settings/external-apis` is called via TestClient with authentication
- **THEN** the test SHALL verify 200 response with `{"scryfall_enabled": bool}`

#### Scenario: PUT settings endpoint tested

- **WHEN** `PUT /api/settings/external-apis` is called with `{"scryfall_enabled": true}`
- **THEN** the test SHALL verify 200 response with the updated value

#### Scenario: Unauthenticated request tested

- **WHEN** `GET /api/settings/external-apis` is called without authentication
- **THEN** the test SHALL verify 401 response

#### Scenario: CardFetcher bug regression test

- **WHEN** `_run_import()` is called and a card is not in the catalog
- **AND** Scryfall is enabled
- **THEN** the test SHALL verify `CardFetcher` is instantiated with `(config.scryfall, config.openai)` (not `config` alone)
