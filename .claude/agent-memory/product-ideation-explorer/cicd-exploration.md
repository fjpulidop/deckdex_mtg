# CI/CD Pipeline Exploration for DeckDex MTG

**Date:** 2026-03-06
**Status:** Exploration complete

---

## Current State Assessment

### What Exists

| Area | Status | Details |
|------|--------|---------|
| GitHub Workflows | **NONE** | No `.github/` directory at all |
| Pre-commit hooks | **NONE** | No `.pre-commit-config.yaml` |
| Makefile | **NONE** | No task runner |
| Python linter | **NONE** | No ruff, flake8, mypy, black, isort configured |
| Python version pin | **NONE** | No `.python-version` file (local env is Python 3.14.3, Docker uses 3.11) |
| Backend tests | **YES** | pytest with 20 test files in `tests/`, configured in `pyproject.toml` |
| Backend coverage | **CONFIGURED** | `pytest-cov` in requirements, coverage config in `pyproject.toml` (fail_under=0) |
| Frontend tests | **YES** | Vitest + jsdom + @testing-library/react, 4 test files |
| Frontend lint | **YES** | ESLint 9 flat config with typescript-eslint + react-hooks + react-refresh |
| Frontend type check | **YES** | `tsc -b` runs as part of `npm run build` |
| Playwright (E2E) | **CONFIGURED** | playwright.config.ts exists, but `e2e/` directory is empty (no tests written) |
| Docker | **YES** | docker-compose.yml with 3 services (db, backend, frontend), separate Dockerfiles |
| DB migrations | **YES** | Raw SQL files in `migrations/`, run via `scripts/setup_db.py` |

### Key Configuration Details

**pyproject.toml (pytest)**
- testpaths: `["tests"]`
- Markers: `slow` (external services), `integration` (API w/ TestClient)
- Coverage source: `backend`, `deckdex`; omits tests and migrations
- `fail_under = 0` (no minimum coverage enforced)

**Frontend (package.json scripts)**
- `build`: `tsc -b && vite build` (type check + bundle)
- `lint`: `eslint .`
- `test`: `vitest run`
- `test:watch`: `vitest`

**Vitest config**
- Environment: jsdom
- Setup: `src/test/setup.ts` (imports jest-dom matchers)
- Pattern: `src/**/__tests__/**/*.test.{ts,tsx}`

**Docker**
- Backend: Python 3.11-slim, installs deps, runs migrations on start
- Frontend: Node 20-alpine, dev server (NOT a production build)
- DB: postgres:15-alpine with healthcheck

---

## Prioritized CI/CD Improvements

### Tier 1: Foundation (Do First)

#### 1. Basic CI Workflow - Backend Tests
**What:** GitHub Actions workflow that runs `pytest tests/` on push/PR to main.
- Python 3.11 matrix (match Docker)
- PostgreSQL service container for integration tests
- Install deps from requirements.txt + requirements-api.txt
- Run with `--tb=short -q` (matching pyproject.toml addopts)

| Metric | Rating |
|--------|--------|
| **Impact** | **HIGH** - Catch regressions before merge. 20 test files already exist. |
| **Effort** | **LOW** - Standard GHA pattern, service container for Postgres is well-documented. |

#### 2. Basic CI Workflow - Frontend Checks
**What:** GitHub Actions job (same workflow) that runs lint + type check + unit tests.
- `npm ci` then `npm run lint`, `npm run build` (includes tsc), `npm run test`
- Node 20 (match Dockerfile)

| Metric | Rating |
|--------|--------|
| **Impact** | **HIGH** - TypeScript errors and lint issues caught automatically. |
| **Effort** | **LOW** - Three npm commands, no special infra needed. |

#### 3. Add Ruff for Python Linting
**What:** Add `ruff` to requirements, configure in `pyproject.toml`, add to CI workflow.
- Ruff is fast, replaces flake8+isort+black in one tool
- Start with default rules, adjust over time
- Run `ruff check` and `ruff format --check` in CI

| Metric | Rating |
|--------|--------|
| **Impact** | **HIGH** - Zero Python linting today means inconsistent code style across contributors. |
| **Effort** | **LOW** - Single dependency, minimal config. May need initial `ruff format .` to baseline. |

---

### Tier 2: Quality Gates (Do Next)

