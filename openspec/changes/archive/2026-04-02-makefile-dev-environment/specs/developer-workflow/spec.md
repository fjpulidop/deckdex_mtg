# Capability Spec: developer-workflow

## Purpose

Defines the unified command surface for local DeckDex development via a
root-level `Makefile`. Covers virtual environment management, dependency
installation, service startup, test execution, database bootstrapping, Docker
operations, and artifact cleanup.

---

## Requirements

### Virtual Environment Management

- **DEVWF-01**: The project MUST provide a `make install` target that creates
  a Python virtual environment at `.venv/` using `python3 -m venv`.
- **DEVWF-02**: `make install` MUST install all packages from
  `requirements.txt` and `backend/requirements-api.txt` into the venv, in
  that order.
- **DEVWF-03**: `make install` MUST run `npm install` inside the `frontend/`
  directory.
- **DEVWF-04**: `make install` MUST be idempotent: re-running it when `.venv/`
  already exists SHALL re-run pip (updating packages if needed) but SHALL NOT
  destroy the existing environment.
- **DEVWF-05**: All Python invocations in Makefile targets MUST use
  `.venv/bin/python` (or derived binaries such as `.venv/bin/uvicorn`), never
  the system Python directly.

### Service Startup

- **DEVWF-06**: `make backend` MUST start `uvicorn backend.api.main:app
  --reload --port 8000` using the venv's uvicorn binary, from the project root.
- **DEVWF-07**: `make frontend` MUST start the frontend dev server by running
  `npm run dev` inside `frontend/`, preserving any environment variables
  configured in `package.json`'s dev script.
- **DEVWF-08**: `make dev` MUST start the backend in the background and the
  frontend in the foreground concurrently.
- **DEVWF-09**: `make dev` MUST terminate the background backend process when
  the user interrupts the foreground frontend process (SIGINT or SIGTERM).

### Testing

- **DEVWF-10**: `make test` MUST run `pytest tests/` using the venv Python
  (`python -m pytest tests/`).

### Database and Infrastructure

- **DEVWF-11**: `make db-setup` MUST delegate to `./scripts/setup_db.sh`
  without modification.
- **DEVWF-12**: `make docker-up` MUST run `docker compose up --build` in
  attached mode (logs visible).
- **DEVWF-13**: `make docker-down` MUST run `docker compose down` without
  `--volumes`, preserving persistent data volumes.

### Cleanup

- **DEVWF-14**: `make clean` MUST remove the `.venv/` directory.
- **DEVWF-15**: `make clean` MUST remove `__pycache__/` directories and
  `*.pyc` files from the project tree, excluding any within `.venv/`.

### Discoverability

- **DEVWF-16**: `make help` MUST print a formatted list of all targets with
  one-line descriptions.
- **DEVWF-17**: `make help` MUST be the default target (invoked when `make`
  is run with no arguments).

### Error Handling

- **DEVWF-18**: Targets that create the venv (`install`) MUST fail with a
  human-readable error message if `python3` is not found in `PATH`.
- **DEVWF-19**: Targets that consume the venv (`backend`, `frontend`, `dev`,
  `test`) MUST fail with a human-readable error if `.venv/` has not been
  created, directing the user to run `make install`.
- **DEVWF-20**: ALL non-file-producing targets MUST be declared in `.PHONY`.

### Backward Compatibility

- **DEVWF-21**: The Makefile MUST NOT modify or remove `scripts/setup_db.sh`.
- **DEVWF-22**: `.venv/` MUST be listed in `.gitignore`. (Already present at
  line 124; Makefile does not need to add it.)

---

## Non-requirements

- Windows compatibility is out of scope.
- CI/CD pipeline integration is out of scope.
- Secret provisioning or `.env` file generation is out of scope.
- Linting or formatting targets are out of scope (ruff is invoked directly or
  via IDE).
