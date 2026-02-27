# backend/

FastAPI app. Thin wrapper around `deckdex/` core — routes delegate to services, WebSockets handle job progress.

## Commands

| Task     | Command                                                              |
|----------|----------------------------------------------------------------------|
| Install  | `pip install -r requirements.txt -r backend/requirements-api.txt`   |
| Run      | `uvicorn backend.api.main:app --reload` (from repo root)             |
| Tests    | `pytest tests/` (from repo root)                                     |
| API docs | http://localhost:8000/docs                                           |

## File map

```
backend/
  api/
    main.py             → App entrypoint, CORS, router registration
    dependencies.py     → FastAPI DI (get_processor_service, etc.)
    routes/             → cards, import, process, settings, stats
    services/           → processor_service.py, settings_store.py
    websockets/         → progress.py (WebSocket job tracking)
  Dockerfile
  requirements-api.txt
```

## Conventions

- Use `dependencies.py` for dependency injection; avoid module-level globals.
- Routes are thin: validate input → call service → return Pydantic model.
- New endpoints: add to the appropriate file in `routes/`, wire up in `main.py`.
- WebSocket pattern: follow `websockets/progress.py` for job progress.
- Services own business logic; routes own HTTP concerns.
