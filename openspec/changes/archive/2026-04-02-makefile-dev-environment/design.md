# Design: Makefile for Virtual Environment and Dev Stack Management

## Overview

A single root-level `Makefile` provides a unified command surface for the
entire DeckDex development lifecycle. It manages the Python virtual
environment at `.venv/`, installs all dependencies from the two existing
requirements files, and orchestrates service startup for both backend and
frontend. All Python invocations go through the venv binary; Make itself does
not alter the shell's `PATH` or activate the venv (which is a shell concept
incompatible with Make's subprocess model).

---

## Variable Declarations

```makefile
VENV        := .venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
UVICORN     := $(VENV)/bin/uvicorn
FRONTEND_DIR := frontend
```

**Design decision — explicit venv-relative paths**: Make runs each recipe
line in a separate shell; `source .venv/bin/activate` would be invisible to
the next line. Using `$(VENV)/bin/python` directly is the correct and
portable pattern for venv-aware Makefiles on macOS/Linux.

**Design decision — PYTHON / PIP / UVICORN as separate variables**: Keeps
recipes readable and makes it trivial to override (e.g.,
`make test PYTHON=.venv/bin/python3.11`) without editing the file.

---

## Python Version Check

At the top of the file, before any target, define a guard that is evaluated
lazily when `python3` is invoked:

```makefile
SYSTEM_PYTHON := $(shell command -v python3 2>/dev/null)

define PYTHON_GUARD
	@if [ -z "$(SYSTEM_PYTHON)" ]; then \
		echo "Error: python3 not found. Install Python 3.9+ and retry."; \
		exit 1; \
	fi
endef
```

This guard is called in targets that create the venv (`install`, `clean`).
Targets that only consume the venv (`test`, `backend`, `dev`) check for the
venv's existence instead:

```makefile
define VENV_GUARD
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "Error: venv not found. Run 'make install' first."; \
		exit 1; \
	fi
endef
```

**Rationale**: Two distinct failure modes need distinct messages. "python3
not found" is an environment issue; "venv not found" is a "you skipped
`make install`" issue. Conflating them produces confusing errors.

---

## Target Specifications

### `make install`

```makefile
install:
	$(call PYTHON_GUARD)
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment at $(VENV)/..."; \
		python3 -m venv $(VENV); \
	fi
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt
	$(PIP) install --quiet -r backend/requirements-api.txt
	cd $(FRONTEND_DIR) && npm install
	@echo "Installation complete. Run 'make dev' to start all services."
```

**Design decision — idempotent venv creation**: The `[ ! -d "$(VENV)" ]`
guard means repeated `make install` calls are safe. They re-run pip (which is
fast for already-installed packages) but do not destroy an existing venv.

**Design decision — install order**: `requirements.txt` before
`backend/requirements-api.txt` mirrors the documented install order in
`backend/CLAUDE.md` ("Install parent requirements first") and prevents
dependency resolution conflicts.

**Design decision — `npm install` from `$(FRONTEND_DIR)` subdirectory**:
The `cd` and `npm install` are in the same recipe line, which runs in a
subshell. This is correct for Make. Alternatively we could use
`$(MAKE) -C $(FRONTEND_DIR) install` but that would require a `frontend/Makefile`.

### `make backend`

```makefile
backend:
	$(call VENV_GUARD)
	$(UVICORN) backend.api.main:app --reload --port 8000
```

Invoked from project root (as per `backend/CLAUDE.md`). The `--reload` flag
is development-only and appropriate for this target's purpose.

### `make frontend`

```makefile
frontend:
	@if [ ! -d "$(FRONTEND_DIR)/node_modules" ]; then \
		echo "Error: node_modules not found. Run 'make install' first."; \
		exit 1; \
	fi
	cd $(FRONTEND_DIR) && npm run dev
```

**Design decision — node_modules check instead of `node` binary check**: A
missing `node` binary produces a clear error from npm itself. The more
actionable failure is a missing `node_modules` directory, which means the
user skipped `make install`. Checking `node_modules` existence gives a
precise error message.

**Design decision — `npm run dev` not `npx vite`**: Preserves the
`NODE_OPTIONS='--max-http-header-size=32768'` flag that is embedded in the
`package.json` dev script. Calling `npx vite` directly would bypass it.

### `make dev`

This is the most nuanced target. It must start the backend in the background,
start the frontend in the foreground, and ensure the backend is killed when
the user hits Ctrl-C.

```makefile
dev:
	$(call VENV_GUARD)
	@echo "Starting backend on :8000 and frontend on :5173..."
	@$(UVICORN) backend.api.main:app --reload --port 8000 & \
	BACKEND_PID=$$!; \
	trap "kill $$BACKEND_PID 2>/dev/null; wait $$BACKEND_PID 2>/dev/null" INT TERM; \
	cd $(FRONTEND_DIR) && npm run dev; \
	kill $$BACKEND_PID 2>/dev/null; \
	wait $$BACKEND_PID 2>/dev/null
```

**Design decision — background backend, foreground frontend**: The frontend
dev server's output (Vite's colored banner, HMR messages) is what developers
watch most closely. Putting it in the foreground gives it the terminal.
Backend logs still stream to stderr alongside it.

**Design decision — SIGINT trap**: Without the trap, pressing Ctrl-C kills
only the foreground `npm run dev` process. The background `uvicorn` would
become an orphan, silently holding port 8000. The `trap` ensures the backend
PID is killed before the shell exits.

**Design decision — `wait` after `kill`**: `kill` sends the signal
asynchronously. `wait` blocks until the process terminates, preventing the
"Terminated" message from printing after the shell prompt returns. The
`2>/dev/null` suppresses "no such process" errors in case the backend already
exited on its own.

