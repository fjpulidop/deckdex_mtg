## Context

DeckDex MTG is a CLI-first tool with a robust architecture for fetching card data from Scryfall and syncing to Google Sheets. The core processing logic (`MagicCardProcessor`, `CardFetcher`, `SpreadsheetClient`) is well-established and tested. Users want a graphical interface to visualize their collection, track price changes, and execute processes with visual feedback without replacing the CLI.

**Current architecture:**
- CLI entry point: `main.py` with comprehensive configuration system
- Core modules: `deckdex/` (card_fetcher, magic_card_processor, spreadsheet_client, config_loader)
- Data store: Google Sheets as source of truth
- External APIs: Scryfall (card data), OpenAI (optional enrichment)

**Constraints:**
- Cannot modify core logic behavior (CLI must continue working identically)
- Google Sheets remains the single source of truth (no dual-write scenarios)
- MVP targets localhost only (no production hosting, no authentication)
- Assume collection size < 2000 cards for MVP

## Goals / Non-Goals

**Goals:**
- Create a web dashboard to visualize collection statistics and price trends
- Provide REST API to access card data and trigger processes
- Show real-time progress feedback via WebSocket for long-running operations
- Reuse 100% of existing processor logic through a wrapper pattern
- Enable simple local deployment with two commands (backend + frontend)
- Document deployment and usage clearly

**Non-Goals:**
- Modifying existing CLI behavior or core processor logic
- Production-ready authentication/authorization (localhost trusted for MVP)
- Complex pagination for large collections (assume < 2000 cards)
- Persistent job queue across backend restarts (in-memory state acceptable)
- Direct card editing from UI (read-only + process triggers)
- Mobile-responsive UI (desktop-first for MVP)

## Decisions

### 1. Backend Framework: FastAPI

**Decision:** Use FastAPI for the REST API backend.

**Rationale:**
- Native async/await support for WebSocket and concurrent operations
- Automatic OpenAPI documentation (useful for frontend development)
- Fast and lightweight, suitable for local deployment
- Strong typing with Pydantic models aligns with existing Python codebase
- Built-in CORS middleware for local dev frontend

**Alternatives considered:**
- Flask: Simpler but lacks native async and automatic API docs
- Django REST Framework: Overkill for MVP, heavyweight for local-only deployment

### 2. Frontend Framework: React + Vite

**Decision:** Use React with Vite as build tool and dev server.

**Rationale:**
- React is well-established with excellent ecosystem for data visualization
- Vite provides fast HMR and simple configuration
- TanStack Query handles API caching, refetching, and loading states automatically
- Recharts offers simple declarative charts without D3 complexity
- Tailwind CSS v4 enables rapid styling without custom CSS (using `@import "tailwindcss"` directive and `@tailwindcss/postcss` plugin)

**Alternatives considered:**
- Vue: Smaller learning curve but React has better visualization library support
- Next.js: Adds SSR complexity unnecessary for localhost-only MVP
- Plain HTML/JS: Would require manual state management and API handling

### 3. Processor Integration: Wrapper Pattern

**Decision:** Create a `ProcessorService` wrapper around `MagicCardProcessor` that adds async callbacks without modifying the core.

**Rationale:**
- Zero risk to existing CLI functionality (no core code changes)
- Allows injecting progress callbacks for WebSocket updates
- Can be implemented quickly without extensive testing of core logic
- Future refactoring can merge this if web becomes primary interface

**Implementation approach:**
```python
class ProcessorService:
    def __init__(self, config: ProcessorConfig, progress_callback=None):
        self.processor = MagicCardProcessor(config)
        self.progress_callback = progress_callback
    
    async def process_cards_async(self):
        # Wrap processor calls with progress notifications
        # Emit events to WebSocket via callback
```

**Alternatives considered:**
- Modifying MagicCardProcessor directly: Higher risk, requires extensive CLI regression testing
- Separate reimplementation: Code duplication, divergence over time

