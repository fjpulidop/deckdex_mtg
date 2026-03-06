## Context

The test suite uses `unittest.TestCase` with `pytest` as runner. Four API test files repeat identical boilerplate: `TestClient` creation, auth dependency override, and sample card data. There is no `conftest.py`, no `pyproject.toml`, and no coverage tooling. The project has no visibility into actual test coverage.

## Goals / Non-Goals

**Goals:**
- Centralize pytest configuration in `pyproject.toml`
- Provide shared fixtures and helpers via `tests/conftest.py`
- Enable coverage measurement with `pytest-cov`
- Zero impact on existing tests (they must pass unchanged)

**Non-Goals:**
- Migrating existing tests from `unittest.TestCase` to pytest-style
- Writing new tests or increasing coverage numbers
- Frontend test infrastructure
- CI/CD integration

## Decisions

### 1. Configuration in `pyproject.toml` (not `pytest.ini` or `setup.cfg`)

Modern Python standard. Single file for pytest config + coverage config. The project has no `pyproject.toml` yet — this creates one with only test-related sections.

**Alternative considered:** `pytest.ini` — simpler but single-purpose. `pyproject.toml` is more future-proof and can host ruff, build config, etc. later.

### 2. Option B: helpers + fixtures coexisting with unittest.TestCase

`conftest.py` provides:
- **Helper functions** (e.g., `make_test_client()`, `SAMPLE_CARDS` constant) — usable from existing `unittest.TestCase` tests via import
- **pytest fixtures** (e.g., `client`, `sample_cards`) — for new pytest-style tests only

This avoids touching any existing test file. Existing tests can optionally import helpers to reduce their boilerplate, but are not required to change.

**Alternative considered:** Option A (migrate all tests to pytest-style first) — higher risk, no immediate value over Option B, blocks progress on infra.

### 3. `pytest-cov` added to `requirements.txt` (not `requirements-dev.txt`)

The project uses a flat `requirements.txt` for all Python deps. No separate dev requirements file exists (except `backend/requirements-api.txt` for backend-specific deps). Adding `pytest-cov` alongside the existing `pytest` entry keeps things consistent.

### 4. Coverage not in `addopts` — explicit invocation only

Running `pytest` stays fast for the dev loop. Running `pytest --cov` generates the coverage report when wanted. No forced overhead.

### 5. `fail_under = 0` initially

Measure first, set threshold later. Avoids an arbitrary number that either blocks work or is meaninglessly low.

### 6. Custom markers: `slow` and `integration`

Enables `pytest -m "not slow"` for fast feedback. Markers declared with `--strict-markers` to catch typos.

## Risks / Trade-offs

- **Two test styles coexist** → Acceptable trade-off. New tests use fixtures, old tests work as-is. Migration happens organically, not as a prerequisite.
- **`SAMPLE_CARDS` in conftest may diverge from copies in existing files** → The conftest version is canonical; existing files keep their copies until they adopt the shared one. No breakage.
- **`pyproject.toml` created for tests only** → Fine. Other tools (ruff, build) can add their sections later.
