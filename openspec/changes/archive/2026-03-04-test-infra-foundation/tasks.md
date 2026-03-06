## 1. Dependencies

- [x] 1.1 Add `pytest-cov` to `requirements.txt` alongside existing `pytest` entry

## 2. Pytest & Coverage Configuration

- [x] 2.1 Create `pyproject.toml` with `[tool.pytest.ini_options]`: testpaths, strict-markers, short tracebacks, quiet output
- [x] 2.2 Add marker declarations: `slow`, `integration`
- [x] 2.3 Add `[tool.coverage.run]` section: source = backend + deckdex, omit tests + migrations
- [x] 2.4 Add `[tool.coverage.report]` section: show_missing, fail_under=0, exclude_lines

## 3. Shared Test Infrastructure

- [x] 3.1 Create `tests/conftest.py` with `make_test_client()` helper function (TestClient + auth override)
- [x] 3.2 Add `SAMPLE_CARDS` constant with representative card data including color_identity
- [x] 3.3 Add pytest fixtures: `client` (module-scoped), `sample_cards` (returns fresh copy)

## 4. Verification

- [x] 4.1 Run `pytest` and confirm all existing tests pass unchanged
- [x] 4.2 Run `pytest --cov` and capture baseline coverage number
