## Why

Setting up DeckDex for local development currently requires developers to
remember and manually execute six or more separate shell commands across
multiple directories — creating a venv, running pip twice against two
different requirements files, changing into `frontend/` to run `npm install`,
then opening two terminal sessions with precise `uvicorn` invocations. There
is no single authoritative entry point. The shell scripts that exist
(`scripts/setup_db.sh`) address only database bootstrapping. New contributors
must derive the full setup procedure from reading `CLAUDE.md` and `backend/CLAUDE.md`
together.

## What Changes

- A new root-level `Makefile` is added with ten targets covering the complete
  development lifecycle: `install`, `dev`, `backend`, `frontend`, `test`,
  `db-setup`, `docker-up`, `docker-down`, `clean`, and `help`.
- The `Makefile` manages the Python virtual environment at `.venv/` and uses
  it consistently for all Python invocations — no global pip.
- `make dev` starts backend and frontend concurrently with proper SIGINT
  handling so both processes are cleaned up on Ctrl-C.
- `.venv/` entry in `.gitignore` is confirmed present (already exists at
  line 124); no change required.
- Existing shell scripts (`scripts/setup_db.sh`) remain unchanged for
  backward compatibility.

## Non-goals

- This change does not replace or modify `scripts/setup_db.sh` or introduce
  any Python tooling changes (no pyproject.toml, no Poetry, no pipx).
- No CI/CD changes. The Makefile is a local developer convenience only.
- No Windows support. Make is expected to run on macOS/Linux.
- No management of the `.env` file or secret provisioning.

## Capabilities

### New Capabilities

- `developer-workflow`: A root-level `Makefile` that provides a unified
  command surface for virtual environment creation, dependency installation,
  service startup (individual and concurrent), test execution, database
  setup delegation, Docker Compose wrappers, and artifact cleanup.

### Modified Capabilities

_(none — no existing spec-level requirements are changing)_

## Impact

- **New file**: `Makefile` at project root.
- **`.gitignore`**: No change needed; `.venv` is already listed at line 124.
- **`scripts/setup_db.sh`**: Referenced by `make db-setup`; no modification.
- **Developer onboarding**: `CLAUDE.md` "Dev commands" section becomes a
  pointer to `make help` rather than raw commands (tracked separately; not
  part of this change).
- **No code impact**: Core (`deckdex/`), backend, and frontend source are
  untouched.
