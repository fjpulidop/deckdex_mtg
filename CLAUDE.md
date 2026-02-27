# DeckDex MTG

MTG collection manager: CLI + web dashboard. Core logic (Python) →
FastAPI backend → React frontend. Syncs to Google Sheets or PostgreSQL.

## Stack

| Layer    | Tech                                                          |
|----------|---------------------------------------------------------------|
| Core     | Python 3.8+, `deckdex/` package                              |
| Backend  | FastAPI, uvicorn, WebSockets, Pydantic                        |
| Frontend | React 19, TypeScript, Vite 7, Tailwind, TanStack Query        |
| Storage  | PostgreSQL (recommended) or Google Sheets                     |
| Ext APIs | Scryfall (card data), OpenAI (optional enrichment)            |

## Repo layout

```
deckdex_mtg/
├── deckdex/         # Core package (card processing, config, storage)
├── backend/         # FastAPI API (routes, services, websockets)
├── frontend/        # React dashboard
├── tests/           # pytest — all tests live here
├── main.py          # CLI entrypoint
├── config.yaml      # Config profiles (default/development/production)
├── migrations/      # DB migrations
└── docker-compose.yml
```

## Dev commands

```bash
# Install
pip install -r requirements.txt -r backend/requirements-api.txt
cd frontend && npm install

# Start (two terminals)
uvicorn backend.api.main:app --reload   # :8000
cd frontend && npm run dev              # :5173

# Tests
pytest tests/

# Docker (full stack)
./scripts/setup_db.sh       # first time only
docker compose up --build
```

## Environment

Secrets in `.env`, never in `config.yaml`:

```
GOOGLE_API_CREDENTIALS=/path/to/credentials.json
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost:5432/deckdex
```

Config priority: `config.yaml` < env vars < CLI flags.

## Architecture

```
Browser → React (Vite, :5173)
              ↓ REST + WebSocket
          FastAPI (:8000)
              ↓
          deckdex/ (core logic)
              ↓
          PostgreSQL / Google Sheets
```

## Conventions

- **Routes are thin**: validate input → call service → return Pydantic model. No business logic in routes.
- **deckdex/ has no framework deps**: stdlib + `requirements.txt` only. No FastAPI or React imports here.
- **Config via config_loader**: never hardcode paths or secrets; always go through `config_loader.py`.
- **Storage via repository**: all DB ops through `storage/repository.py`. No raw SQL elsewhere.
- **WebSockets**: follow `api/websockets/progress.py` pattern for job progress.
- **Frontend**: functional components + hooks, TypeScript strict, `useApi` hook for all backend calls.

## Warnings

⚠️ **Concurrency**: Do NOT run CLI and web simultaneously when using Google Sheets only — writes conflict. PostgreSQL (`DATABASE_URL` set) allows both.

⚠️ **No auth**: App is localhost-only. Do not expose to the internet.

⚠️ **Job state**: lost on backend restart (in-memory, not persisted).

## Specs (OpenSpec)

`openspec/specs/` is the source of truth for requirements and design decisions.
**Before implementing any feature, read the relevant spec(s) in this folder.**

Key specs to know:
- `openspec/specs/data-model.md` — data model and field definitions
- `openspec/specs/architecture/spec.md` — system architecture
- `openspec/specs/conventions.md` — coding conventions
- `openspec/specs/web-api-backend/spec.md` — API contracts
- `openspec/specs/web-dashboard-ui/spec.md` — UI patterns
- Per-capability specs live in `openspec/specs/<capability>/spec.md`

## Change workflow (OpenSpec)

Changes live in `openspec/changes/<name>/`. Use `/opsx:ff` to create a new change, `/opsx:apply` to implement, `/opsx:archive` when done.

## Scoped context

- `backend/CLAUDE.md` — FastAPI routes, services, WebSockets
- `frontend/CLAUDE.md` — React, TypeScript, Vite
- `deckdex/CLAUDE.md` — Core package (processor, storage, config)
