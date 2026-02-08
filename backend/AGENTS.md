# AGENTS.md — backend

## Overview

Backend API for DeckDex MTG web interface: FastAPI app, REST routes, WebSockets for progress, and a wrapper around the deckdex processor. Runs in Docker or locally with uvicorn.

## Commands

| Task | Command | Notes |
|------|---------|-------|
| Install | `pip install -r requirements-api.txt` (from repo root: `pip install -r requirements.txt` then backend deps) | Run from project root or backend/ |
| Run API | `uvicorn backend.api.main:app --reload` (from repo root) or see README | Dev server |
| Lint / typecheck | From repo root: `pytest`, lint as per project | Backend shares root Python tooling |

See root `AGENTS.md` for project-wide skills and workflow. Backend-specific tests live in `tests/` at repo root; run from root.

## File map

```
backend/
  api/              → FastAPI app, routes, dependencies
  api/main.py       → App entrypoint
  api/routes/       → REST endpoints (cards, import, process, settings, stats)
  api/services/     → processor_service, settings_store
  api/websockets/  → progress WebSocket
  Dockerfile        → Image for API service
  requirements-api.txt → API dependencies
```

## Conventions

- Use FastAPI dependency injection (`dependencies.py`); avoid global state.
- Routes are thin: validate input, call services, return Pydantic models.
- WebSockets: use `api/websockets/progress.py` pattern for job progress.
- Check root AGENTS.md for project-wide conventions and OpenSpec workflow.