**Design decision — single recipe continuation lines with `\`**: All lines
of the dev recipe are a single shell invocation (connected by `;` and `\`).
This is required because shell variables (`BACKEND_PID`) do not persist
across separate Make recipe lines, each of which runs in its own subshell.

### `make test`

```makefile
test:
	$(call VENV_GUARD)
	$(PYTHON) -m pytest tests/ -v
```

Uses `python -m pytest` rather than the venv's `pytest` binary directly. This
pattern ensures pytest always resolves imports relative to the project root
(since `python -m pytest` prepends `""` / cwd to `sys.path`). It avoids
subtle import errors that can appear when running the `pytest` binary on
projects with src-layout concerns.

### `make db-setup`

```makefile
db-setup:
	./scripts/setup_db.sh
```

Pure delegation. Does not attempt to replicate the script's logic. The script
already handles both Docker and local psql paths with appropriate error
messages.

### `make docker-up`

```makefile
docker-up:
	docker compose up --build
```

**Design decision — no `-d` flag**: `make docker-up` is explicitly not
detached. Developers who want the logs streaming (most common case for
debugging) get them. Detached mode is `docker compose up --build -d`, which
developers can invoke directly when needed.

### `make docker-down`

```makefile
docker-down:
	docker compose down
```

Straightforward wrapper. Does not add `--volumes` by default — that would
destroy the `deckdex-pgdata` volume, wiping the local database. Developers who
want volume teardown must invoke Docker directly.

### `make clean`

```makefile
clean:
	rm -rf $(VENV)
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
	@echo "Cleaned venv and Python cache artifacts."
```

**Design decision — exclude `.venv/` from find**: Since we are deleting
`.venv/` first, in practice the venv is already gone when the `find` runs.
The `not -path "./.venv/*"` guard handles the edge case where `rm -rf`
partially fails (permissions issue) and leaves a partial venv with
`__pycache__` directories inside. Without this guard, `find` would descend
into the partial venv, which is wasteful and confusing.

**Design decision — `|| true` on finds**: `find -exec rm -rf` returns
non-zero when no matches are found on some systems. With `set -e`-style
Makefile behavior, this would abort `make clean` unnecessarily.

### `make help`

```makefile
help:
	@echo ""
	@echo "DeckDex MTG — Development Makefile"
	@echo "======================================"
	@echo ""
	@echo "  make install      Create .venv/, install Python and npm dependencies"
	@echo "  make dev          Start backend (:8000) and frontend (:5173) concurrently"
	@echo "  make backend      Start backend only (uvicorn --reload)"
	@echo "  make frontend     Start frontend only (npm run dev)"
	@echo "  make test         Run pytest tests/"
	@echo "  make db-setup     Initialize database (delegates to scripts/setup_db.sh)"
	@echo "  make docker-up    Build and start full stack via Docker Compose"
	@echo "  make docker-down  Stop Docker Compose services"
	@echo "  make clean        Remove .venv/ and Python cache artifacts"
	@echo "  make help         Show this message"
	@echo ""
```

`help` is the default target (first in file), so `make` with no arguments
prints usage — a standard ergonomic convention.

---

## .PHONY Declaration

```makefile
.PHONY: install dev backend frontend test db-setup docker-up docker-down clean help
```

All targets produce no files. Without `.PHONY`, Make would check for a file
named e.g. `test` in the project root. If one existed (unlikely but possible),
the target would silently not run. `.PHONY` is declared for every target in
this Makefile.

---

## .gitignore Verification

`.venv/` is already present in `.gitignore` at line 124. The generic `venv/`
and `env/` patterns are also present. No modification is needed.

---

## Complete File Structure

The Makefile is organized in this order:

1. Header comment with project name and usage
2. `.DEFAULT_GOAL := help`
3. Variable declarations (`VENV`, `PYTHON`, `PIP`, `UVICORN`, `FRONTEND_DIR`, `SYSTEM_PYTHON`)
4. Guard macro definitions (`PYTHON_GUARD`, `VENV_GUARD`)
5. `.PHONY` declaration
6. `help` target (default)
7. `install` target
8. `dev` target
9. `backend` target
10. `frontend` target
11. `test` target
12. `db-setup` target
13. `docker-up` target
14. `docker-down` target
15. `clean` target

---

## Compatibility

This change introduces no new API surface, no modifications to existing
endpoints, commands, agents, placeholders, or config keys.

**Compatibility: No contract surface changes detected.**

---

## Risks and Considerations

- **Make availability**: `make` is pre-installed on macOS (via Xcode Command
  Line Tools) and all common Linux distributions. This is not a meaningful
  risk for this project's target audience.
- **`uvicorn` binary location**: The venv-relative `$(VENV)/bin/uvicorn` path
  works on macOS and Linux. On Windows (not a supported platform), paths would
  use `Scripts/` — not addressed here.
- **`npm run dev` NODE_OPTIONS**: The `npm run dev` invocation in
  `package.json` uses `NODE_OPTIONS='--max-http-header-size=32768'`. This
  value was set by a previous change; `make frontend` preserves it because it
  delegates to `npm run dev` rather than calling Vite directly.
- **Port conflicts**: `make dev` does not check whether ports 8000 or 5173
  are already in use. uvicorn and Vite will both produce clear error messages
  in that case. Adding a pre-flight port check would add complexity with
  minimal benefit.
- **SIGINT propagation in `make dev`**: The `trap` + `wait` pattern is POSIX
  sh compliant and works correctly with `/bin/sh` (the default Make shell on
  macOS and Linux). It does not rely on bash-specific behavior.
