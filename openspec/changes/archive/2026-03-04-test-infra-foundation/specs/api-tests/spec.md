## MODIFIED Requirements

### Requirement: Shared test infrastructure
Automated tests for backend API (health, stats, cards list) with mocked collection; no DB or Sheets. Tests SHALL be able to use shared helpers and fixtures from `tests/conftest.py` instead of duplicating boilerplate (TestClient setup, auth override, sample data).

#### Scenario: Existing tests pass unchanged
- **WHEN** the test suite is run after adding `conftest.py`
- **THEN** all existing API tests pass without any modifications to their files

#### Scenario: New API tests use shared fixtures
- **WHEN** a developer writes a new API test
- **THEN** they can use the `client` fixture or `make_test_client()` helper instead of repeating the TestClient setup boilerplate
