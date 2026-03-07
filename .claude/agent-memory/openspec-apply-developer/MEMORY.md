# OpenSpec Apply Developer Memory

## OpenSpec CLI Commands

- `openspec new change "<name>"` — create new change directory
- `openspec status --change "<name>" --json` — check artifact completion
- `openspec instructions <artifact> --change "<name>" --json` — get instructions for a specific artifact (not `--json` with no artifact)
- `openspec archive <name>` — archives to `openspec/changes/archive/<date>-<name>`
- Apply workflow: proposal → design + specs → tasks → implement → mark [x] → archive

## Codebase Patterns

### Testing
- Test files: `tests/test_<module>.py`, pytest functions (not unittest.TestCase)
- Gold standard: `tests/test_decks.py` — module-scoped fixture, dependency_overrides, MagicMock
- conftest.py has `SAMPLE_CARDS`, `client` fixture, `make_test_client()` helper
- InsightsService is a pure-computation class — no mocking needed, takes `List[Dict]` directly

### FastAPI Dependency Injection (testing)
- `get_current_user_id` → FastAPI Depends → use `app.dependency_overrides[dep_fn] = lambda: value`
- `get_collection_repo`, `get_catalog_repo`, `get_job_repo`, `get_user_settings_repo` → called DIRECTLY in route bodies (not Depends) → must `patch("backend.api.routes.<module>.<fn>", return_value=...)`
- Parsers imported inline in routes → patch at `deckdex.importers.<module>.<fn>` or `backend.api.routes.import_routes._parse_file`

### Rate Limiter (slowapi)
- Created in `backend/api/main.py`: `limiter = Limiter(key_func=get_remote_address)`
- Import routes use `@limiter.limit("5/minute")` decorator — must disable in tests
- Test bypass: `mock_limiter.limit.return_value = lambda f: f` then patch both `app.state.limiter` AND `backend.api.routes.import_routes.limiter`

