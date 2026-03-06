## ADDED Requirements

### Requirement: Backend tests run in CI against PostgreSQL
The backend test suite SHALL be executable in a CI environment where a PostgreSQL 15 service container is available via `DATABASE_URL`, without requiring any local `.env` file or real external service credentials.

#### Scenario: Tests pass with only CI-provided environment variables
- **WHEN** pytest runs in CI with `DATABASE_URL` pointing to the PostgreSQL service container
- **THEN** all tests pass without requiring `GOOGLE_API_CREDENTIALS` or `OPENAI_API_KEY`

#### Scenario: No tests call real external APIs
- **WHEN** any test involving Scryfall or OpenAI runs
- **THEN** the external API call is mocked and never reaches the real service

---

### Requirement: Coverage threshold is enforced in CI
The backend test run in CI SHALL enforce a non-zero minimum coverage threshold via `fail_under` in `pyproject.toml`. The threshold SHALL be set to a value that reflects the actual current coverage baseline.

#### Scenario: Coverage enforcement prevents regressions
- **WHEN** a code change removes test coverage
- **THEN** pytest exits with a non-zero code and CI reports a coverage failure

#### Scenario: Threshold is realistic at baseline
- **WHEN** CI first runs with the coverage threshold configured
- **THEN** the existing test suite meets the threshold without any test additions required
