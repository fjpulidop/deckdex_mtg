# DeckDex MTG

![Logo](images/Deckdex.png)

A full-stack Magic: The Gathering collection manager with CLI and web dashboard. Track your cards, build decks, monitor prices, and explore collection insights.

**This project is built and maintained with AI** — designed, implemented, and reviewed by [Claude Code](https://claude.com/claude-code) agents orchestrated through a custom pipeline. See [AI-Driven Development](#ai-driven-development) for details.

## Features

- **Collection Management** — Browse, search, filter, and edit cards with gallery/table views
- **Deck Builder** — Create Commander decks with card picker, mana curve stats, and animated commander backgrounds
- **Analytics Dashboard** — Interactive charts for color distribution, mana curves, rarity breakdown, and collection value
- **Collection Insights** — AI-powered analysis catalog with actionable recommendations
- **Price Tracking** — Automated Scryfall price updates with incremental writes and resume support
- **Real-time Progress** — WebSocket-powered live updates for long-running operations
- **Import** — CSV, JSON, and text list import with duplicate detection and resolution UI
- **Internationalization** — English and Spanish (i18n)
- **Auth** — Google OAuth with JWT session cookies and admin roles
- **Demo Mode** — Unauthenticated preview with sample data
- **CLI** — Full command-line interface for automation and batch processing

## Stack

| Layer    | Tech                                                  |
|----------|-------------------------------------------------------|
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS, TanStack Query |
| Backend  | FastAPI, Uvicorn, WebSockets, Pydantic               |
| Core     | Python 3.11+, `deckdex/` package                     |
| Storage  | PostgreSQL (recommended) or Google Sheets             |
| External | Scryfall (card data/prices), OpenAI (optional enrichment) |

## Architecture

```mermaid
graph TB
    Browser["Browser"]

    subgraph Frontend["Frontend (:5173)"]
        React["React 19 + Vite 7"]
        TQ["TanStack Query"]
        Tailwind["Tailwind CSS"]
        i18n["i18n (EN/ES)"]
    end

    subgraph Backend["Backend (:8000)"]
        FastAPI["FastAPI"]
        WS["WebSocket Server"]
        Auth["Google OAuth + JWT"]
        Routes["REST API Routes"]
        Services["Services Layer"]
    end

    subgraph Core["Core (deckdex/)"]
        Fetcher["Card Fetcher"]
        Processor["Card Processor"]
        Storage["Storage Adapters"]
    end

    subgraph External["External Services"]
        Scryfall["Scryfall API"]
        OpenAI["OpenAI (optional)"]
        Google["Google OAuth"]
    end

    DB[("PostgreSQL")]
    Sheets[("Google Sheets")]

    Browser -->|HTTP| React
    React --> TQ
    TQ -->|REST| Routes
    React -->|WebSocket| WS
    Auth --> Google
    Routes --> Services
    Services --> Core
    Fetcher --> Scryfall
    Processor --> OpenAI
    Storage --> DB
    Storage -.->|alternative| Sheets
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (recommended) or Google Sheets API credentials

### Setup

```bash
git clone <repo-url>
cd deckdex_mtg

# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r backend/requirements-api.txt

# Frontend
cd frontend && npm install && cd ..

# Environment
cp .env.example .env  # Edit with your credentials
```

Create a `.env` file:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/deckdex
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret
JWT_SECRET_KEY=your-secret-key

# Optional
OPENAI_API_KEY=sk-...
GOOGLE_API_CREDENTIALS=/path/to/credentials.json  # Only for Google Sheets storage
```

If using PostgreSQL, run migrations:
```bash
./scripts/setup_db.sh       # Docker
# or
python scripts/setup_db.py  # Direct
```

### Run

```bash
# Backend (Terminal 1)
uvicorn backend.api.main:app --reload   # http://localhost:8000

# Frontend (Terminal 2)
cd frontend && npm run dev              # http://localhost:5173
```

### Docker

```bash
./scripts/setup_db.sh        # First time only
docker compose up --build    # Frontend :5173, Backend :8000
```

## CLI

```bash
# Update prices
python main.py --update_prices

# Process cards with AI enrichment
python main.py --use_openai

# Test run
python main.py --limit 10 --dry-run --verbose

# Resume after interruption
python main.py --update_prices --resume-from 450

# Use production profile
python main.py --profile production --update_prices

# Show config
python main.py --show-config
```

Full options: `python main.py --help`

## Testing

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ -q --tb=short --cov=backend --cov=deckdex

# Frontend
cd frontend && npm run test
```

CI runs automatically on PRs via GitHub Actions (lint, type check, tests for both layers).

## Project Structure

```
deckdex_mtg/
├── backend/              # FastAPI API
│   └── api/
│       ├── routes/       # REST endpoints (cards, decks, analytics, insights, auth, admin, ...)
│       ├── services/     # Business logic wrappers
│       └── websockets/   # Real-time progress
├── frontend/             # React dashboard
│   └── src/
│       ├── components/   # 30+ React components
│       ├── pages/        # Dashboard, DeckBuilder, Analytics, Admin, Import, ...
│       ├── api/          # Typed API client
│       └── locales/      # i18n (en, es)
├── deckdex/              # Core package (card fetching, processing, storage)
├── tests/                # pytest test suite
├── migrations/           # Database migrations
├── openspec/             # Specs and change tracking
├── main.py               # CLI entry point
├── config.yaml           # Configuration profiles
└── docker-compose.yml
```

## Notes

- **Concurrency**: Do not run CLI and web simultaneously when using Google Sheets only — writes conflict. PostgreSQL allows both.
- **Auth**: All data endpoints require authentication. Admin routes require admin role.
- **Job state**: In-memory, lost on backend restart.
- **API docs**: Available at `http://localhost:8000/docs` when backend is running.

## AI-Driven Development

This project is built and maintained using [Claude Code](https://claude.com/claude-code) with a custom multi-agent pipeline. A human operator defines priorities and approves plans — agents handle design, implementation, and review.

### Workflow

The development cycle follows three stages:

1. **Backlog** — Automated commands scan specs vs. code to find gaps, or generate new feature ideas through product discovery. Results are published as GitHub Issues with labels, priority, and effort estimates.

2. **Prioritization** — The operator reviews the backlog and selects items for implementation (typically 3 per sprint).

3. **Parallel Implementation** — Selected items are implemented concurrently by specialized agents.

### Agent Pipeline

```mermaid
graph LR
    subgraph Backlog["1. Backlog"]
        SB["/spec-backlog"]
        PB["/product-backlog"]
    end

    Operator["Operator picks top 3"]

    subgraph Pipeline["2. Parallel Implementation"]
        direction TB

        subgraph Architects["Phase 1: Design (parallel)"]
            A1["Architect 1"]
            A2["Architect 2"]
            A3["Architect 3"]
        end

        subgraph Developers["Phase 2: Implement (parallel, isolated worktrees)"]
            D1["Developer 1"]
            D2["Developer 2"]
            D3["Developer 3"]
        end

        subgraph Review["Phase 3: Merge & Review"]
            Merge["Orchestrator merges worktrees"]
            R["Reviewer runs full CI"]
        end

        Architects --> Developers --> Review
    end

    PR["PR + auto-close issues"]

    SB --> Operator
    PB --> Operator
    Operator --> Pipeline
    Review --> PR
```

**How it works:**

| Agent | Role | Scope |
|-------|------|-------|
| **Explorer** | Scans code and specs to assess what's built vs. what's missing | Read-only, parallel |
| **Architect** | Creates design artifacts (proposal, design, delta-spec, tasks) using [OpenSpec](openspec/) | Writes to `openspec/changes/`, parallel |
| **Developer** | Implements tasks from architect's blueprint, runs CI locally | Isolated git worktree per feature, parallel |
| **Reviewer** | Validates all merged changes, fixes cross-feature conflicts | Main repo, sequential |
| **Orchestrator** | Coordinates the pipeline, merges worktrees, creates PR | Main repo, manages all phases |

Each feature gets its own architect + developer pair running in parallel. The orchestrator merges all results, the reviewer validates, and a single PR is opened linking the resolved GitHub Issues.

### Specs as Source of Truth

All features are specified in `openspec/specs/` before implementation. Changes go through a structured artifact workflow (`proposal` > `design` > `delta-spec` > `tasks`) that ensures agents have clear, grounded blueprints — not vague instructions.

## License

[MIT](https://choosealicense.com/licenses/mit/)
