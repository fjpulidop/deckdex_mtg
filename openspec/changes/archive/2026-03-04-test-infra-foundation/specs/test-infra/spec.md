## ADDED Requirements

### Requirement: Pytest configuration in pyproject.toml
The project SHALL have a `pyproject.toml` at the repo root with `[tool.pytest.ini_options]` configuring test paths, strict markers, and short traceback output.

#### Scenario: pytest discovers tests without explicit path
- **WHEN** a developer runs `pytest` from the repo root without arguments
- **THEN** pytest discovers and runs all tests in the `tests/` directory

#### Scenario: Undeclared marker causes failure
- **WHEN** a test uses `@pytest.mark.foo` and `foo` is not declared in `pyproject.toml`
- **THEN** pytest fails with an error about the unknown marker

### Requirement: Custom test markers
The project SHALL declare `slow` and `integration` markers in `pyproject.toml` so developers can selectively run or skip test subsets.

#### Scenario: Run only fast tests
- **WHEN** a developer runs `pytest -m "not slow"`
- **THEN** only tests not marked with `@pytest.mark.slow` are executed

#### Scenario: Run only integration tests
- **WHEN** a developer runs `pytest -m integration`
- **THEN** only tests marked with `@pytest.mark.integration` are executed

### Requirement: Coverage configuration
The project SHALL have `[tool.coverage.run]` and `[tool.coverage.report]` sections in `pyproject.toml` targeting the `backend` and `deckdex` source directories.

#### Scenario: Coverage report on demand
- **WHEN** a developer runs `pytest --cov`
- **THEN** a coverage report is printed showing line-by-line coverage for `backend/` and `deckdex/`, excluding `tests/` and `migrations/`

#### Scenario: Coverage not enforced by default
- **WHEN** a developer runs `pytest` without `--cov`
- **THEN** no coverage report is generated and no coverage threshold is checked

### Requirement: pytest-cov dependency
The project SHALL include `pytest-cov` in its Python dependencies.

#### Scenario: pytest-cov is installable
- **WHEN** a developer runs `pip install -r requirements.txt`
- **THEN** `pytest-cov` is installed and available

### Requirement: Shared test client helper
`tests/conftest.py` SHALL provide a `make_test_client()` function that returns a FastAPI `TestClient` with the auth dependency overridden to a test user (user_id=1).

#### Scenario: Helper returns configured client
- **WHEN** test code calls `make_test_client()`
- **THEN** the returned `TestClient` has `get_current_user_id` overridden and can make authenticated API requests

### Requirement: Shared sample card data
`tests/conftest.py` SHALL export a `SAMPLE_CARDS` list containing representative card dictionaries usable across test files.

#### Scenario: Sample cards available for import
- **WHEN** a test file does `from conftest import SAMPLE_CARDS`
- **THEN** it receives a list of card dictionaries with fields: name, rarity, type, set_name, price, color_identity

### Requirement: Pytest fixtures for new tests
`tests/conftest.py` SHALL provide pytest fixtures (`client`, `sample_cards`) that new pytest-style tests can use via dependency injection.

#### Scenario: New test uses client fixture
- **WHEN** a new pytest-style test function declares a `client` parameter
- **THEN** it receives a configured `TestClient` instance with auth overridden

#### Scenario: New test uses sample_cards fixture
- **WHEN** a new pytest-style test function declares a `sample_cards` parameter
- **THEN** it receives a fresh copy of the sample cards list
