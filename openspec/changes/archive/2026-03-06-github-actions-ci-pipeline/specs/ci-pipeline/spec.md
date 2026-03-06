## ADDED Requirements

### Requirement: GitHub Actions CI workflow exists
The project SHALL have a `.github/workflows/ci.yml` file that defines automated CI checks for every push and pull request targeting the `main` branch.

#### Scenario: Workflow triggers on push to main
- **WHEN** code is pushed to the `main` branch
- **THEN** the CI workflow runs both the `backend` and `frontend` jobs automatically

#### Scenario: Workflow triggers on pull request to main
- **WHEN** a pull request targets the `main` branch
- **THEN** the CI workflow runs both the `backend` and `frontend` jobs automatically

---

### Requirement: Backend CI job runs Python 3.11
The `backend` CI job SHALL use Python 3.11 to match the Docker production environment.

#### Scenario: Backend job uses correct Python version
- **WHEN** the `backend` CI job runs
- **THEN** Python 3.11 is configured via `actions/setup-python` with `python-version: "3.11"`

---

### Requirement: Backend CI job has a PostgreSQL service container
The `backend` CI job SHALL spin up a PostgreSQL 15 service container with a health check so that integration tests can connect to a real database.

#### Scenario: PostgreSQL service is healthy before tests run
- **WHEN** the `backend` CI job starts
- **THEN** a `postgres:15` service container is started with health check (`pg_isready`) and tests wait until it is healthy before proceeding

#### Scenario: DATABASE_URL points to the service container
- **WHEN** the `backend` CI job runs tests
- **THEN** the `DATABASE_URL` environment variable is set to `postgresql://postgres:postgres@localhost:5432/deckdex_test`

---

### Requirement: Backend CI job caches pip dependencies
The `backend` CI job SHALL cache pip dependencies keyed to `requirements.txt` and `backend/requirements-api.txt` to reduce install time on subsequent runs.

#### Scenario: Cache hit skips re-downloading packages
- **WHEN** requirements files have not changed since the last successful run
- **THEN** `actions/setup-python` restores the cached pip packages instead of downloading them

---

### Requirement: Backend CI job runs ruff linting
The `backend` CI job SHALL run `ruff check .` to enforce Python style rules and fail if any violations are found.

#### Scenario: Ruff finds no violations
- **WHEN** `ruff check .` is run and no violations exist
- **THEN** the step passes and the job continues

#### Scenario: Ruff finds violations
- **WHEN** `ruff check .` is run and violations exist
- **THEN** the step fails and the CI job reports failure

---

### Requirement: Backend CI job runs ruff format check
The `backend` CI job SHALL run `ruff format --check .` to ensure all Python files are formatted according to project style.

#### Scenario: All files are already formatted
- **WHEN** `ruff format --check .` is run and no formatting differences exist
- **THEN** the step passes

#### Scenario: Unformatted file detected
- **WHEN** `ruff format --check .` is run and a file differs from canonical format
- **THEN** the step fails and shows which files need formatting

---

### Requirement: Backend CI job runs pytest with coverage
The `backend` CI job SHALL run `pytest tests/ -q --tb=short --cov=backend --cov=deckdex --cov-report=term` and fail if coverage falls below the configured threshold.

#### Scenario: All tests pass and coverage meets threshold
- **WHEN** pytest runs and all tests pass and coverage >= `fail_under` in `pyproject.toml`
- **THEN** the step passes

#### Scenario: Test failure blocks CI
- **WHEN** any test fails
- **THEN** the pytest step fails and the CI job reports failure

#### Scenario: Coverage below threshold blocks CI
- **WHEN** pytest runs successfully but coverage falls below `fail_under`
- **THEN** the pytest step fails with a coverage report

---

### Requirement: Backend CI job runs database migrations
The `backend` CI job SHALL run `python scripts/setup_db.py` before running tests to ensure the database schema is up to date.

