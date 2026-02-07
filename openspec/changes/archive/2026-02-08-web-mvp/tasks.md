## 1. Backend Setup and Structure

- [x] 1.1 Create `backend/` directory structure with api/, routes/, services/, websockets/ subdirectories
- [x] 1.2 Create `backend/requirements-api.txt` with FastAPI, uvicorn, websockets dependencies
- [x] 1.3 Create `backend/api/main.py` with basic FastAPI app initialization and CORS middleware
- [x] 1.4 Implement health check endpoint GET `/api/health` returning service name and version
- [x] 1.5 Create `.env.example` file documenting required environment variables

## 2. Backend - Collection Data Endpoints

- [x] 2.1 Create `backend/api/routes/cards.py` with router for card-related endpoints
- [x] 2.2 Implement GET `/api/cards` endpoint reading from Google Sheets via SpreadsheetClient
- [x] 2.3 Add pagination support with `limit` and `offset` query parameters to `/api/cards`
- [x] 2.4 Add search filtering with `search` query parameter (case-insensitive name matching)
- [x] 2.5 Implement GET `/api/cards/{card_name}` endpoint for single card details
- [x] 2.6 Add 30-second TTL cache for collection reads to reduce Sheets API calls
- [x] 2.7 Fix SpreadsheetClient instantiation: pass `config=GoogleSheetsConfig` object, not individual kwargs
- [x] 2.8 Fix credentials_path resolution: load from .env via `GOOGLE_API_CREDENTIALS` when config returns None
- [x] 2.9 Fix column mapping to match actual Google Sheets headers (20 columns, not 23)
- [x] 2.10 Add safe_str/safe_float helpers to handle N/A and non-numeric values in Sheets data
- [x] 2.11 Skip header row from get_all_values() (first row is column names)
- [x] 2.12 Ignore literal "undefined" string in search parameter (JS URLSearchParams edge case)

## 3. Backend - Statistics Endpoint

- [x] 3.1 Create `backend/api/routes/stats.py` with router for statistics
- [x] 3.2 Implement GET `/api/stats` endpoint calculating total_cards, total_value, average_price
- [x] 3.3 Add last_updated timestamp to stats response
- [x] 3.4 Implement 30-second cache for stats calculations

## 4. Backend - ProcessorService Wrapper

- [x] 4.1 Create `backend/api/services/processor_service.py` module
- [x] 4.2 Implement `ProcessorService` class that wraps `MagicCardProcessor`
- [x] 4.3 Add `progress_callback` parameter to ProcessorService constructor
- [x] 4.4 Implement `process_cards_async()` method that runs processor in thread pool
- [x] 4.5 Implement `update_prices_async()` method for price updates
- [x] 4.6 Implement `ProgressCapture` class that intercepts tqdm stderr/stdout output
- [x] 4.7 Extract current/total/percentage from tqdm output via regex pattern matching
- [x] 4.8 Emit WebSocket progress events in real-time via `asyncio.run_coroutine_threadsafe`
- [x] 4.9 Add completion event emission with summary when process finishes
- [x] 4.10 Implement thread-safe state access with locks for progress updates
- [x] 4.11 Add job metadata tracking (job_id, start_time, configuration)
- [x] 4.12 Restore original stderr/stdout in finally block to prevent stream corruption

## 5. Backend - Process Execution Endpoints

