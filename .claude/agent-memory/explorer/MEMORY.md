# Explorer Agent - Memory

## Deck Builder Exploration (2026-03-05)
- Full exploration completed, see product-ideation-explorer/deck-builder-exploration.md
- Key finding: catalog_cards.legalities JSONB enables format validation without Scryfall API calls
- Key finding: deck_cards references collection cards only; wishlist needs separate approach
- Card picker has N+1 API call pattern (adds cards one at a time in loop)

## Testing Exploration (2026-03-05, updated)
- Full exploration completed, see product-ideation-explorer/testing-exploration.md
- API route deep-dive: see product-ideation-explorer/testing-api-routes-exploration.md
- 61 total API endpoints across 11 route files + 1 app-level
- Well tested: decks (18 tests), catalog (10), settings (6), stats (3), health (2)
- ZERO tests: import_routes (5 endpoints), auth (9), insights (3), admin routes (2), process (5 of 7)
- Partial: cards (4 of 9 tested), analytics (2 of 5 tested)
- Highest-impact improvement: test import_routes.py (highest risk, zero coverage, most complex untested file)
- Gold standard pattern: test_decks.py (pytest functions, module-scoped fixture, dependency_overrides)
- Blocker for import route tests: slowapi rate limiter needs mock/disable pattern (not yet established)

## Testing Core/Services Exploration (2026-03-05)
- Full exploration completed, see product-ideation-explorer/testing-core-services-exploration.md
- Highest-impact improvement: InsightsService unit tests (906 lines, zero coverage, pure computation, zero mocking needed)
- Key helpers also untested: _normalize_color_identity, _parse_price, _parse_date (all in insights_service.py)
- Importers (moxfield, mtgo, tappedout, generic_csv) + detect_format() all have ZERO tests but are small/pure
- Repository helpers (_card_to_row, _row_to_card, _safe_cmc) are pure functions with ZERO tests
- ResolveService is clean and testable (3-tier resolution: catalog exact -> catalog fuzzy -> scryfall)
- Services with heavy coupling (importer_service, processor_service) better suited for integration tests

## Collection Insights Exploration (2026-03-05)
- Full exploration completed, see product-ideation-explorer/collection-insights-exploration.md
- All 17 insights implemented with 5 animated response renderers
- Critical UX gap: only one result visible at a time
- Highest-impact: persist multiple results + pin favorites (medium effort)
- Significant overlap with Analytics page (color/rarity/set distributions duplicated)

## CI/CD Exploration (2026-03-06)
- Full exploration completed, see product-ideation-explorer/cicd-exploration.md
- ZERO CI/CD: no .github/, no pre-commit, no Python linter
- Python version mismatch: local 3.14 vs Docker 3.11 (risk)
- Top actions: create CI workflow, add ruff, pin Python 3.11, set coverage threshold, branch protection
- Migrations are raw SQL (not Alembic) -- CI needs Postgres service container
- Frontend Dockerfile runs dev server, not production build

## Pagination & Performance Exploration (2026-03-06)
- Full exploration completed, see product-ideation-explorer/pagination-exploration.md
- CRITICAL BUG: _collection_cache not keyed by user_id (data leaks between users)
- All paths load entire collection into memory; filter/aggregate in Python
- Dashboard uses limit=10000 (no pagination); no total_count in API response
- Analytics fires 6 parallel requests each re-filtering same dataset in Python
- No SQL-level filtering/pagination/aggregation in repository layer
- Recommended: fix cache -> SQL filtering -> SQL aggregation -> paginated response -> pagination UI
- Google Sheets path stays as-is; optimize Postgres only

## Accessibility Exploration (2026-03-06)
- Full exploration completed, see product-ideation-explorer/accessibility-exploration.md
- 37 component files + 7 page files reviewed
- Gold standard: ConfirmModal (dialog role, auto-focus, ESC) and CardFormModal (combobox ARIA)
- CRITICAL: 10+ modals missing role="dialog", aria-modal, aria-labelledby (only ConfirmModal has them)
- CRITICAL: No focus traps in any modal; zero aria-live regions in entire codebase
- CRITICAL: Only 1 of ~10 error displays uses role="alert"
- MAJOR: ~30 label/input pairs missing htmlFor/id associations
- MAJOR: Sortable table headers not keyboard-accessible, no aria-sort
- Recommendation: build reusable Modal wrapper component encapsulating all a11y patterns
- Quick wins (Tier 1): dialog roles, role="alert", aria-labels, label associations, aria-sort (~2hrs)
- ActionButtons.tsx has hardcoded English strings (bypasses i18n)

## Card Gallery View Exploration (2026-03-07, initial)
- See product-ideation-explorer/card-gallery-view-exploration.md (pre-implementation)

## Card Gallery Refinement Exploration (2026-03-07, post-implementation)
- See product-ideation-explorer/card-gallery-refinement-exploration.md
- MVP delivered: CardGallery.tsx, useImageCache.ts (useSyncExternalStore), Dashboard toggle, 10 tests
- CRITICAL gaps: no keyboard grid nav, no role="list" on container
- MAJOR gaps: gallery ignores sort props (no sort UI), ignores quantity props (no badge)
- MODERATE: ~60 lines toolbar+pagination duplicated between CardTable/CardGallery
- Top pick: sort controls (pill bar above grid, uses existing onSortChange prop)