### 4. Real-Time Updates: WebSocket over Polling

**Decision:** Use WebSocket for real-time progress updates instead of HTTP polling.

**Rationale:**
- Lower latency: updates pushed immediately vs. polling interval
- Reduced server load: single connection vs. repeated HTTP requests
- Better UX: smooth progress bar updates
- FastAPI has native WebSocket support

**Event types:**
```json
{"type": "progress", "current": 450, "total": 1000, "percentage": 45}
{"type": "error", "card_name": "Foo", "message": "not found"}
{"type": "complete", "summary": {"success": 992, "errors": 8}}
```

**Alternatives considered:**
- HTTP polling: Simpler but wasteful, adds 1-5s latency
- Server-Sent Events (SSE): Simpler than WebSocket but unidirectional

### 5. Data Source: Google Sheets (No New Database)

**Decision:** Continue using Google Sheets as the single source of truth. Backend reads from Sheets via existing `SpreadsheetClient`.

**Rationale:**
- Zero migration effort (sheets already populated and maintained)
- No dual-write complexity or sync bugs
- Users can continue using sheets directly
- Existing auth and permissions already configured

**Trade-offs:**
- Sheets API has rate limits (600 requests/minute per user)
- Query performance limited compared to SQL database
- No complex filtering/aggregation on backend

**Mitigation:**
- Cache collection data in-memory with 30s TTL
- Use batch reads from Sheets client (already implemented)
- For MVP, full collection reads acceptable (< 2000 cards)

**Alternatives considered:**
- SQLite local database: Adds complexity, requires migration script, dual-write issues
- PostgreSQL: Overkill for local MVP, deployment complexity

### 6. Job State Management: In-Memory

**Decision:** Store job state (process execution status) in-memory using Python dict with job_id keys.

**Rationale:**
- Simple and fast for MVP
- No additional dependencies
- Acceptable for localhost usage (single user, backend runs continuously)

**Trade-offs:**
- Job state lost on backend restart
- No historical job logs

**Mitigation:**
- Document that backend should remain running during processes
- Add job completion notifications to UI
- Future: persist to SQLite if historical tracking needed

**Alternatives considered:**
- Redis: Requires separate service, overkill for localhost MVP
- SQLite: Adds complexity for MVP, can be added later if needed

### 7. Deployment: Dual Process (Dev Servers)

**Decision:** Run backend (uvicorn) and frontend (vite) as separate processes. Optional docker-compose for convenience.

**Rationale:**
- Simple for local development (two terminal windows)
- Frontend proxies API requests to backend in vite.config.ts
- No build step needed during development
- Docker-compose provides one-command startup for users who prefer it

**Setup:**
```bash
# Terminal 1: Backend
cd backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend  
cd frontend
npm run dev  # Runs on :5173, proxies /api/* to :8000
```

**Alternatives considered:**
- Single FastAPI serving static build: Requires build step, slower dev iteration
- Production nginx setup: Unnecessary for localhost MVP

## Risks / Trade-offs

### [Risk] Concurrency: CLI and Web running simultaneously

**Impact:** If CLI and web both write to Google Sheets at the same time, race conditions or quota errors may occur.

**Mitigation:**
- Document in README: "Do not run CLI processes while web is processing"
- Add warning banner in web UI when process is running
- Future: Implement file lock or process coordination mechanism

### [Risk] Collection size exceeds 2000 cards

**Impact:** Loading entire collection into memory and rendering large tables may cause performance issues.

**Mitigation:**
- For MVP: Document assumption of < 2000 cards
- Add simple frontend pagination (display 50 cards per page client-side)
- Future: Implement backend pagination with offset/limit if needed

### [Risk] Backend restart loses active job state

**Impact:** If backend crashes during process, frontend loses connection and user cannot resume.

