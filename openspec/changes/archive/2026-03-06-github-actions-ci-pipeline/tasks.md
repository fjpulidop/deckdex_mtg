## 1. Python Toolchain Setup

- [x] 1.1 Add `ruff` and `pytest-cov` to `requirements.txt`
- [x] 1.2 Add `[tool.ruff]`, `[tool.ruff.lint]`, and `[tool.ruff.format]` sections to `pyproject.toml` with target-version="py311", line-length=120, select=["E","F","I","W"], ignore=["E501"], quote-style="double"
- [x] 1.3 Run `ruff check --fix .` and `ruff format .` to baseline the codebase (formatting only, no logic changes)
- [x] 1.4 Add `.python-version` file with content `3.11`

## 2. Coverage Threshold

- [x] 2.1 Run `pytest tests/ --cov=backend --cov=deckdex --cov-report=term -q` to determine current coverage percentage
- [x] 2.2 Update `fail_under` in `pyproject.toml`'s `[tool.coverage.report]` section to a value 2-5% below the measured coverage (minimum 1)

## 3. Docker Build Cleanup

- [x] 3.1 Create `.dockerignore` file excluding: `.git`, `node_modules`, `venv`, `__pycache__`, `*.pyc`, `.env`, `.claude`, `openspec`

## 4. GitHub Actions Workflow

- [x] 4.1 Create `.github/workflows/` directory
- [x] 4.2 Create `.github/workflows/ci.yml` with trigger on push/PR to `main`
- [x] 4.3 Add `backend` job: Python 3.11, PostgreSQL 15 service container, pip cache, install deps, run migrations, ruff check, ruff format --check, pytest with coverage
- [x] 4.4 Add `frontend` job: Node 20, npm cache, `npm ci`, `npm run lint`, `npx tsc --noEmit`, `npm run test`

## 5. Verification

- [x] 5.1 Run `cd frontend && npx tsc --noEmit` locally and confirm it passes
- [x] 5.2 Run `pytest tests/ -q --tb=short` locally and confirm all tests pass
- [x] 5.3 Run `ruff check .` locally and confirm no violations