#### Scenario: Migrations run against the service container
- **WHEN** the `backend` CI job runs
- **THEN** `python scripts/setup_db.py` is executed against the PostgreSQL service container before pytest runs

---

### Requirement: Frontend CI job runs on Node 20
The `frontend` CI job SHALL use Node 20 to match the frontend Dockerfile.

#### Scenario: Frontend job uses correct Node version
- **WHEN** the `frontend` CI job runs
- **THEN** Node 20 is configured via `actions/setup-node` with `node-version: "20"`

---

### Requirement: Frontend CI job caches npm dependencies
The `frontend` CI job SHALL cache npm packages keyed to `frontend/package-lock.json` to reduce install time.

#### Scenario: Cache hit skips re-downloading packages
- **WHEN** `package-lock.json` has not changed since the last successful run
- **THEN** `actions/setup-node` restores cached npm packages

---

### Requirement: Frontend CI job runs ESLint
The `frontend` CI job SHALL run `npm run lint` in the `frontend/` directory and fail if any lint errors are found.

#### Scenario: No lint errors
- **WHEN** `npm run lint` runs and ESLint finds no errors
- **THEN** the step passes

#### Scenario: Lint errors found
- **WHEN** `npm run lint` runs and ESLint reports errors
- **THEN** the step fails and reports which files/rules failed

---

### Requirement: Frontend CI job runs TypeScript type check
The `frontend` CI job SHALL run `npx tsc --noEmit` to verify type correctness without producing a build artifact.

#### Scenario: No type errors
- **WHEN** `npx tsc --noEmit` runs and TypeScript finds no type errors
- **THEN** the step passes

#### Scenario: Type errors found
- **WHEN** `npx tsc --noEmit` runs and TypeScript reports errors
- **THEN** the step fails and reports which files have type errors

---

### Requirement: Frontend CI job runs Vitest unit tests
The `frontend` CI job SHALL run `npm run test` (which calls `vitest run`) and fail if any tests fail.

#### Scenario: All tests pass
- **WHEN** `npm run test` runs and all Vitest tests pass
- **THEN** the step passes

#### Scenario: Test failure blocks CI
- **WHEN** any Vitest test fails
- **THEN** the step fails with the test failure report

---

### Requirement: Python version is pinned to 3.11
The repository SHALL contain a `.python-version` file with the content `3.11` to match the Docker production environment and signal the intended Python version to tooling.

#### Scenario: .python-version file exists with correct content
- **WHEN** a developer checks out the repository
- **THEN** `.python-version` exists and contains `3.11`

---

### Requirement: Ruff is configured in pyproject.toml
The project SHALL have a `[tool.ruff]` section in `pyproject.toml` configuring target Python version, line length, selected rule sets, and quote style.

#### Scenario: Ruff config is present
- **WHEN** `ruff check .` or `ruff format .` is run
- **THEN** ruff reads `[tool.ruff]` from `pyproject.toml` and applies project-specific settings

---

### Requirement: Coverage threshold is non-zero
The `fail_under` value in `pyproject.toml`'s `[tool.coverage.report]` section SHALL be set to a realistic non-zero value reflecting actual current test coverage.

#### Scenario: Coverage meets threshold
- **WHEN** pytest runs with `--cov` and coverage is above `fail_under`
- **THEN** pytest exits successfully

#### Scenario: Coverage falls below threshold
- **WHEN** pytest runs with `--cov` and coverage drops below `fail_under`
- **THEN** pytest exits with a non-zero exit code

---

### Requirement: .dockerignore excludes dev artifacts
The repository SHALL have a `.dockerignore` file that excludes `.git`, `node_modules`, `venv`, `__pycache__`, `*.pyc`, `.env`, `.claude`, and `openspec` from Docker build contexts.

#### Scenario: .dockerignore is present
- **WHEN** `docker build` is run
- **THEN** `.dockerignore` is present and excluded directories are not sent to the Docker daemon