#### 4. Coverage Reporting with Threshold
**What:** Run pytest with `--cov` flag, upload to Codecov or just enforce minimum.
- Start with a realistic threshold (e.g., fail_under=40, whatever current coverage is)
- Gradually increase as test coverage improves
- Consider separate thresholds for `backend/` and `deckdex/`

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Prevents coverage from silently declining. Testing exploration found significant gaps (import routes, insights service, importers all at 0%). |
| **Effort** | **LOW** - Already configured in pyproject.toml, just need to set fail_under > 0 and add `--cov` flag. |

#### 5. Pin Python Version (.python-version)
**What:** Add `.python-version` file with `3.11` to match Docker.
- Local dev uses 3.14.3 but Docker uses 3.11-slim -- this is a real risk
- CI should test on 3.11 to match production
- Consider also testing 3.12 for forward-compat

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Version mismatch between local (3.14) and Docker (3.11) could cause subtle bugs. |
| **Effort** | **LOW** - One file. |

#### 6. Dependency Caching in CI
**What:** Cache pip and npm dependencies between CI runs.
- `actions/setup-python` with pip cache
- `actions/setup-node` with npm cache
- Reduces CI time from ~2-3 min to ~30-60s for cached runs

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Faster CI = faster feedback loop. |
| **Effort** | **LOW** - Built-in to setup actions. |

---

### Tier 3: Safety Nets (Medium Priority)

#### 7. Pre-commit Hooks
**What:** Add `.pre-commit-config.yaml` with ruff + eslint + type checks.
- Catch issues before they even hit CI
- Optional: developer can skip with `--no-verify` when needed
- Hooks: ruff check, ruff format, trailing whitespace, yaml check

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Shifts feedback left, but only benefits developers who install hooks. |
| **Effort** | **LOW** - Standard pre-commit setup. |

#### 8. Docker Build Validation
**What:** CI job that builds both Docker images to verify they don't break.
- `docker build -f backend/Dockerfile .`
- `docker build -f frontend/Dockerfile frontend/`
- Does NOT need to run the containers, just verify the build succeeds

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Frontend Dockerfile runs dev server (not production); backend Dockerfile has real build logic. |
| **Effort** | **LOW** - Two docker build commands. |

