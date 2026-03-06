# Testing API Routes Exploration (2026-03-05)

## Endpoint Inventory by Route File

| Route File              | Prefix         | Endpoints | Tests Exist? | Test File(s)                                 |
|-------------------------|----------------|-----------|-------------|----------------------------------------------|
| `cards.py`              | `/api/cards`   | 9         | PARTIAL     | `test_api.py` (4), `test_api_extended.py` (2)|
| `decks.py`              | `/api/decks`   | 9         | YES         | `test_decks.py` (18)                         |
| `analytics.py`          | `/api/analytics` | 5       | PARTIAL     | `test_api_extended.py` (6)                   |
| `process.py`            | `/api`         | 7         | MINIMAL     | `test_api_extended.py` (2, jobs only)        |
| `import_routes.py`      | `/api/import`  | 5         | ZERO        | none                                         |
| `settings_routes.py`    | `/api/settings`| 4         | YES         | `test_external_apis_routes.py` (6)           |
| `catalog_routes.py`     | `/api/catalog` | 6         | YES         | `test_catalog_routes.py` (10)                |
| `auth.py`               | `/api/auth`    | 9         | ZERO        | none                                         |
| `admin_routes.py`       | `/api/admin`   | 2         | ZERO        | `test_admin.py` tests logic but NOT routes   |
| `insights.py`           | `/api/insights`| 3         | ZERO        | none                                         |
| `stats.py`              | `/api/stats`   | 1         | YES         | `test_api.py` (3)                            |
| `main.py` (app-level)   | `/api`         | 1         | YES         | `test_api.py` (2, health)                    |
| **TOTAL**               |                | **61**    |             |                                              |

## Detailed Coverage Gaps

### ZERO Coverage (28 endpoints)

1. **import_routes.py** (5 endpoints)
   - `POST /api/import/file` -- CSV/JSON file upload, replace collection
   - `POST /api/import/preview` -- parse and preview without DB write
   - `POST /api/import/resolve` -- resolve card names against catalog + Scryfall
   - `POST /api/import/external` -- async import with job tracking
   - `POST /api/import/external/cards` -- JSON body import with pre-resolved cards

2. **auth.py** (9 endpoints)
   - `GET /api/auth/google` -- OAuth redirect
   - `GET /api/auth/callback` -- OAuth callback
   - `GET /api/auth/exchange` -- token exchange
   - `GET /api/auth/me` -- current user
   - `PATCH /api/auth/profile` -- update profile
   - `POST /api/auth/refresh` -- refresh token
   - `POST /api/auth/logout` -- logout
   - `GET /api/auth/health` -- auth health
   - `GET /api/auth/avatar/{user_id}` -- user avatar

3. **insights.py** (3 endpoints)
   - `GET /api/insights/catalog` -- catalog-based insights
   - `GET /api/insights/suggestions` -- card suggestions
   - `POST /api/insights/{insight_id}` -- action on insight

4. **admin_routes.py** (2 endpoints, logic tested but not routes)
   - `POST /api/admin/catalog/sync` -- admin trigger catalog sync
   - `GET /api/admin/catalog/sync/status` -- admin sync status

5. **process.py** (5 of 7 endpoints untested)
   - `POST /api/process` -- trigger card processing job
   - `POST /api/prices/update` -- trigger bulk price update
   - `POST /api/prices/update/{card_id}` -- single card price update
   - `GET /api/jobs/{job_id}` -- get specific job status
   - `POST /api/jobs/{job_id}/cancel` -- cancel running job

### PARTIAL Coverage (4 endpoints missing)

6. **cards.py** (5 of 9 untested)
   - `GET /api/cards/suggest` -- card name suggestions
   - `GET /api/cards/resolve` -- resolve card by name
   - `GET /api/cards/{id}/image` -- card image proxy
   - `POST /api/cards/` -- add card to collection
   - `PUT /api/cards/{id}` -- update card
   - `PATCH /api/cards/{id}/quantity` -- update quantity
   - `DELETE /api/cards/{id}` -- delete card

7. **analytics.py** (3 of 5 untested)
   - `GET /api/analytics/color-identity` -- color identity distribution
   - `GET /api/analytics/cmc` -- mana curve distribution
   - `GET /api/analytics/type` -- type distribution

## Gold Standard Test Pattern Analysis

### `test_decks.py` (18 tests) -- Best Pattern
- **Style**: Pure pytest functions (no unittest.TestCase)
- **Fixtures**: module-scoped `deck_client` fixture yielding `(client, mock_repo)` tuple
- **Mocking**: Uses FastAPI dependency_overrides to inject `MagicMock(spec=DeckRepository)`
- **Coverage strategy**: Tests every endpoint with both success and failure (404) paths
- **Special**: Tests 501 when PostgreSQL unavailable
- **Why it works**: Clean, declarative, zero mock nesting, each test configures mock return for its scenario

### `test_external_apis_routes.py` (7 tests) -- Good but Older Style
- **Style**: unittest.TestCase with setUp/tearDown
- **Mocking**: Mix of dependency_overrides and `@patch` decorators
- **Coverage strategy**: Tests GET, PUT, validation errors, 503 fallback
- **Includes**: Regression test for CardFetcher bug (service-level, not route)

