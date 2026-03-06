## Context

DeckDex has 20 test files in `tests/` and a frontend with ESLint + Vitest configured, but no CI pipeline exists. The project uses Python 3.11 in Docker but local dev runs 3.14, which is a real risk. No Python linter is configured at all. The CI pipeline must run against PostgreSQL (not SQLite) because tests use `TestClient(app)` which bootstraps the real FastAPI app with DB.

Current state:
- `pyproject.toml` has pytest config with `fail_under = 0` (no coverage enforcement)
- `frontend/package.json` has `lint`, `test`, and `build` (which includes `tsc -b`) scripts
- `scripts/setup_db.py` exists for running migrations
- No `.github/` directory at all

## Goals / Non-Goals

**Goals:**
- Run backend tests (pytest) + ruff lint/format checks on every push and PR to main
- Run frontend lint (ESLint), type check (tsc), and unit tests (Vitest) on every push and PR to main
- Enforce a non-zero coverage threshold
- Pin Python version to 3.11 to match Docker
- Baseline the codebase with ruff formatting (no logic changes)
- Cache pip and npm deps for fast CI runs

**Non-Goals:**
- E2E tests (Playwright, no tests exist)
- Pre-commit hooks
- MyPy type checking
- Dependabot / automated dependency updates
- Branch protection rules (GitHub settings, not code)
- Production Docker build changes

## Decisions

### Decision 1: Use GitHub Actions (not CircleCI/Jenkins/etc.)

**Choice:** GitHub Actions natively in `.github/workflows/ci.yml`

**Rationale:** Project is already on GitHub. Zero infra cost for open source. Native integration with PR status checks. Free tier is sufficient for this workload.

**Alternatives considered:** CircleCI (requires third-party account), local Makefile only (no automatic enforcement).

---

### Decision 2: PostgreSQL service container (not SQLite in-memory)

**Choice:** Use `services: postgres:15` in the GitHub Actions job

**Rationale:** Tests are written against PostgreSQL (uses `DATABASE_URL` env var). Using SQLite would require conditional imports or significant test refactoring. The exploration confirmed tests use `TestClient(app)` which boots the real app.

**Alternatives considered:** Mock the DB layer (too invasive — would require rewriting existing tests), use SQLite (incompatible with existing test patterns).

---

### Decision 3: Two parallel jobs, not matrix strategy

**Choice:** Two separate named jobs (`backend` and `frontend`) in the same workflow file

**Rationale:** Backend and frontend have completely different toolchains (Python vs Node). Parallel execution is faster than sequential. Named jobs give clearer status checks for branch protection. Matrix strategy is better suited for testing multiple versions of the same thing.

**Alternatives considered:** Single job (too slow, harder to read), separate workflow files (harder to see overall CI status at a glance).

---

### Decision 4: `ruff` over `flake8 + black + isort`

**Choice:** Add `ruff` as the single Python linter/formatter

**Rationale:** Ruff replaces flake8 + isort + pyupgrade + black in one extremely fast tool. The project has zero Python linting today, so starting fresh with ruff is the right move.

**Alternatives considered:** `black + flake8 + isort` (3 separate tools, slower, more config).

---

### Decision 5: Run `tsc --noEmit` not `npm run build` for type checking

**Choice:** Use `npx tsc --noEmit` in CI instead of `npm run build`

**Rationale:** `npm run build` runs `tsc -b && vite build` which also bundles the app — unnecessary for CI and slower. `tsc --noEmit` gives us pure type safety checking with faster feedback.

**Alternatives considered:** `npm run build` (slower, builds what we don't need in CI).

---

### Decision 6: Set `fail_under` to current baseline, not 0

**Choice:** Run pytest with coverage first, set `fail_under` slightly below current coverage

**Rationale:** Starting with `fail_under = 0` is meaningless. We need a real floor that prevents coverage regressions. The exploration noted significant test gaps (import routes, insights at 0%), so the actual number should be realistic.

**Alternatives considered:** Start at 0 and gradually increase (too permissive, never enforced), start at 80% (too aggressive, will block valid PRs immediately).

## Risks / Trade-offs

- **[Risk] Ruff finds formatting issues across the entire codebase** → Mitigation: Run `ruff format .` and `ruff check --fix .` as a one-time baseline commit before enabling CI. This is purely cosmetic — no logic changes.

- **[Risk] Tests fail in CI due to missing env vars** → Mitigation: CI job sets `DATABASE_URL` to the service container, and any other required env vars (e.g., dummy `JWT_SECRET_KEY`) as job-level env.

- **[Risk] `scripts/setup_db.py` may not be idempotent** → Mitigation: The CI DB is fresh on every run (service container), so migration scripts always start from a clean state. Non-issue.

- **[Risk] Coverage threshold blocks valid PRs** → Mitigation: Set `fail_under` to 2-5% below current actual coverage to give headroom.

- **[Risk] CI is slow** → Mitigation: Dependency caching via `actions/setup-python` pip cache and `actions/setup-node` npm cache reduces subsequent runs from ~3min to ~1min.

## Migration Plan

1. Run `ruff format .` and `ruff check --fix .` locally (baseline commit, no logic changes)
2. Add `ruff` and `pytest-cov` to `requirements.txt`
3. Add `[tool.ruff]` config to `pyproject.toml` and set realistic `fail_under`
4. Add `.python-version` with `3.11`
5. Add `.dockerignore`
6. Create `.github/workflows/ci.yml`
7. Push to a PR — verify both jobs pass
8. Enable branch protection requiring CI to pass (manual GitHub step)

## Open Questions

- None: all decisions made based on exploration findings.
