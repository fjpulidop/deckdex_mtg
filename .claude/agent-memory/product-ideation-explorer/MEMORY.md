# Product Ideation Explorer - Memory

## Deck Builder Current State (explored 2026-03-05)
- See `deck-builder-exploration.md` for full analysis
- Grid of deck tiles with commander backgrounds, DeckDetailModal, DeckCardPickerModal
- Backend: full CRUD, PostgreSQL-only, deck_cards with (deck_id, card_id, quantity, is_commander)
- No format field on decks table, no description/notes field
- catalog_cards table has `legalities JSONB` -- key for format validation
- cards table has color_identity -- key for Commander color restrictions
- Card picker only pulls from user's collection (cards table), limit 200
- No import/export, no deck copy, no statistics beyond mana curve + total price

## Analytics State (explored 2026-03-05)
- See `analytics-exploration.md` for full findings
- 4 KPIs + 4 charts with cross-chart drill-down, Recharts library
- Insights service (17 insights) fully implemented in backend but NOT surfaced in analytics UI
- Insights API routes wired and functional
- Key gaps: no type_line analytics, no price distribution, no value-based views, no deck-aware analytics, no comparative views

## Testing Landscape (explored 2026-03-05)
- See `testing-exploration.md` for full analysis
- 16 backend test files, ~2700 lines, nearly all unittest.TestCase style
- 2 frontend test files exist (CardTable, Filters) -- Vitest + Testing Library already configured
- No E2E tests, no CI/CD pipeline (no .github/workflows/)
- Major untested backend: decks CRUD (8 endpoints), import routes (5 endpoints), process routes (6 endpoints), insights (3 endpoints), WebSocket, filters module
- SAMPLE_CARDS duplicated in 3 files instead of using conftest.py
- test_admin.py and test_external_apis_settings.py use inline reimplementation of logic instead of testing actual code
- pyproject.toml has proper pytest config with markers (slow, integration) and coverage config
- Frontend: vitest.config.ts exists, jsdom env, setupFiles, __tests__ convention

## Collection Insights State (explored 2026-03-05)
- See `collection-insights-exploration.md` for full analysis
- All 17 insights fully implemented (backend + frontend renderers)
- 5 response types with polished animations: value (count-up), distribution (animated bars), list (thumbnails), comparison (WUBRG symbols), timeline
- Suggestion engine with 7 collection signals working
- Lives on Dashboard page only, NOT on Analytics page
- CRITICAL UX GAP: only one insight result visible at a time (new replaces old)
- Highest-impact improvement: persist multiple results + pin favorites (medium effort, huge UX win)
- Overlap with Analytics: by_color, by_rarity, by_set, total_value/total_cards duplicated
- Tech debt: no Pydantic response models, duplicated _normalize_color_identity, hardcoded EUR + es-ES locale

## Pagination & Performance Exploration (2026-03-06)
- See `pagination-exploration.md` for full analysis
- CRITICAL BUG: _collection_cache is global, not keyed by user_id -- data leaks between users
- All data paths load entire collection into memory, filter/aggregate in Python
- Dashboard requests limit=10000, no pagination UI, no server-side total count
- Analytics fires 6 parallel requests (5 analytics + 1 stats), each re-filtering same dataset
- No SQL-level filtering, pagination, or aggregation exists in repository
- Cards API returns flat array (no total count) -- blocking issue for pagination UI
- Recommended order: fix cache bug -> SQL filtering -> SQL stats/analytics -> paginated response -> pagination UI
- Google Sheets path can stay as-is (small collections); optimize Postgres path only

## CI/CD Exploration (2026-03-06)
- See `cicd-exploration.md` for full analysis
- ZERO CI/CD exists: no .github/workflows/, no pre-commit hooks, no Python linter
- Python version mismatch: local 3.14.3 vs Docker 3.11-slim (risk!)
- Backend: 20 pytest test files, coverage configured but fail_under=0
- Frontend: 4 vitest test files, ESLint 9 flat config, Playwright configured but zero E2E tests
- Frontend Dockerfile runs dev server (NOT production build)
- Top 5 actions: (1) create CI workflow, (2) add ruff, (3) pin Python 3.11, (4) set coverage threshold, (5) branch protection
- DB migrations are raw SQL files, not Alembic -- CI needs Postgres service container

## Card Gallery View Exploration (2026-03-07)
- See `card-gallery-view-exploration.md` for full analysis
- ZERO gallery/grid view exists -- only CardTable (table layout)
- Image infra: per-card API endpoint, filesystem ImageStore (scryfall_id key), useCardImage hook (Blob URLs, no client cache)
- Key bottleneck: 50 cards/page = 50 individual image API calls with no caching between mounts
- Top priority: client-side blob cache -> view toggle -> CardGallery component -> lazy loading -> skeletons
- Architecture recommendation: Dashboard owns toggle, renders CardTable OR CardGallery (Option B -- shared props interface)
- Competitive gap: Moxfield/Archidekt both default to gallery; DeckDex table-only is a significant UX gap
- Auth consideration: images served via cookie auth; Blob URL approach needed (plain img src won't send cookies)

## Key Architectural Insights
- Decks only reference cards in collection (cards table) -- cannot add cards user doesn't own
- catalog_cards (Scryfall bulk data) exists with legalities, could power format validation and wishlist features
- No deck format/description columns yet -- schema migration needed for format support
- Card picker adds cards one-by-one via sequential API calls (N+1 pattern)
- Cards table has: type_line, keywords, power, toughness, edhrec_rank, release_date, game_strategy, tier -- many unused in analytics
- Cache is per-process in-memory dicts with 30s TTL, no invalidation on data mutation

## Job Persistence Exploration (2026-03-07)
- See `job-persistence-exploration.md` for full analysis
- Hybrid in-memory + Postgres jobs system; DB table exists but underused
- 3 critical bugs: GET /jobs/{id} ignores DB, no orphan cleanup on startup, route ordering (/history vs /{job_id})
- Catalog sync uses raw SQL + wrong status values; single-card price update not persisted at all
- No progress/error persistence; no job cleanup policy; jobs table grows unbounded
- WebSocket endpoint only validates in-memory -- fails after restart for valid DB jobs
- 13 improvement ideas ranked; top 4 are trivial fixes (< 1hr each, high impact)
- Key insight: hybrid approach is fine for localhost single-server; gaps are in restart recovery and data consistency