### Key difference: `test_decks.py` is the clear winner for new test patterns:
1. Uses pytest fixtures instead of setUp/tearDown
2. Uses dependency_overrides exclusively (no `@patch` on route internals)
3. Module-scoped client avoids repeated setup/teardown overhead
4. Each test is self-documenting via descriptive function names

## Prioritized Improvement Ideas

### Tier 1: Highest Impact/Effort Ratio

| # | Target                 | Endpoints | New Tests (est.) | Complexity | Impact/Effort | Rationale |
|---|------------------------|-----------|-----------------|------------|---------------|-----------|
| 1 | **import_routes.py**   | 5         | 15-20           | Medium     | **9/10**      | Most complex untested routes; file upload, async jobs, format detection, error paths. High regression risk. Already has helpers (_parse_file) that are easy to test. |
| 2 | **process.py**         | 5 untested| 12-15           | Medium     | **8/10**      | Core workflow (process cards, update prices, job lifecycle). Jobs tested only for list endpoint. Cancel + status are critical. |
| 3 | **cards.py** (gaps)    | 5 untested| 10-12           | Small      | **8/10**      | Existing test file + pattern makes it trivial to add missing CRUD endpoints (POST, PUT, PATCH, DELETE). Suggest + resolve are high-value. |

### Tier 2: Important but More Complex

| # | Target                 | Endpoints | New Tests (est.) | Complexity | Impact/Effort | Rationale |
|---|------------------------|-----------|-----------------|------------|---------------|-----------|
| 4 | **analytics.py** (gaps)| 3 untested| 9               | Small      | **7/10**      | Same pattern as rarity/sets tests. Color-identity, CMC, type tests are copy-paste with different data. |
| 5 | **insights.py**        | 3         | 8-10            | Medium     | **7/10**      | Requires understanding insight service + catalog integration. User-facing feature. |
| 6 | **admin_routes.py**    | 2         | 5-6             | Small      | **6/10**      | Logic already tested in test_admin.py; need route-level integration tests. Low endpoint count. |

### Tier 3: Important but Complex or Low-Priority

| # | Target                 | Endpoints | New Tests (est.) | Complexity | Impact/Effort | Rationale |
|---|------------------------|-----------|-----------------|------------|---------------|-----------|
| 7 | **auth.py**            | 9         | 20-25           | Large      | **5/10**      | OAuth flows are hard to test without real Google integration. Many external dependencies. However, /me, /health, /logout are trivial. |

## THE SINGLE HIGHEST-IMPACT IMPROVEMENT

### Write tests for `import_routes.py` (5 endpoints, 0 tests)

**Why this is #1:**

1. **Highest risk, zero coverage.** Import is the primary data ingestion path. Users upload CSVs from Moxfield, paste MTGO decklists, import from other apps. A regression here means data loss or corrupted collections. Zero tests means zero safety net.

2. **Complex business logic in routes.** Despite the "routes are thin" convention, `import_routes.py` contains:
   - File format detection and parsing (CSV, JSON, Moxfield, TappedOut, MTGO)
   - File size validation (10MB limit)
   - UTF-8 encoding validation
   - CSV header mapping with 20+ column aliases
   - Async background job creation with WebSocket progress callbacks
   - Card name resolution against catalog + Scryfall
   - Multiple mode handling (merge vs. replace)

3. **Many error paths that need verification:**
   - No file uploaded (400)
   - File too large (413)
   - Invalid encoding (400)
   - Invalid JSON (400)
   - Empty CSV (400)
   - No valid cards (400)
   - No Postgres (501)
   - Parse failure (400)

4. **Testability is good.** The routes use FastAPI dependencies (`get_collection_repo`, `get_current_user_id`, `get_job_repo`, etc.) which can be overridden. The pattern from `test_decks.py` applies directly. File upload testing via TestClient is well-supported.

5. **Estimated scope:** 15-20 tests covering:
   - `POST /file`: success CSV, success JSON, no file, empty file, too large, bad encoding, invalid JSON, empty CSV, no postgres (9 tests)
   - `POST /preview`: success file, success text, no input, parse failure (4 tests)
   - `POST /resolve`: success, no cards, catalog miss (3 tests)
   - `POST /external`: success async job, no postgres, no input (3 tests)
   - `POST /external/cards`: success, empty cards, no postgres (3 tests)

6. **Template approach:** Follow `test_decks.py` pattern exactly:
   - pytest functions, no unittest.TestCase
   - Module-scoped fixture providing `(client, mock_repo, mock_job_repo)`
   - dependency_overrides for all injected dependencies
   - Each test configures mocks for its specific scenario

## Dependencies and Prerequisites

- The `limiter` (slowapi rate limiter) on import routes needs to be handled in tests -- either disabled or mocked. This is a pattern not yet established in any test file and will need a reusable solution.
- File upload testing via TestClient requires building `UploadFile` objects -- standard but needs initial setup.
- The `_parse_file` helper imports from `deckdex.importers` which may need mocking to avoid testing parser logic in route tests.

## Cross-Reference with Previous Exploration

This builds on the testing exploration from 2026-03-05 which identified the same gaps. The key new insight here is the prioritization: import_routes beats process.py and auth.py because it has the worst risk/coverage ratio and the most testable error paths.
