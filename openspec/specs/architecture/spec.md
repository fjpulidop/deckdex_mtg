# Architecture

High-level components, data flow, and boundaries. CLI and web share core; web adds backend + frontend.

## Goals

- CLI-first sync of MTG card data (Scryfall → Google Sheets); optional OpenAI enrichment.
- Keep prices current with minimal API cost; testable and runnable locally/CI.

## Components

1. **CLI** (`main.py`) — Orchestrates tasks; 16+ options (profile, config, show-config, batch-size, workers, api-delay, sheet-name, credentials-path, limit, resume-from, dry-run, verbose).
2. **Web Backend** (`backend/api/main.py`) — FastAPI on 8000; REST + WebSocket; reuses core via ProcessorService.
3. **Web Frontend** (`frontend/src/main.tsx`) — React on 5173; TanStack Query, Recharts, Tailwind v4.
4. **ProcessorService** (`backend/api/services/processor_service.py`) — Wraps MagicCardProcessor; async callbacks for progress; no core logic changes.
5. **Configuration** (`deckdex/config_loader.py`) — config.yaml + profiles (default, development, production); DECKDEX_* env; CLI overrides; priority YAML < ENV < CLI; --show-config.
6. **Scryfall Fetcher** (`deckdex/card_fetcher.py`) — API + cache; rate-limit/backoff; ScryfallConfig.
7. **Google Sheets** (`deckdex/spreadsheet_client.py`) — Rows ↔ sheet; batched updates; incremental price writes; GoogleSheetsConfig.
8. **Enrichment** (in card_fetcher) — Optional OpenAI strategy/tier; OpenAIConfig.
9. **Price Updater** — Delta-only writes; buffered batches (write_buffer_batches); numeric values; CSV error report.
10. **Worker** — ThreadPoolExecutor; thread-safe batching; ProcessingConfig.max_workers.
11. **Caching** — LRU in-memory; optional persistence; web backend: 30s TTL for collection reads.

*Components 5–10 are shared by CLI and web.*

## Data flow

Config load (YAML → ENV → CLI) → ProcessorConfig. Read card names from sheet → queue → per card: cache/Scryfall/optional OpenAI → price delta → batched sheet updates (incremental).

## Layer boundaries

- **Core** (`deckdex/`) — No CLI/web imports.
- **CLI** (`main.py`) — Parsing, console, invokes core.
- **Web Backend** (`backend/`) — Routes, WebSocket, ProcessorService, job state.
- **Web Frontend** (`frontend/`) — React, TanStack Query, WebSocket client.

## Deployment

- **CLI-only:** `python main.py`.
- **Web:** backend `uvicorn api.main:app --reload --port 8000`; frontend `npm run dev` (5173). Vite proxies /api to backend.
- **Docker:** optional `docker-compose up`.
- Concurrency: when using PostgreSQL as the collection store, CLI and web MAY run simultaneously (both read/write the same DB). When using Google Sheets as the only source, do not run CLI and web simultaneously (writes conflict). Sheets limit 600 req/min when using Sheets.

## Directory structure

```
deckdex_mtg/
├── backend/api/         # main.py, routes/, services/, websockets/
├── frontend/src/        # components/, api/, App.tsx
├── deckdex/             # card_fetcher, magic_card_processor, spreadsheet_client, config_loader
├── main.py, config.yaml, requirements.txt
└── docker-compose.yml   # optional
```

## Integration

- Backend → Core: ProcessorService wraps processor; routes use SpreadsheetClient, config_loader.
- Frontend → Backend: REST + WebSocket; Vite proxy /api → :8000.
- Secrets: GOOGLE_API_CREDENTIALS, OPENAI_API_KEY (env only; not in config.yaml).

## Non-functional

- Performance: workers, batch size, api_delay, retries via config/ENV/CLI.
- Cost: batched updates, selective price writes, incremental buffers.
- Reliability: retries + backoff; CSV error report.
- Observability: normal (progress + errors) vs verbose; dry-run; --show-config.

## Security

- Credentials and API keys in env only; config.yaml safe to commit (no secrets). Least-privilege Google account.
- **Authentication:** Google OAuth 2.0 → JWT in HTTP-only cookies; all data endpoints require auth.
- **CORS:** Configurable via `DECKDEX_CORS_ORIGINS` env var (comma-separated, default `http://localhost:5173`).
- **Rate limiting:** slowapi (in-memory); per-IP for auth endpoints (10/min).
- **Middleware stack** (FastAPI, execution order bottom-to-top):
  1. Security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security` in production)
  2. Request ID + logging (UUID per request, `X-Request-ID` response header)
  3. Body size limit (25 MB global; 500 KB for profile updates)
  4. CORS middleware
- **Error sanitization:** 500 responses return generic `{"detail": "Internal server error"}`; full details logged server-side only.
- **Token lifecycle:** JWT includes `jti` claim; refresh via `POST /api/auth/refresh` blacklists old JTI; logout blacklists token. In-memory blacklist with TTL cleanup.
- **SSRF protection:** Avatar URLs validated against domain allowlist (Google, Gravatar, GitHub) before downloading. Avatar proxy caches locally.
- **Path traversal:** ImageStore validates keys (rejects `..`, `/`, null bytes); base dir resolved to absolute path.
- **Reverse proxy:** See `docs/deployment/reverse-proxy.md` for nginx and Caddy configurations for production HTTPS.