- [x] 5.1 Create `backend/api/routes/process.py` with router for process operations
- [x] 5.2 Implement POST `/api/process` endpoint creating new card processing job
- [x] 5.3 Implement POST `/api/prices/update` endpoint creating new price update job
- [x] 5.4 Add job state management with in-memory dict keyed by job_id
- [x] 5.5 Generate UUID job_id for each new process
- [x] 5.6 Add concurrency check to prevent multiple simultaneous processes (return 409 Conflict)
- [x] 5.7 Implement GET `/api/jobs/{job_id}` endpoint for querying job status
- [x] 5.8 Return 404 Not Found for non-existent job_ids
- [x] 5.9 Implement GET `/api/jobs` endpoint listing all active and recently completed jobs
- [x] 5.10 Track job_type ('process' or 'update_prices') per job_id
- [x] 5.11 Keep completed jobs in _active_jobs for frontend polling (don't delete immediately)
- [x] 5.12 Add `_cleanup_old_jobs()` to prevent memory leaks (cleans up on new job creation)

## 6. Backend - WebSocket Progress Implementation

- [x] 6.1 Create `backend/api/websockets/progress.py` module
- [x] 6.2 Implement WebSocket endpoint at `/ws/progress/{job_id}`
- [x] 6.3 Add connection validation (reject if job_id not found with close code 4004)
- [x] 6.4 Implement progress event broadcasting to all connected clients for same job_id
- [x] 6.5 Add JSON serialization for progress events with type, current, total, percentage fields
- [x] 6.6 Add JSON serialization for error events with type, card_name, error_type, message fields
- [x] 6.7 Add JSON serialization for complete events with type, status, summary fields
- [x] 6.8 Include timestamp (ISO 8601) in all WebSocket events
- [x] 6.9 Implement heartbeat ping frames every 30 seconds for connection health
- [x] 6.10 Handle client disconnection gracefully (continue processing in background)
- [x] 6.11 Close WebSocket with code 1000 after sending complete event
- [x] 6.12 Log connection establishment and disconnection at INFO level

## 7. Backend - Error Handling and Logging

- [x] 7.1 Add global exception handler returning 500 Internal Server Error with logging
- [x] 7.2 Add validation error handler returning 400 Bad Request with details
- [x] 7.3 Handle Google Sheets quota errors returning 503 Service Unavailable
- [x] 7.4 Configure loguru logger for backend operations (INFO level default)
- [x] 7.5 Log all API requests with endpoint, method, and response status
- [x] 7.6 Log WebSocket events at appropriate levels (INFO for connections, ERROR for exceptions)

## 8. Backend - Testing and Documentation

- [x] 8.1 Create `backend/README.md` with setup and running instructions
- [x] 8.2 Document environment variables required (GOOGLE_API_CREDENTIALS, OPENAI_API_KEY)
- [x] 8.3 Add example curl commands for testing endpoints in README
- [ ] 8.4 Test all REST endpoints manually with curl or Postman
- [ ] 8.5 Test WebSocket connection with wscat or browser console

## 9. Frontend - Project Setup

- [x] 9.1 Create `frontend/` directory and initialize Vite + React + TypeScript project
- [x] 9.2 Install dependencies: @tanstack/react-query, @tailwindcss/postcss, tailwindcss v4, lucide-react
- [x] 9.3 Configure Tailwind CSS v4: use `@import "tailwindcss"` in index.css, `@tailwindcss/postcss` plugin in postcss.config.js (no tailwind.config.js needed in v4)
- [x] 9.4 Configure Vite proxy in vite.config.ts to forward /api/* and /ws/* to http://localhost:8000
- [x] 9.5 Create basic App.tsx with routing structure
- [x] 9.6 Relax tsconfig.app.json: disable verbatimModuleSyntax, noUnusedLocals, noUnusedParameters for MVP flexibility

## 10. Frontend - API Client Setup

- [x] 10.1 Create `frontend/src/api/client.ts` with base fetch configuration
- [x] 10.2 Setup TanStack Query provider in main.tsx
- [x] 10.3 Create custom hook `useCards()` for fetching card collection
- [x] 10.4 Create custom hook `useStats()` for fetching statistics
- [x] 10.5 Create custom hook `useWebSocket(jobId)` for WebSocket connection management
- [x] 10.6 Configure TanStack Query with 30-second stale time for caching
- [x] 10.7 Fix API client to filter undefined params from URLSearchParams (prevents `search=undefined`)
- [x] 10.8 Fix API client URLs to include trailing slashes (prevents 307 redirect loops)
- [x] 10.9 Use relative WebSocket URL (wsProtocol + host) instead of hardcoded localhost

## 11. Frontend - Dashboard Statistics Cards

- [x] 11.1 Create `frontend/src/components/StatsCards.tsx` component
- [x] 11.2 Display total cards count in stat card
- [x] 11.3 Display total collection value formatted as currency in stat card
- [x] 11.4 Display last updated timestamp in relative format (e.g., "2 hours ago")
- [x] 11.5 Add loading skeleton state for stats cards
- [x] 11.6 Style stats cards with Tailwind CSS (grid layout, shadow, rounded corners)

## ~~12. Frontend - Price Chart Component~~ REMOVED

- ~~12.1-12.5~~ Removed: PriceChart component eliminated from MVP. No local database exists to track historical price data. Google Sheets only stores current values. Price history tracking would require a new SQLite/persistent store — out of scope for MVP.

## 13. Frontend - Card Table Component

- [x] 13.1 Create `frontend/src/components/CardTable.tsx` component
- [x] 13.2 Display card data in table with columns: Name, Type, Rarity, Price, Set
- [x] 13.3 Implement client-side pagination showing 50 cards per page
- [x] 13.4 Add pagination controls (Previous, Next, page numbers)
- [x] 13.5 Implement column sorting (click header to sort ascending/descending)
- [x] 13.6 Add loading state with skeleton rows
- [x] 13.7 Style table with Tailwind CSS (striped rows, hover effects)

## 14. Frontend - Filtering Controls

- [x] 14.1 Create `frontend/src/components/Filters.tsx` component
- [x] 14.2 Add search input for filtering cards by name (debounced)
- [x] 14.3 Add rarity dropdown filter (all, common, uncommon, rare, mythic)
- [x] 14.4 Add "Clear Filters" button to reset all filters
- [x] 14.5 Wire filters to CardTable component state
- [x] 14.6 Style filters with Tailwind CSS (flex layout, input styling)

## 15. Frontend - Action Buttons

- [x] 15.1 Create `frontend/src/components/ActionButtons.tsx` component
- [x] 15.2 Add "Process Cards" button that triggers POST to `/api/process`
- [x] 15.3 Add "Update Prices" button that triggers POST to `/api/prices/update`
- [x] 15.4 Disable buttons and show "Starting..." when job is being created
- [x] 15.5 Handle button click errors with alert notifications
- [x] 15.6 Style buttons with Tailwind CSS (primary button style, disabled state)
- [x] 15.7 Pass job type string ('Process Cards' / 'Update Prices') to onJobStarted callback

## 16. Frontend - Progress Modal Component

- [x] 16.1 Create `frontend/src/components/ProcessModal.tsx` component
- [x] 16.2 Display modal overlay when process starts
- [x] 16.3 Show progress bar with percentage updated from WebSocket events
- [x] 16.4 Display "Processing X/Y cards" or "Initializing..." text
- [x] 16.5 Display scrollable error list for failed cards (up to 20 shown)
- [x] 16.6 Show completion summary with success/error status when done
- [x] 16.7 Add "Done" button to close modal after completion
- [x] 16.8 Add "Minimize (continues in background)" button for running jobs
- [x] 16.9 Display WebSocket connection status ("Connecting...", "Connected", "Done", "Disconnected")
- [x] 16.10 Style modal with Tailwind CSS (centered, shadow, bg-black/50 overlay)
- [x] 16.11 Notify parent via onComplete callback when job finishes
- [x] 16.12 Expose summary data from WebSocket complete events for error/success display

## 17. Frontend - Error Handling and Notifications

- [x] 17.1 Handle action button errors with alert dialog
- [x] 17.2 Handle TanStack Query errors with backend connection error page
- [x] 17.3 Add ErrorBoundary component for catching React render errors (wraps entire app in main.tsx)
- [x] 17.4 Display fallback UI when error boundary catches error
- [x] 17.5 Add backend connection error page in Dashboard (shown when API is unreachable, with retry button)
- [x] 17.6 Use Tailwind v4 compatible opacity syntax (bg-black/50 instead of bg-opacity-50)

## 18. Frontend - Dashboard Integration

- [x] 18.1 Create `frontend/src/pages/Dashboard.tsx` page component
- [x] 18.2 Compose Dashboard with StatsCards, Filters, CardTable, ActionButtons, ActiveJobs
- [x] 18.3 Implement layout with Tailwind CSS (stats row, actions, filters, table)
- [x] 18.4 Add auto-refresh for stats and cards every 30 seconds
- [x] 18.5 Handle loading states across all dashboard sections
- [x] 18.6 Track background jobs in state (jobId, type, startedAt)
- [x] 18.7 Support minimizing/reopening progress modals via ActiveJobs panel
- [ ] 18.8 Test dashboard with real backend API (manual)

## 19. Frontend - Active Jobs Floating Panel (NEW)

- [x] 19.1 Create `frontend/src/components/ActiveJobs.tsx` component
- [x] 19.2 Display floating bar in bottom-right corner when background jobs exist
- [x] 19.3 Show job type, elapsed time, and mini SVG progress ring for each job
- [x] 19.4 Poll GET `/api/jobs/{id}` every 2 seconds for status updates
- [x] 19.5 Allow clicking a job to re-open its progress modal
- [x] 19.6 Hide job from panel when it's currently shown in the modal
- [x] 19.7 Auto-remove completed/failed jobs from panel after 5 seconds
- [x] 19.8 Show different colors: dark for running, green for complete, red for error

## 20. Backend - Job Cancellation (NEW)

- [x] 20.1 Add `JobCancelledException` custom exception class in `processor_service.py`
- [x] 20.2 Add `cancel_event` parameter to `ProgressCapture.__init__()` (accepts `threading.Event`)
- [x] 20.3 Check cancel flag in `ProgressCapture.write()` — raise `JobCancelledException` if set
- [x] 20.4 Check cancel flag in `ProgressCapture.flush()` — raise `JobCancelledException` if set
- [x] 20.5 Pass `self._cancel_flag` to `ProgressCapture` instances in `process_cards_async()` and `update_prices_async()`
- [x] 20.6 Catch `JobCancelledException` in `run_processor()` and `run_update()` — return `{'status': 'cancelled', ...}`
- [x] 20.7 Add `cancel_async()` method to `ProcessorService`: sets cancel flag + emits WebSocket `complete` event with status `cancelled`
- [x] 20.8 Skip emitting duplicate `complete` event from `process_cards_async`/`update_prices_async` if cancel flag is already set
- [x] 20.9 Implement `POST /api/jobs/{job_id}/cancel` endpoint in `process.py`
- [x] 20.10 Validate job exists and is in `running` state before cancelling (return 404/409 otherwise)
- [x] 20.11 Store cancelled job result in `_job_results`
- [x] 20.12 Add `cancelJob(jobId)` function to frontend API client (`client.ts`)

## 21. Frontend - Stop Button & Cancelled State (NEW)

- [x] 21.1 Add red "Stop" button to `ProcessModal` footer (shown alongside "Minimize" while job is running)
- [x] 21.2 Add `isCancelling` state: disable Stop button and show "Stopping..." while cancel request is in flight
- [x] 21.3 Change progress bar color to orange while cancelling
- [x] 21.4 Handle `cancelled` status in ProcessModal completion message (orange styling, shows progress at cancellation)
- [x] 21.5 Handle `cancelled` status in ActiveJobs panel (orange background, cancel icon, "Cancelled" label)
- [x] 21.6 Treat `cancelled` as terminal state in ActiveJobs polling (auto-remove after 5 seconds)

## 22. Backend - WebSocket Progress Reconnect (NEW)

- [x] 22.1 On WebSocket connect, read current `progress_data` and `status` from `ProcessorService` in `_active_jobs`
- [x] 22.2 If job is `running` with progress > 0, send immediate `progress` event after `connected` ack
- [x] 22.3 If job already finished (`complete`/`error`), send immediate `complete` event with result from `_job_results`
- [x] 22.4 Include `job_status` field in the `connected` WebSocket message

## 23. Frontend - Progress Reconnect & Elapsed Timer (NEW)

- [x] 23.1 In `useWebSocket` hook, fetch `GET /api/jobs/{id}` immediately on `jobId` change (before WebSocket connects)
- [x] 23.2 Use REST response as initial progress state (avoids 0% flash on modal reopen)
- [x] 23.3 If REST says job already completed, set `complete` and `summary` directly without waiting for WebSocket
- [x] 23.4 Use `cancelled` flag to prevent state updates if effect is cleaned up before REST resolves
- [x] 23.5 Add `startedAt?: Date` prop to `ProcessModal`
- [x] 23.6 Implement live elapsed time counter with `setInterval` (updates every second)
- [x] 23.7 Format elapsed time adaptively: `12s`, `2m 34s`, `1h 5m 12s`
- [x] 23.8 Freeze timer on job completion (capture `finishedAt` timestamp)
- [x] 23.9 Display timer in modal header with clock icon and monospaced font (`font-mono tabular-nums`)
- [x] 23.10 Pass `startedAt` from Dashboard's `backgroundJobs` state to `ProcessModal` via lookup

## 24. Deployment - Docker Setup (Optional)

- [x] 24.1 Create `backend/Dockerfile` for FastAPI backend
- [x] 24.2 Create `frontend/Dockerfile` for Vite dev server (or production build)
- [x] 24.3 Create `docker-compose.yml` at project root
- [x] 24.4 Configure docker-compose to run backend on port 8000 and frontend on port 5173
- [x] 24.5 Add volume mounts for development hot-reload
- [ ] 24.6 Test docker-compose up starts both services correctly

## 25. Documentation and Final Testing

- [x] 25.1 Update root `README.md` with web MVP section
- [x] 25.2 Document how to run backend (uvicorn command)
- [x] 25.3 Document how to run frontend (npm run dev command)
- [x] 25.4 Document docker-compose usage
- [x] 25.5 Document concurrency risk (CLI and web should not process simultaneously)
- [ ] 25.6 Test end-to-end: start backend, start frontend, process cards, verify updates
- [ ] 25.7 Test end-to-end: start backend, start frontend, update prices, verify progress tracking
- [ ] 25.8 Test end-to-end: start job, cancel via Stop button, verify processor stops
- [ ] 25.9 Test end-to-end: minimize modal, reopen, verify progress is preserved (not 0%)
- [ ] 25.10 Verify existing CLI still works without any changes