**Mitigation:**
- Leverage existing `--resume-from` CLI flag: backend can suggest resume row
- Document that long processes should be monitored
- Future: Persist job state to SQLite for resumability

### [Risk] Google Sheets API rate limits

**Impact:** Frequent dashboard refreshes could hit 600 req/min limit.

**Mitigation:**
- Implement 30-second TTL cache in backend for collection reads
- Frontend uses TanStack Query with 30s stale time (avoids excessive refetching)
- Batch reads using existing SpreadsheetClient logic

### [Trade-off] No authentication for MVP

**Impact:** Anyone with localhost access can trigger processes.

**Mitigation:**
- MVP is localhost-only (inherently trusted environment)
- Document that this is not production-ready
- Future: Add basic auth with password in .env if deploying to LAN

### [Trade-off] In-memory job state is ephemeral

**Impact:** Cannot view historical process runs or debug past failures.

**Mitigation:**
- Existing CSV error reports still generated (output/ directory)
- Frontend shows real-time errors during process
- Future: Add job history table if needed

## Migration Plan

**Phase 1: Backend Setup**
1. Create `backend/` directory structure
2. Implement FastAPI app with basic health endpoint
3. Create ProcessorService wrapper with mock progress callback
4. Implement `/api/cards` endpoint reading from Sheets
5. Implement `/api/stats` endpoint (aggregations)
6. Test endpoints with curl/Postman

**Phase 2: Frontend Skeleton**
1. Initialize Vite + React + TypeScript project in `frontend/`
2. Setup Tailwind CSS v4 with `@tailwindcss/postcss` plugin and `@import "tailwindcss"` in index.css (no tailwind.config.js needed in v4)
3. Create Dashboard component structure (empty placeholders)
4. Integrate TanStack Query and connect to `/api/cards` and `/api/stats`
5. Display basic card table and stats cards
6. Add ErrorBoundary component for graceful React error handling

**Phase 3: WebSocket + Process Execution**
1. Implement WebSocket endpoint `/ws/progress/{job_id}` in backend
2. Wire ProcessorService callbacks to emit WebSocket events
3. Create job management routes: POST `/api/process`, GET `/api/jobs/{id}`
4. Frontend: ProcessModal component with WebSocket connection
5. Test end-to-end process flow with real data

**Phase 4: Job Management & Polish**
1. Add ActiveJobs floating panel for background job tracking (mini progress rings, click to reopen modal)
2. Implement filters on card table (search, rarity)
3. Add error handling UI (display failed cards, ErrorBoundary, backend connection error page)
4. Implement tqdm interception in ProcessorService for real-time progress via WebSocket
5. Add GET /api/jobs endpoint for listing all active/recent jobs
6. Create docker-compose.yml for optional one-command startup
7. Write deployment docs in README
8. Use Tailwind v4 compatible syntax (e.g., `bg-black/50` instead of `bg-black bg-opacity-50`)
9. Remove PriceChart component (no local database for historical data, out of MVP scope)

**Phase 5: Job Cancellation, Progress Reconnect & UX Polish**
1. Add `POST /api/jobs/{job_id}/cancel` endpoint for job cancellation
2. Implement `JobCancelledException` in ProgressCapture — raises on `write()`/`flush()` when cancel flag is set, aborting the processor from within its own thread
3. Add `cancel_async()` to ProcessorService: sets cancel flag + emits WebSocket `complete` event with `status: cancelled`
4. ProgressCapture receives `cancel_event` (threading.Event) and checks it on every stream write
5. Frontend: Add Stop button (red) to ProcessModal alongside Minimize button
6. Frontend: Handle `cancelled` state in ProcessModal (orange styling, progress-at-cancellation message)
7. Frontend: Handle `cancelled` state in ActiveJobs panel (orange badge, auto-remove after 5s)
8. Add `cancelJob()` to frontend API client
9. WebSocket reconnect with current state: on connect, backend sends current `progress_data` snapshot from ProcessorService (not just `connected` ack)
10. WebSocket sends `complete` event immediately if job already finished when client reconnects
11. Frontend `useWebSocket` hook: fetch initial progress from REST `/api/jobs/{id}` before connecting WebSocket (avoids 0% flash on modal reopen)
12. Add elapsed time counter to ProcessModal header (live timer, freezes on completion)
13. Pass `startedAt` from Dashboard's job tracking state to ProcessModal

