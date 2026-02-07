## Why

The DeckDex MTG CLI is robust and functional, but lacks intuitive visualization for users who prefer graphical interfaces. A web MVP enables visualizing the collection, viewing real-time statistics, tracking price changes through charts, and running processes with immediate visual feedback, all without rewriting existing logic.

## What Changes

- **New React web interface**: Dashboard for visualizing collection, statistics, price charts, and card table with filters
- **FastAPI backend**: REST API exposing endpoints to list cards, get statistics, and execute processes (process cards, update prices)
- **WebSocket for real-time progress**: Bidirectional communication to show long-running process progress with live-updating progress bars
- **Reuse existing logic**: Backend wraps `MagicCardProcessor` and `CardFetcher` without modifying their behavior
- **Simple local deployment**: Setup with Vite dev server (frontend) and uvicorn (backend), or optional docker-compose
- **No CLI changes**: CLI tool continues working exactly the same; web is an additional layer

## Capabilities

### New Capabilities

- `web-api-backend`: FastAPI backend with REST endpoints to access collection data and execute processes (GET /api/cards, GET /api/stats, POST /api/process, POST /api/prices/update, GET /api/jobs/{id})
- `web-dashboard-ui`: React interface with TanStack Query, Recharts for graphs, Tailwind CSS for styling, and components for dashboard, card table, and statistics
- `websocket-progress`: WebSocket endpoint (/ws/progress/{job_id}) for real-time process progress communication with progress, error, and complete event types
- `processor-service-wrapper`: Service that wraps MagicCardProcessor for API usage, enabling async callbacks without modifying the existing core

### Modified Capabilities

- `architecture`: Extended to include new web layer (backend + frontend) while keeping existing CLI intact; Google Sheets remains the source of truth

## Impact

**Affected code:**
- New directory structure: `backend/` (FastAPI app, routes, services, websockets) and `frontend/` (React app with Vite)
- `openspec/specs/architecture.md`: Update to document web architecture complementary to CLI

**APIs and dependencies:**
- Backend: New dependencies FastAPI, uvicorn, websockets (requirements-api.txt)
- Frontend: New dependencies React, @tanstack/react-query, recharts, tailwindcss (package.json)
- No changes to existing CLI dependencies (requirements.txt)

**Systems:**
- Google Sheets API: No changes, continues to be used the same way from backend
- Scryfall API: No changes, accessed from backend through CardFetcher
- OpenAI API: No changes, optionally accessed from backend

**Deployment:**
- Local: Two processes (backend on :8000, frontend on :5173) or docker-compose
- No external hosting needed for MVP (localhost only)
- No authentication in MVP (localhost trusted)

**Risks:**
- Concurrency: CLI and web should not run processes simultaneously (document workflow)
- Collection size: Assuming < 2000 cards for MVP (no complex backend pagination)
- Job state: In-memory in MVP (lost on backend restart)