## Price History Exploration (2026-03-07)
- Full exploration completed, see product-ideation-explorer/price-history-exploration.md
- PriceHistory entity defined in data-model spec but NEVER implemented (zero migrations, zero code)
- Price updates overwrite price_eur in-place -- all previous prices permanently lost
- PriceChart.tsx exists but is dead code (mock data, "Coming Soon", never imported anywhere)
- No charting library in frontend dependencies
- price_eur stored as TEXT throughout -- price_history table should use NUMERIC(10,2)
- Phase 1 (highest priority, lowest effort): create price_history table + INSERT on update + collection_value_snapshots
- Key insight: every day without Phase 1 is permanently lost price history data
- Differentiation: personal portfolio value tracking (none of Moxfield/Archidekt/EDHREC do this)

## Job Persistence Exploration (2026-03-07)
- Full exploration completed, see product-ideation-explorer/job-persistence-exploration.md
- Hybrid architecture: in-memory (_active_jobs, _job_results, _job_types module globals) + Postgres (jobs table)
- Jobs table exists (migration 008): id UUID, user_id, type, status, created_at, completed_at, result JSONB
- CRITICAL: GET /api/jobs/{job_id} only checks in-memory -- returns 404 after restart
- CRITICAL: No orphaned job cleanup -- 'running' rows persist forever after crash
- CRITICAL: Route ordering bug -- /api/jobs/history matched as /api/jobs/{job_id}
- BUG: Catalog sync uses raw SQL with wrong status values ('completed'/'failed' vs 'complete'/'error')
- BUG: Single-card price update NOT persisted to DB at all
- No progress or error log persistence -- in-memory only
- WebSocket validates against in-memory only -- rejects valid DB jobs after restart
- Top fixes: (1) orphaned job cleanup on startup, (2) route ordering, (3) normalize statuses, (4) DB fallback

## Theme Persistence & Consistency Exploration (2026-03-07)
- Full exploration completed, see product-ideation-explorer/theme-persistence-exploration.md
- BUG: Login.tsx has ZERO dark mode support (all hardcoded light classes)
- BUG: InsightComparisonRenderer uses @media (prefers-color-scheme: dark) instead of .dark class
- MISSING: No cross-tab sync (no StorageEvent listener in ThemeContext)
- Flash prevention in main.tsx (synchronous JS) works but not in index.html <head>
- 40 files use dark: variants -- good coverage overall, Login.tsx is the outlier
- Top pick: fix Login.tsx + InsightComparisonRenderer + add cross-tab sync (~2hrs total)

## Animated Backgrounds Performance Exploration (2026-03-07)
- Full exploration completed, see product-ideation-explorer/animated-backgrounds-exploration.md
- Two canvas components: AetherParticles (app pages, 50 particles) and CardMatrix (landing, ~40 drops)
- Well-built foundation: 30fps cap, DPR-aware, debounced resize, reduced-motion, proper cleanup
- CRITICAL: No Page Visibility API -- animation loops burn CPU in background tabs
- MAJOR: CardMatrix uses ctx.shadowBlur=8 in dark mode -- expensive Gaussian blur every frame per drop
- MAJOR: Theme toggle causes full effect re-run (flash); could use ref for isDark
- MINOR: No DPR change detection for multi-monitor; no user toggle to disable backgrounds
- Top pick: Page Visibility API pause (highest impact, smallest effort, ~30 min)

## Navigation UI Polish Exploration (2026-03-07)
- Full exploration completed, see product-ideation-explorer/navigation-ui-exploration.md
- BUG: LanguageSwitcher uses hardcoded slate colors (text-slate-300/text-white) -- invisible in light mode on main Navbar
- BUG: Mobile backdrop uses broken `top-[calc(100%+4rem)]` positioning
- MISSING: No mobile menu animation (instant show/hide)
- MISSING: No focus-visible rings; user dropdown missing role="menu"/aria-haspopup
- MISSING: No shared PageLayout wrapper (each page reinvents container classes)
- Import page has no navbar link (only reachable via Dashboard buttons)
- JobsBottomBar w-96 exceeds phone widths; not responsive
- Top pick: fix LanguageSwitcher colors (critical bug, ~15min)
- Best bundle: LanguageSwitcher fix + backdrop fix + hide lang switcher on mobile + focus-visible rings (~2hrs total)

## Card Image Storage Optimization Exploration (2026-03-07)
- Full exploration completed, see product-ideation-explorer/card-image-storage-exploration.md
- SECURITY: key validation rejects startswith("/") but NOT embedded "/" (spec says reject any "/")
- PERFORMANCE: zero HTTP cache headers on image responses (no Cache-Control, no ETag)
- PERFORMANCE: full file read_bytes() into Python memory per request; should use FileResponse (already used in auth.py)
- PERFORMANCE: no batch image endpoint; gallery triggers N individual HTTP requests
- PERFORMANCE: frontend cache keyed by card.id not scryfall_id (same image fetched multiple times across views)
- BUG: put() error handler has potential fd leak (os.get_inheritable on closed fd)
- MISSING: no disk space management, no LRU eviction, no multi-size image support
- Top pick: Cache-Control immutable + FileResponse + fix "/" key validation (~1hr combined, highest impact/effort)