### Import Routes (`backend/api/routes/import_routes.py`)
- 5 endpoints: `/file`, `/preview`, `/resolve`, `/external`, `/external/cards`
- Background job pattern: route schedules task, returns `{job_id, card_count, format, mode}`
- Tests verify response shape only for background tasks (don't wait for execution)

### InsightsService Gotchas
- `rarity_order = ["Mythic", "Rare", "Uncommon", "Common"]` — uses `.capitalize()` so "mythic rare" falls outside
- `_normalize_color_identity("")` returns "C" (colorless), as does None and "[]"
- `_parse_price` handles EU format (comma as decimal): "1,50" → 1.5

### Key File Paths
- Core insights: `backend/api/services/insights_service.py`
- Tests location: `tests/` only
- Layer-specific docs: `backend/CLAUDE.md`, `.claude/rules/testing.md`

## OpenSpec Workflow Notes
- Delta spec format requires `## ADDED/MODIFIED/REMOVED/RENAMED Requirements` + `#### Scenario:` blocks for archival validation
- Pure test-only changes (no spec delta) archive with a non-blocking warning — that's fine
- `openspec instructions apply --change "<name>" --json` gives task list and context files
- Manually create specs in `openspec/changes/<name>/specs/<capability>/spec.md` when needed
- When Bash is denied: create change artifacts manually (proposal.md, design.md, tasks.md) in `openspec/changes/<name>/` and archive to `openspec/changes/archive/YYYY-MM-DD-<name>/`
- `openspec archive "<name>" -y --skip-specs` — use when spec delta files don't use exact ADDED/MODIFIED/REMOVED/RENAMED format
- Run `openspec` commands from `/Users/javi/repos/deckdex_mtg/` (main repo root), NOT from worktrees

## Job Persistence Fixes (2026-03-07)

### Patching Direct Function Calls vs Depends
- `get_job_repo()` is called DIRECTLY in routes (not via `Depends`), so patch at `backend.api.routes.process.get_job_repo` not via `dependency_overrides`
- Same applies to `get_collection_repo()`, `get_catalog_repo()` in route bodies

### Catalog Service Lock Testing
- `_sync_lock` is module-global in `catalog_service.py` — tests calling `start_sync` must release it in `tearDown`; lock may still be held if background thread hasn't finished
- Pattern: `if cs._sync_lock.locked(): cs._sync_lock.release()` in both setUp and tearDown

### `import X` Local Binding Pitfall
- `import X` anywhere in a function creates a local binding for `X` in the ENTIRE function scope
- If `X` is used before the `import X` line → `UnboundLocalError` at the earlier usage
- Fix: move `import X` to the top of the function, or use module-level import

### Status Canonical Values
- `'running'`, `'complete'`, `'error'`, `'cancelled'` — NOT `'completed'` or `'failed'`
- `update_job_status` CASE expression uses these exact strings to set `completed_at`

### openspec Archive with MODIFIED specs
- MODIFIED requires the exact `### Requirement: Header` to exist in the target spec file before archiving
- If missing: add the section to the target spec manually, then archive
- Fallback: `openspec archive "<name>" -y --skip-specs` skips spec update entirely

## SQL Pagination and Filtering (2026-03-06)

### Cache User Isolation Pattern
- `_collection_cache` MUST be `dict[int, dict]` keyed by `user_id`, not a single global dict
- `clear_collection_cache(user_id=None)` — clears specific user or all entries
- Stats and analytics caches must include `user_id` in their tuple keys

### Dual-Path Pattern (Postgres vs Sheets)
- `repo = get_collection_repo()` — if non-None, use SQL path; else Python/cache path
- SQL methods: `repo.get_cards_filtered()`, `repo.get_cards_stats()`, `repo.get_cards_analytics()`
- `_build_filter_clauses(filters, user_id)` returns `(where_str, params_dict)` — fully parameterized

### Paginated API Response
- `GET /api/cards/` now returns `{ items: Card[], total: int, limit: int, offset: int }`
- Frontend uses `CardPage` interface (named `CardPage`, not `CardListResponse`)
- `useCards()` returns `{ data: CardPage | undefined }` — access via `data.items`

### Route Ordering Rule
- Specific routes (`/filter-options`, `/suggest`, `/resolve`, `/{id}/price-history`, `/{id}/image`) must be before `/{card_id_or_name}`
- FastAPI matches more-specific paths first when path segments are concrete

### Test Mocking for Dual-Path Routes
- Always mock BOTH `get_collection_repo` (return None) AND `get_cached_collection` for unit tests
- `patch("backend.api.routes.cards.get_collection_repo", return_value=None)` forces Sheets path

### Window Function Pagination
- `COUNT(*) OVER() AS total_count, * FROM cards WHERE ... LIMIT :limit OFFSET :offset`
- Single query returns both rows AND total — no second COUNT(*) query needed

## Server-Side Sorting (2026-03-07)

### Sort Column Whitelist Pattern
- Backend: `_ALLOWED_SORT_COLUMNS` set in route validates input; `_SORT_COLUMN_MAP` dict in `PostgresCollectionRepository` is the second defense layer before string interpolation
- Unknown sort columns fall back to `created_at` (never raise 422 — degrade gracefully)
- Allowed: `name, created_at, price_eur, quantity, set_name, rarity, cmc`
- `NULLS LAST` always, regardless of direction — ensures consistent UX

### Frontend Column Mapping
- Frontend `price` column → API `sort_by=price_eur` (DB column name)
- Map is owned in Dashboard: `API_SORT_COLUMN = { price: 'price_eur' }`
- `type` column header click is not server-sortable — backend silently falls back

### Controlled Sort + Pagination Props
- Dashboard owns `page`, `sortBy`, `sortDir` state; passes as props to CardTable
- CardTable becomes fully controlled for sort/page — no local state for these
- `onSortChange(key, dir)` callback; `onPageChange(newPage)` callback
- Reset `page = 1` whenever filters or sort change

## Frontend Insights Component Patterns

### CollectionInsights (insight-history change, 2026-03-05)
- State changed from `activeResult: InsightResponseType | null` to `results: InsightResultEntry[]`
- `InsightResultEntry = {id, response, pinned, executedAt}` — defined inline in component file
- localStorage key `deckdex:pinned_insights` — JSON array of insight_id strings
- New results prepend (most recent first); auto-executed pinned insights append in mount effect
- `InsightResultCard` — module-level component (not a separate file), wraps InsightResponse with pin/dismiss chrome

### InsightResponse `hideQuestion` prop (added 2026-03-05)
- `frontend/src/components/insights/InsightResponse.tsx` accepts `hideQuestion?: boolean` (default false)
- When true: renders renderers in React fragment, no outer div/h3. Use when parent owns card chrome.

## Frontend Test Gotchas (card-gallery-view, 2026-03-07)

### localStorage in jsdom (vitest)
- jsdom's `localStorage` may NOT expose `clear()`/`removeItem()` as callable functions
- Use a manual mock via `Object.defineProperty(window, 'localStorage', { value: mockObj, writable: true })`
- Store state in a plain JS object, reset it in beforeEach/afterEach

### IntersectionObserver mock must be a regular function
- Arrow functions can't be `new`-ed — always use `function MockIO(callback) {...}`
- TDZ issue: if callback fires synchronously (common in mocks), don't reference the variable being assigned inside the callback
- Pattern: use a `ref` so `observerRef.current?.disconnect()` is safe as a null-safe call

### Module-level cache in hooks
- Don't use `vi.resetModules()` to reset module-level Maps — it breaks the mock chain
- Use unique numeric IDs per test to avoid cache pollution between tests

### `global` vs `globalThis` in test files
- `global` is not recognized in TypeScript's browser/jsdom environment
- Use `(globalThis as any).IntersectionObserver = ...` to set global mocks

### openspec archive
- Run from main repo root, not worktree
- Use `--skip-specs -y` when spec format doesn't use exact ADDED/MODIFIED/REMOVED/RENAMED sections
