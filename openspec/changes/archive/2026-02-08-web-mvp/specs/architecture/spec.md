## MODIFIED Requirements

### Requirement: Architecture SHALL support both CLI and web interfaces

The system architecture SHALL extend to include a web layer (backend + frontend) while keeping the existing CLI intact.

**High-level Components** (updated):

1. CLI / Interactive CLI
   - Entrypoint: `main.py`
   - Orchestrates tasks with comprehensive argument parsing for performance tuning, Google Sheets configuration, and processing control.
   - Provides 16+ configuration options including profile, config, show-config, batch-size, workers, api-delay, sheet-name, credentials-path, limit, resume-from, dry-run, verbose.

2. **Web Backend (FastAPI) - NEW**
   - Entrypoint: `backend/api/main.py`
   - Provides REST API endpoints for accessing collection data and executing processes
   - Reuses core modules through ProcessorService wrapper
   - Runs on port 8000 via uvicorn
   - Supports WebSocket connections for real-time progress updates

3. **Web Frontend (React) - NEW**
   - Entrypoint: `frontend/src/main.tsx`
   - Dashboard UI for visualizing collection statistics, price charts, and card table
   - Communicates with backend via REST API and WebSocket
   - Runs on port 5173 via Vite dev server
   - Uses TanStack Query for data fetching, Recharts for visualizations, Tailwind CSS v4 for styling (with `@tailwindcss/postcss` plugin)

4. **ProcessorService Wrapper - NEW**
   - Module: `backend/api/services/processor_service.py`
   - Wraps `MagicCardProcessor` to enable async callbacks for API usage
   - Provides progress events for WebSocket broadcasting
   - Does not modify core processor behavior

5. Configuration Management
   - Module: `deckdex/config_loader.py`
   - Loads configuration from config.yaml with profile support (default, development, production).
   - Merges environment variables (DECKDEX_* prefix) and CLI flags using strict priority hierarchy.
   - Validates all parameters and provides nested configuration objects (ProcessingConfig, ScryfallConfig, GoogleSheetsConfig, OpenAIConfig) to subsystems.
   - Supports --show-config flag for debugging resolved configuration.
   - **Used by both CLI and web backend**

6. Scryfall Fetcher
   - Module: `deckdex/card_fetcher.py`
   - Responsible for querying Scryfall API, normalizing responses, and caching results.
   - Uses persistent HTTP sessions and rate-limit/backoff handling.
   - Configured via ScryfallConfig (max_retries, retry_delay, timeout).
   - **Used by both CLI and web backend**

7. Google Sheets Sync
   - Module: `deckdex/spreadsheet_client.py`
   - Translates internal card models to sheet rows and performs batched updates to minimize API calls.
   - Manages authentication via Google Service Account credentials JSON.
   - Supports incremental price writes for better progress visibility and resilience.
   - Configured via GoogleSheetsConfig (batch_size, max_retries, retry_delay, sheet_name, worksheet_name).
   - **Used by both CLI and web backend**

8. Enrichment Service (Optional)
   - Module: `deckdex/card_fetcher.py` (integrated)
   - Calls OpenAI to generate game strategy and tier metadata.
   - Runs optionally per-card or in batches; results are cached to avoid duplicate calls.
   - Configured via OpenAIConfig (enabled, model, max_tokens, temperature, max_retries).
   - **Used by both CLI and web backend**

9. Price Updater
   - Compares current prices with new Scryfall prices and only writes changed values.
   - Uses incremental buffered writes (configurable via write_buffer_batches) to Google Sheets.
   - Writes prices as numeric values for spreadsheet calculations.
   - Generates CSV error reports for failed card lookups.
   - **Used by both CLI and web backend**

10. Worker / Executor
    - Uses ThreadPoolExecutor for parallel processing of cards.
    - Ensures thread-safe Google Sheets batching and rate-limit compliance.
    - Parallelism level configured via ProcessingConfig.max_workers.
    - **Used by both CLI and web backend**

11. Caching & Persistence
    - In-memory LRU caches for short-term API responses.
    - Optional local persistence (JSON or lightweight DB) for price history and deduplication.
    - **Web backend adds 30-second TTL cache for collection reads to reduce Sheets API calls**

#### Scenario: CLI continues working without modifications
- **WHEN** user runs `python main.py` with any existing CLI flags
- **THEN** system processes cards using existing logic without any behavioral changes

#### Scenario: Web backend reuses core modules
- **WHEN** web backend needs to process cards
- **THEN** it uses ProcessorService wrapper which delegates to existing MagicCardProcessor

#### Scenario: CLI and web share configuration system
- **WHEN** either CLI or web backend needs configuration
- **THEN** both use `config_loader.load_config()` with same config.yaml and environment variables

#### Scenario: Google Sheets remains single source of truth
- **WHEN** either CLI or web writes/reads card data
- **THEN** both use same SpreadsheetClient and Google Sheets as the only data store

### Requirement: Architecture SHALL support dual deployment modes

The system SHALL support running CLI standalone or running CLI + web concurrently.

**Deployment modes:**

1. **CLI-only mode (existing):**
   - Run `python main.py` commands as before
   - No web services needed

2. **Web-enabled mode (new):**
   - Run backend: `cd backend && uvicorn api.main:app --reload --port 8000`
   - Run frontend: `cd frontend && npm run dev` (port 5173)
   - CLI still available alongside web

3. **Docker-compose mode (optional):**
   - Run `docker-compose up` to start both backend and frontend containers
   - Useful for simplified local setup

#### Scenario: Run CLI without starting web services
- **WHEN** user only needs CLI functionality
- **THEN** CLI works without requiring backend or frontend to be running

