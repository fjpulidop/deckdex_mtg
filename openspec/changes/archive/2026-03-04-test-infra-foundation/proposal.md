## Why

The test suite has ~162 tests but no shared infrastructure: no `conftest.py` (boilerplate repeated in 4+ files), no coverage tooling (nobody knows actual coverage), and no pytest configuration file. This friction discourages writing new tests and makes it impossible to track quality trends. Setting up the foundation now enables confident iteration on the codebase.

## What Changes

- Add `[tool.pytest.ini_options]` and `[tool.coverage.*]` sections to a new `pyproject.toml`
- Create `tests/conftest.py` with shared helpers (TestClient factory, auth override) and pytest fixtures for new tests — **without modifying existing test files**
- Add `pytest-cov` to backend test dependencies
- Measure and document the baseline coverage number

## Non-goals

- Migrating existing `unittest.TestCase` tests to pytest-style — that happens organically over time
- Increasing coverage (this change is infra only, not new tests)
- Frontend test infrastructure changes
- CI/CD pipeline setup

## Capabilities

### New Capabilities
- `test-infra`: pytest configuration, shared conftest.py, coverage tooling setup

### Modified Capabilities
- `api-tests`: Adding shared fixtures and helpers that existing API tests can optionally adopt

## Impact

- New file: `pyproject.toml` (project root)
- New file: `tests/conftest.py`
- Modified: `requirements.txt` or `backend/requirements-api.txt` (add `pytest-cov`)
- No changes to existing test files
- No changes to application code