**Rollback strategy:**
- Web layer is additive only (no changes to core)
- Can delete `backend/` and `frontend/` directories without affecting CLI
- No database migrations to revert

**Testing approach:**
- Backend: pytest for API endpoints, mock SpreadsheetClient
- Frontend: Manual testing in browser (MVP, no automated tests)
- Integration: Test with real Google Sheets in dev environment

## Resolved Questions

1. **Price history visualization:** Removed from MVP.
   - **Decision:** No local database exists to track historical prices. Google Sheets only stores current values, not snapshots over time. The PriceChart component was removed entirely as it was mock-only with no path to real data. A future version could add SQLite to snapshot daily totals, but this is out of MVP scope.

2. **Error handling for WebSocket disconnects:** Basic handling implemented.
   - **Decision:** WebSocket disconnects set status to 'disconnected'. Frontend polls via REST `/api/jobs/{id}` as fallback for progress tracking (used by ActiveJobs floating panel).

3. **Stats calculations:** Cached for 30 seconds.
   - **Decision:** Simple in-memory cache with TTL implemented.

4. **Job ID generation:** UUID v4.
   - **Decision:** Use Python `uuid.uuid4()` for job IDs.

5. **Background job visibility:** Floating ActiveJobs panel.
   - **Decision:** When a user minimizes a progress modal (or starts multiple jobs), a floating panel appears in the bottom-right corner showing all active jobs with mini progress rings. Clicking a job re-opens its progress modal. Jobs are tracked both via WebSocket (real-time) and REST polling (fallback). Panel auto-removes completed jobs after 5 seconds.

6. **Real-time progress for processes:** tqdm interception.
   - **Decision:** The core MagicCardProcessor uses tqdm for progress bars. Since we cannot modify core code, ProcessorService intercepts sys.stderr/sys.stdout to capture tqdm output, extracts current/total/percentage via regex, and emits WebSocket progress events. This works for both process_cards and update_prices operations.

7. **Job cancellation:** ProgressCapture as cancellation injection point.
   - **Decision:** Since MagicCardProcessor doesn't support cancellation natively, we use the same stream interception mechanism (ProgressCapture) to abort the processor. When the cancel flag is set, `ProgressCapture.write()` raises `JobCancelledException`, which propagates up through `tqdm.update()` → the processor's iteration loop → caught cleanly by the wrapper. This stops the processor at the next tqdm write (i.e., after the current batch finishes). For `process_cards` (sequential loop), cancellation is near-instant. For `update_prices` (ThreadPoolExecutor), in-progress batches complete but no new results are collected. No core code modifications required.

8. **Progress reconnection on modal reopen:** Dual initialization (REST + WebSocket).
   - **Decision:** When a user minimizes a progress modal and reopens it later, the progress state must not reset to 0%. Two mechanisms ensure this: (a) Frontend `useWebSocket` hook immediately fetches current progress from `GET /api/jobs/{id}` as initial state, (b) Backend WebSocket endpoint sends current `progress_data` snapshot from the active ProcessorService immediately after accepting the connection. The REST fetch provides instant display, and WebSocket events take over for real-time updates.

9. **Elapsed time display in progress modal.**
   - **Decision:** The ProcessModal displays a live elapsed time counter in its header (clock icon + monospaced font), matching the timer shown in the ActiveJobs floating panel. The timer updates every second while the job is running and freezes at the final duration when the job completes/cancels/fails. The `startedAt` timestamp is passed from the Dashboard's job tracking state.
