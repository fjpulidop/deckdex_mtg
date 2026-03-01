---
paths:
  - "backend/**"
---

# Backend Conventions (FastAPI)

- Routes are thin: validate input → call service → return Pydantic model. No business logic in routes.
- Services own business logic; routes own HTTP concerns.
- Use `dependencies.py` for dependency injection (e.g., `get_processor_service`). Avoid module-level globals.
- New endpoints: add to the appropriate file in `routes/`, then wire the router in `main.py`.
- Services go in `backend/api/services/`. Follow existing patterns (`processor_service.py`, `card_image_service.py`).
- All response types must be Pydantic models. No raw dicts in route returns.
- WebSocket pattern: follow `websockets/progress.py` for job progress. Use the existing `ConnectionManager` pattern.
- Backend calls into `deckdex/` core for business logic. Never duplicate core logic in the API layer.