#### Scenario: Run web and CLI concurrently (with caution)
- **WHEN** both web backend and CLI attempt to process simultaneously
- **THEN** race conditions may occur (documented risk, mitigated by user coordination)

#### Scenario: Web backend and frontend run independently
- **WHEN** backend is running on port 8000
- **THEN** frontend on port 5173 proxies API requests to backend via vite config

### Requirement: Architecture SHALL define clear boundaries between layers

The system SHALL maintain separation between CLI, web, and core logic layers.

**Layer boundaries:**

- **Core Layer** (`deckdex/`): Pure logic, no CLI or web dependencies
  - MagicCardProcessor
  - CardFetcher
  - SpreadsheetClient
  - Configuration system

- **CLI Layer** (`main.py`): CLI-specific concerns
  - Argument parsing
  - Console output formatting
  - Direct invocation of core components

- **Web Backend Layer** (`backend/`): API-specific concerns
  - HTTP routing and request handling
  - WebSocket management
  - ProcessorService wrapper for async callbacks
  - Job state management

- **Web Frontend Layer** (`frontend/`): UI-specific concerns
  - React components
  - Data fetching with TanStack Query
  - WebSocket client
  - User interaction handlers

#### Scenario: Core modules have no web dependencies
- **WHEN** importing core modules (CardFetcher, MagicCardProcessor)
- **THEN** they have no imports from FastAPI, React, or web-specific libraries

#### Scenario: ProcessorService is only web dependency on core
- **WHEN** web backend needs to use processor
- **THEN** it only interacts through ProcessorService wrapper, never importing MagicCardProcessor directly in routes

## ADDED Requirements

### Requirement: Architecture SHALL document concurrency constraints

The system SHALL document known concurrency limitations between CLI and web.

**Concurrency constraints:**

- CLI and web backend should not run processes (process_cards or update_prices) simultaneously
- Reading collection data is safe to do concurrently (both use same SpreadsheetClient read methods)
- Google Sheets API rate limits (600 req/min) apply across all clients
- In-memory job state in backend is separate from CLI execution

#### Scenario: Concurrent reads are safe
- **WHEN** CLI reads collection while web backend serves /api/cards
- **THEN** both succeed without conflicts (read-only operations)

#### Scenario: Concurrent writes risk race conditions
- **WHEN** CLI processes cards while web backend processes cards
- **THEN** both may attempt to write to same sheet cells causing conflicts (documented risk)

### Requirement: Architecture SHALL define directory structure

The system SHALL organize code into clear directory structure.

**Project structure:**

```
deckdex_mtg/
├── backend/                      # NEW: Web backend
│   ├── api/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── routes/              # API endpoint handlers
│   │   ├── services/            # ProcessorService wrapper
│   │   └── websockets/          # WebSocket handlers
│   └── requirements-api.txt     # Backend dependencies
├── frontend/                     # NEW: Web frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── api/                 # API client code
│   │   └── App.tsx              # Main app component
│   ├── package.json
│   └── vite.config.ts
├── deckdex/                      # EXISTING: Core logic
│   ├── card_fetcher.py
│   ├── magic_card_processor.py
│   ├── spreadsheet_client.py
│   └── config_loader.py
├── main.py                       # EXISTING: CLI entry
├── config.yaml                   # EXISTING: Configuration
├── requirements.txt              # EXISTING: CLI dependencies
└── docker-compose.yml            # NEW: Optional deployment
```

#### Scenario: Backend code isolated in backend/ directory
- **WHEN** examining backend code
- **THEN** all FastAPI-specific code resides in `backend/` directory

#### Scenario: Frontend code isolated in frontend/ directory
- **WHEN** examining frontend code
- **THEN** all React-specific code resides in `frontend/` directory

#### Scenario: Core logic remains in deckdex/ directory
- **WHEN** examining core processor logic
- **THEN** it remains in `deckdex/` directory unchanged

### Requirement: Architecture SHALL define integration points for web layer

The system SHALL document how web layer integrates with existing components.

**Integration points:**

1. **Web Backend → Core:**
   - ProcessorService wraps MagicCardProcessor
   - Backend routes import SpreadsheetClient for reads
   - Backend uses config_loader for configuration

2. **Web Frontend → Backend:**
   - REST API calls via fetch/TanStack Query
   - WebSocket connections for progress updates
   - Vite proxy forwards /api/* to backend

3. **Web Backend → Google Sheets:**
   - Uses existing SpreadsheetClient (no changes)
   - Same authentication mechanism (credentials JSON)

4. **Web Backend → Scryfall:**
   - Uses existing CardFetcher (no changes)
   - Same rate limiting and retry logic

#### Scenario: Backend uses existing SpreadsheetClient
- **WHEN** backend reads collection data
- **THEN** it instantiates SpreadsheetClient exactly as CLI does

#### Scenario: Frontend proxies API requests in development
- **WHEN** frontend makes request to /api/cards
- **THEN** Vite dev server proxies to http://localhost:8000/api/cards

### Requirement: Architecture SHALL support web-specific caching

The system SHALL add caching layer in web backend to reduce API load.

**Caching strategy:**

- Collection data cached with 30-second TTL
- Stats endpoint cached with 30-second TTL
- Cache implemented as simple Python dict with timestamp
- CLI does not use this cache (no shared state)

#### Scenario: API responses cached to reduce Sheets queries
- **WHEN** /api/cards called twice within 30 seconds
- **THEN** backend returns cached data on second call without querying Google Sheets

#### Scenario: Cache invalidated on process completion
- **WHEN** process completes successfully
- **THEN** backend clears collection cache to reflect updated data
