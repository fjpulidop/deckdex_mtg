# Test Infrastructure

Pytest configuration, shared test helpers, coverage tooling, and fixtures for the DeckDex test suite.

### Requirements

- **Pytest configuration:** The project SHALL have a `pyproject.toml` at the repo root with `[tool.pytest.ini_options]` configuring test paths, strict markers, and short traceback output. Running `pytest` from repo root discovers all tests in `tests/`. Undeclared markers cause failure.
- **Custom markers:** The project SHALL declare `slow` and `integration` markers in `pyproject.toml`. Run fast tests with `pytest -m "not slow"`, integration tests with `pytest -m integration`.
- **Coverage configuration:** The project SHALL have `[tool.coverage.run]` and `[tool.coverage.report]` sections targeting `backend` and `deckdex` source directories, excluding `tests/` and `migrations/`. Coverage runs on demand with `pytest --cov`, not by default.
- **pytest-cov dependency:** The project SHALL include `pytest-cov` in `requirements.txt`.
- **Shared test client helper:** `tests/conftest.py` SHALL provide `make_test_client()` returning a FastAPI `TestClient` with auth dependency overridden to test user (user_id=1).
- **Shared sample card data:** `tests/conftest.py` SHALL export `SAMPLE_CARDS` list with representative card dictionaries (name, rarity, type, set_name, price, color_identity).
- **Pytest fixtures:** `tests/conftest.py` SHALL provide `client` (module-scoped TestClient) and `sample_cards` (fresh copy) fixtures for new pytest-style tests.
