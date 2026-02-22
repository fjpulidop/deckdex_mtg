## MODIFIED Requirements

### Requirement: Components
High-level components, data flow, and boundaries. CLI and web share core; web adds backend + frontend.

1. **CLI** (`main.py`) — Orchestrates tasks; 16+ options (profile, config, show-config, batch-size, workers, api-delay, sheet-name, credentials-path, limit, resume-from, dry-run, verbose).
2. **Web Backend** (`backend/api/main.py`) — FastAPI on 8000; REST + WebSocket; reuses core via ProcessorService. **Auth layer**: Google OAuth 2.0 login, JWT cookie issuance/validation, `get_current_user` dependency; auth routes at `/api/auth/*`.
3. **Web Frontend** (`frontend/src/main.tsx`) — React on 5173; TanStack Query, Recharts, Tailwind v4. **Auth layer**: `AuthContext`, `ProtectedRoute`, login page (`/login`).
4. **ProcessorService** (`backend/api/services/processor_service.py`) — Wraps MagicCardProcessor; async callbacks for progress; no core logic changes.
5. **Configuration** (`deckdex/config_loader.py`) — config.yaml + profiles (default, development, production); DECKDEX_* env; CLI overrides; priority YAML < ENV < CLI; --show-config.
6. **Scryfall Fetcher** (`deckdex/card_fetcher.py`) — API + cache; rate-limit/backoff; ScryfallConfig.
7. **Google Sheets** (`deckdex/spreadsheet_client.py`) — Rows ↔ sheet; batched updates; incremental price writes; GoogleSheetsConfig.
8. **Enrichment** (in card_fetcher) — Optional OpenAI strategy/tier; OpenAIConfig.
9. **Price Updater** — Delta-only writes; buffered batches (write_buffer_batches); numeric values; CSV error report.
10. **Worker** — ThreadPoolExecutor; thread-safe batching; ProcessingConfig.max_workers.
11. **Caching** — LRU in-memory; optional persistence; web backend: 30s TTL for collection reads.
12. **User Management** (`users` table) — Google OAuth identity store; `google_id`, `email`, `display_name`, `avatar_url`; user created on first Google login.

*Components 5–10 are shared by CLI and web.*

#### Scenario: Auth layer in backend and frontend
- **WHEN** the web application is deployed
- **THEN** the backend SHALL include auth routes (`/api/auth/*`) and JWT middleware, and the frontend SHALL include `AuthContext`, `ProtectedRoute`, and a login page

### Requirement: Data flow
Config load (YAML → ENV → CLI) → ProcessorConfig. Read card names from DB → queue → per card: cache/Scryfall/optional OpenAI → price delta → batched DB updates (incremental). All card and deck data is scoped by `user_id`; the authenticated user's ID is injected from the JWT cookie into every query.

#### Scenario: User-scoped data flow
- **WHEN** an authenticated user makes a request to the web API
- **THEN** the backend SHALL extract `user_id` from the JWT and scope all card/deck queries to that user

### Requirement: Security
Credentials and API keys in env only; config.yaml safe to commit (no secrets). Least-privilege Google account. Authentication via Google OAuth 2.0; JWT in HTTP-only secure cookie; all data endpoints require valid JWT (except `/api/health` and `/api/auth/*`). Auth secrets: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `JWT_SECRET_KEY` in env only.

#### Scenario: Auth secrets in environment
- **WHEN** the backend is deployed for web use
- **THEN** `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `JWT_SECRET_KEY` SHALL be provided via environment variables (not in config.yaml or committed files)
