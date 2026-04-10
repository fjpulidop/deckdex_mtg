# Tasks: makefile-dev-environment

## Context

This change adds a single root-level `Makefile`. There are no backend, API,
frontend, or database schema changes. All tasks are `[core]` (project
tooling). The `.venv/` entry in `.gitignore` already exists at line 124 and
requires no action.

Relevant specs: `openspec/changes/makefile-dev-environment/specs/developer-workflow/spec.md`
Relevant design: `openspec/changes/makefile-dev-environment/design.md`

---

## Task 1 — Create root-level Makefile

**Layer**: `[core]`

**File**: `Makefile` (new file at project root)

**Description**:

Create the root-level `Makefile` with all ten targets as specified in
`design.md`. Follow the exact variable names, guard macros, recipe patterns,
and ordering documented there.

The file must contain, in order:

1. Header comment block identifying the file and listing available targets.
2. `.DEFAULT_GOAL := help`
3. Variable declarations:
   ```makefile
   VENV         := .venv
   PYTHON       := $(VENV)/bin/python
   PIP          := $(VENV)/bin/pip
   UVICORN      := $(VENV)/bin/uvicorn
   FRONTEND_DIR := frontend
   SYSTEM_PYTHON := $(shell command -v python3 2>/dev/null)
   ```
4. Guard macro definitions using `define`/`endef`:
   - `PYTHON_GUARD`: errors if `$(SYSTEM_PYTHON)` is empty.
   - `VENV_GUARD`: errors if `$(PYTHON)` does not exist as a file.
5. `.PHONY: install dev backend frontend test db-setup docker-up docker-down clean help`
6. `help` target — prints formatted usage to stdout (the `@echo` approach
   from `design.md`).
7. `install` target — creates venv if absent, upgrades pip, installs both
   requirements files in order, runs `npm install` in `frontend/`.
8. `dev` target — background backend with `BACKEND_PID`, SIGINT/TERM trap,
   foreground frontend, kill + wait on exit.
9. `backend` target — `$(UVICORN) backend.api.main:app --reload --port 8000`.
10. `frontend` target — checks `node_modules` exists, runs `npm run dev` from
    `$(FRONTEND_DIR)`.
11. `test` target — `$(PYTHON) -m pytest tests/ -v`.
12. `db-setup` target — `./scripts/setup_db.sh`.
13. `docker-up` target — `docker compose up --build`.
14. `docker-down` target — `docker compose down`.
15. `clean` target — `rm -rf $(VENV)`, then `find` for `__pycache__` and
    `*.pyc`, excluding `.venv/` paths.

**Critical implementation notes**:

- Use tab indentation for all recipe lines (Make requires tabs, not spaces).
- The `dev` target's entire recipe must be a single shell invocation (all
  lines connected with `;` and `\`) because shell variables like `BACKEND_PID`
  do not survive separate recipe lines.
- `make frontend` must delegate to `npm run dev` (not `npx vite`) to preserve
  the `NODE_OPTIONS` flag embedded in `package.json`.
- `make clean`'s `find` command must include `-not -path "./.venv/*"` to
  avoid descending into a partially-removed venv.

**Acceptance criteria** (DEVWF-01 through DEVWF-22):

- [ ] `make help` prints all ten targets with descriptions and returns exit 0.
- [ ] `make install` creates `.venv/`, installs all packages from
      `requirements.txt` and `backend/requirements-api.txt`, and runs
      `npm install` in `frontend/`.
- [ ] `make install` is idempotent: running it twice does not fail or destroy
      the venv.
- [ ] `make backend` starts uvicorn on port 8000 using `.venv/bin/uvicorn`.
- [ ] `make frontend` starts Vite via `npm run dev` from `frontend/`.
- [ ] `make test` runs pytest using `.venv/bin/python -m pytest tests/`.
- [ ] `make db-setup` delegates to `./scripts/setup_db.sh`.
- [ ] `make docker-up` runs `docker compose up --build`.
- [ ] `make docker-down` runs `docker compose down`.
- [ ] `make clean` removes `.venv/` and Python cache artifacts.
- [ ] `make install` (without python3) prints a clear error and exits non-zero.
- [ ] `make backend` (without `make install` first) prints "Run make install
      first" and exits non-zero.
- [ ] All targets are declared `.PHONY`.

---

## Task 2 — Verify Makefile syntax with dry-run

**Layer**: `[test]`

**File**: `Makefile` (read-only verification)

**Depends on**: Task 1

**Description**:

After creating the Makefile, verify its syntax is valid and that dry-run
parsing produces the expected command expansions.

Run:

```bash
# Verify syntax — Make will error on bad tab/space mix or syntax issues
make --dry-run help
make --dry-run install
make --dry-run backend
make --dry-run frontend
make --dry-run test
make --dry-run db-setup
make --dry-run docker-up
make --dry-run docker-down
make --dry-run clean
```

The `--dry-run` flag (`-n`) parses and prints commands without executing them.
Any syntax errors (unclosed `define`, missing `endef`, space-instead-of-tab
indentation) will produce a Make error before any command runs.

**Acceptance criteria**:

- [ ] `make --dry-run help` exits 0 and prints the echo commands.
- [ ] `make --dry-run install` exits 0 and shows the pip install commands.
- [ ] `make --dry-run backend` exits 0 and shows the uvicorn command.
- [ ] `make --dry-run test` exits 0 and shows the pytest command.
- [ ] `make --dry-run clean` exits 0 and shows the rm and find commands.
- [ ] No "missing separator" or "unterminated define" errors appear.

---

## Task 3 — Confirm .gitignore requires no change

**Layer**: `[core]`

**File**: `.gitignore` (read-only verification)

**Depends on**: none

**Description**:

Confirm that `.venv/` is already listed in `.gitignore` so no modification is
needed. This task is a verification gate, not an implementation task.

Run:

```bash
grep -n "\.venv" .gitignore
```

Expected output: a line containing `.venv` at line 124 (or nearby). If the
pattern is absent, add `.venv/` to the "Environments" section of `.gitignore`
between the `env/` and `venv/` lines.

**Acceptance criteria**:

- [ ] `.venv` or `.venv/` appears in `.gitignore`.
- [ ] If absent, it is added in the "Environments" section.

**Current status**: Already satisfied. `.venv` is present at line 124 of
`.gitignore`. No file edit is required unless verification contradicts this.

---

## Completion Checklist

- [ ] Task 1: `Makefile` created at project root with all targets.
- [ ] Task 2: All `make --dry-run <target>` commands exit 0.
- [ ] Task 3: `.venv/` confirmed present in `.gitignore`.
- [ ] `git status` shows only `Makefile` as a new file (no accidental `.gitignore` edits).