#### 9. MyPy Type Checking (Python)
**What:** Add mypy for gradual type checking of Python code.
- Start with `--ignore-missing-imports` and limited scope
- Focus on `deckdex/` core first, then `backend/`
- Run in CI but initially as warning-only (don't block PRs)

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Python type safety is valuable but the codebase may not be annotated enough for it to be immediately useful. |
| **Effort** | **MEDIUM** - Likely many existing type errors to triage initially. |

---

### Tier 4: Advanced (Do Later)

#### 10. Branch Protection Rules
**What:** Require CI to pass before merging to main.
- GitHub branch protection: require status checks
- Require up-to-date branches before merging
- No configuration needed in CI -- this is a GitHub repo setting

| Metric | Rating |
|--------|--------|
| **Impact** | **HIGH** - Without this, CI is advisory only. Broken code can still merge. |
| **Effort** | **LOW** - GitHub settings toggle. But putting it in Tier 4 because it depends on having stable CI first (Tier 1). |

#### 11. E2E Tests with Playwright
**What:** Write and run Playwright E2E tests in CI.
- Config exists but `e2e/` directory is empty
- Requires full stack running (backend + frontend + DB)
- Use docker-compose for CI E2E, or manage services individually

| Metric | Rating |
|--------|--------|
| **Impact** | **HIGH** (once tests exist) - Currently **LOW** because there are zero E2E tests to run. |
| **Effort** | **HIGH** - Need to write tests first, then CI needs docker-compose or multi-service orchestration. |

#### 12. Automated Dependency Updates (Dependabot/Renovate)
**What:** Auto-PRs for dependency updates.
- Python (requirements.txt) and Node (package.json)
- Dependabot is built into GitHub, zero config beyond a yaml file
- Group updates to reduce PR noise

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Security patches auto-proposed. But adds PR noise for a solo/small project. |
| **Effort** | **LOW** - Single `dependabot.yml` config file. |

#### 13. Production Docker Build for Frontend
**What:** Change frontend Dockerfile to produce a production build (nginx serving static files) instead of running dev server.
- Current frontend Dockerfile runs `npm run dev` -- this is NOT production-ready
- Production: multi-stage build with `npm run build` then nginx
- Add to CI to verify production build works

| Metric | Rating |
|--------|--------|
| **Impact** | **MEDIUM** - Matters when deploying, not critical for CI today. |
| **Effort** | **MEDIUM** - New Dockerfile.prod or multi-stage Dockerfile. |

#### 14. Security Scanning
**What:** Run `npm audit`, `pip audit`, or Snyk/Trivy for vulnerability scanning.
- GitHub's built-in Dependabot security alerts handle some of this
- Trivy can scan Docker images too

| Metric | Rating |
|--------|--------|
| **Impact** | **LOW** (for localhost app) - DeckDex is localhost-only, no auth, so attack surface is limited. |
| **Effort** | **LOW** - Simple GHA additions. |

---

## Recommended Implementation Order

### Phase 1: Get CI Running (1-2 hours)

Create `.github/workflows/ci.yml` with two jobs:

**Job 1: `backend`**
```
- Setup Python 3.11
- Start PostgreSQL service container
- pip install requirements
- ruff check + ruff format --check
- pytest tests/ --cov --cov-report=term
```

**Job 2: `frontend`**
```
- Setup Node 20
- npm ci (with cache)
- npm run lint
- npm run build (includes tsc type check)
- npm run test
```

Trigger: push to main, pull_request to main.

### Phase 2: Harden (30 min)

- Set `fail_under` in pyproject.toml to current coverage level
- Add `.python-version` file
- Enable branch protection requiring CI to pass

### Phase 3: Developer Experience (30 min)

- Add pre-commit hooks config
- Add a Makefile with common tasks (`make test`, `make lint`, `make ci`)
- Add dependabot.yml

### Phase 4: Future

- E2E tests (requires writing tests first)
- Production Docker build
- MyPy (requires type annotation effort)

---

## Architecture Considerations

### PostgreSQL in CI
- Backend tests use `TestClient(app)` which bootstraps the FastAPI app
- Some tests likely need a real DB (integration tests marked with `@pytest.mark.integration`)
- Options: (a) Use PostgreSQL service container, (b) SQLite for unit tests, (c) Mock DB layer
- **Recommendation:** PostgreSQL service container -- matches production, tests are already written against it

### Rate Limiting in Tests
- slowapi rate limiter is present in backend
- Testing exploration noted this as a blocker for import route tests
- CI should set env var to disable rate limiting, or tests should mock/override the limiter

### Scryfall API in Tests
- Tests should NEVER hit Scryfall (per testing conventions)
- CI environment has no internet access to Scryfall anyway (unless explicitly allowed)
- All external API calls should be mocked (testing convention already in place)

### Environment Variables in CI
- `DATABASE_URL`: Set to service container Postgres URL
- `GOOGLE_API_CREDENTIALS`, `OPENAI_API_KEY`: Not needed (mocked in tests)
- `JWT_SECRET_KEY`: Set a dummy value for tests
- `.env` file: Should NOT be committed; use GitHub secrets for any real values

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Tests fail in CI but pass locally (env diff) | HIGH | Pin Python 3.11, use Postgres service container |
| CI is slow (>5 min) | MEDIUM | Cache deps, split jobs, run in parallel |
| Flaky tests block PRs | LOW | Currently no flaky test reports; monitor after enabling |
| Ruff finds hundreds of issues in existing code | MEDIUM | Run `ruff format .` and `ruff check --fix .` once to baseline |
| Coverage threshold blocks valid PRs | LOW | Start with current coverage level, increase gradually |

---

## Summary: Top 5 Actions by Priority

1. **Create `.github/workflows/ci.yml`** with backend (pytest + ruff) and frontend (lint + build + test) jobs -- Impact: HIGH, Effort: LOW
2. **Add ruff** to Python toolchain -- Impact: HIGH, Effort: LOW
3. **Pin Python to 3.11** via `.python-version` -- Impact: MEDIUM, Effort: LOW
4. **Set coverage fail_under** to current baseline -- Impact: MEDIUM, Effort: LOW
5. **Enable branch protection** on main after CI is stable -- Impact: HIGH, Effort: LOW
