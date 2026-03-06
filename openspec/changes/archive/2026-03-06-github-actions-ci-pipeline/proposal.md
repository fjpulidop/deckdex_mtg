## Why

DeckDex has no CI pipeline — tests, linting, and type checks run only if developers remember to run them locally. This creates real risk: broken code can merge to main undetected, Python formatting is inconsistent (no linter configured), and there's a version mismatch between local dev (Python 3.14) and Docker production (Python 3.11).

## What Changes

- Add `.github/workflows/ci.yml` with two parallel jobs: `backend` and `frontend`
- `backend` job: runs ruff linting + pytest with coverage on every push/PR to main, against a PostgreSQL 15 service container
- `frontend` job: runs ESLint, TypeScript type-check (`tsc --noEmit`), and Vitest on every push/PR to main
- Add `ruff` to Python toolchain with `pyproject.toml` config; run baseline format/fix pass
- Add `.python-version` file pinned to `3.11` to match Docker
- Set a realistic `fail_under` coverage threshold in `pyproject.toml`
- Add `.dockerignore` file to exclude dev artifacts from Docker builds

## Capabilities

### New Capabilities
- `ci-pipeline`: GitHub Actions CI workflow with backend (pytest + ruff) and frontend (lint + typecheck + vitest) jobs, dependency caching, PostgreSQL service container, and coverage enforcement

### Modified Capabilities
- `api-tests`: Coverage threshold enforcement added; tests now run in CI against PostgreSQL service container

## Non-goals

- Pre-commit hooks (separate concern, low adoption)
- E2E tests with Playwright (no tests written yet)
- MyPy type checking for Python (requires significant annotation effort)
- Dependabot configuration
- Production Docker build changes
- Branch protection rules (GitHub settings, not code)

## Impact

- New file: `.github/workflows/ci.yml`
- New file: `.python-version`
- New file: `.dockerignore`
- Modified: `requirements.txt` — add `ruff`, `pytest-cov`
- Modified: `pyproject.toml` — add `[tool.ruff]` config, update `fail_under`
- CI will run `scripts/setup_db.py` for migrations (must exist and be runnable)
- All existing Python files will be reformatted by `ruff format` (no logic changes)
