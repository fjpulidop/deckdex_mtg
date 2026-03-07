## ADDED Requirements

### Requirement: Scryfall credentials GET returns configured=true when credentials exist
The system SHALL have HTTP integration tests verifying that `GET /api/settings/scryfall-credentials` returns `{"configured": true}` when `get_scryfall_credentials` returns a non-None value.

#### Scenario: Credentials present returns configured true
- **WHEN** an authenticated client sends `GET /api/settings/scryfall-credentials` and `get_scryfall_credentials` returns a dict
- **THEN** the response status SHALL be 200 and `configured` SHALL be `true`

### Requirement: Scryfall credentials GET returns configured=false when no credentials
The system SHALL have HTTP integration tests verifying that `GET /api/settings/scryfall-credentials` returns `{"configured": false}` when `get_scryfall_credentials` returns `None`.

#### Scenario: No credentials returns configured false
- **WHEN** an authenticated client sends `GET /api/settings/scryfall-credentials` and `get_scryfall_credentials` returns `None`
- **THEN** the response status SHALL be 200 and `configured` SHALL be `false`

### Requirement: Scryfall credentials PUT stores credentials and returns configured=true
The system SHALL have HTTP integration tests verifying that `PUT /api/settings/scryfall-credentials` with a non-null credentials body calls `set_scryfall_credentials` and returns `{"configured": true}`.

#### Scenario: PUT with credentials stores and returns true
- **WHEN** an authenticated client sends `PUT /api/settings/scryfall-credentials` with `{"credentials": {"key": "value"}}` and `get_scryfall_credentials` subsequently returns a non-None value
- **THEN** the response status SHALL be 200, `set_scryfall_credentials` SHALL have been called once, and `configured` SHALL be `true`

### Requirement: Scryfall credentials PUT with null clears credentials and returns configured=false
The system SHALL have HTTP integration tests verifying that `PUT /api/settings/scryfall-credentials` with `{"credentials": null}` calls `set_scryfall_credentials(None)` and returns `{"configured": false}`.

#### Scenario: PUT with null credentials clears and returns false
- **WHEN** an authenticated client sends `PUT /api/settings/scryfall-credentials` with `{"credentials": null}` and `get_scryfall_credentials` subsequently returns `None`
- **THEN** the response status SHALL be 200, `set_scryfall_credentials` SHALL have been called with `None`, and `configured` SHALL be `false`
