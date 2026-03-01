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

Layer-specific conventions are in `.claude/rules/` (loaded conditionally per layer).

## Warnings

⚠️ **Concurrency**: Do NOT run CLI and web simultaneously when using Google Sheets only — writes conflict. PostgreSQL (`DATABASE_URL` set) allows both.

⚠️ **No auth**: App is localhost-only. Do not expose to the internet.

⚠️ **Job state**: lost on backend restart (in-memory, not persisted).

## OpenSpec

- **Specs**: `openspec/specs/` is the source of truth. Read relevant specs before implementing.
- **Changes**: `openspec/changes/<name>/`. Use `/opsx:ff` → `/opsx:apply` → `/opsx:archive`.
- Key specs: `data-model.md`, `architecture/spec.md`, `conventions.md`, `web-api-backend/spec.md`, `web-dashboard-ui/spec.md`. Per-capability: `openspec/specs/<capability>/spec.md`.

## Scoped context

- `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `deckdex/CLAUDE.md` — per-layer commands, file maps, and context.
- `.claude/rules/` — per-layer conventions (loaded conditionally by path).
