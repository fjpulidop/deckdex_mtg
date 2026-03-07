# Explorer Agent - Memory

## Decks Exploration (2026-03-07, replaces 2026-03-05)
- Full exploration: product-ideation-explorer/decks-exploration.md
- ALL 9 endpoints + ALL frontend components implemented per spec
- 19 route tests; import endpoint has ZERO tests (biggest gap)
- N+1 bug in card picker; hardcoded EUR currency
- Key differentiator: decks reference YOUR collection
- Top opportunity: cross-deck card overlap detection

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

## Price History Exploration (2026-03-07, updated)
- Full exploration completed, see product-ideation-explorer/price-history-exploration.md
- NOW IMPLEMENTED: migration 014_price_history.sql, repository methods, processor INSERT, PriceChart.tsx (real LineChart)
- PriceChart rendered inside CardDetailModal (per-card view)
- STILL MISSING: collection_value_snapshots (daily aggregate), value-over-time chart on Analytics page
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

## Analytics & Prices Exploration (2026-03-07, updated)
- Full exploration completed, see product-ideation-explorer/analytics-exploration.md
- 5 analytics endpoints (rarity, color-identity, cmc, sets, type) + stats + price-history -- ALL implemented
- 7 frontend chart components (modular, reusable) + KpiCards with animated count-up -- ALL implemented
- Drill-down system fully working: 5 dimensions, removable chips, cross-filtering
- BUG: /api/analytics/type accesses repo private methods (_build_filter_clauses, _get_engine) from route layer
- GAPS: 3/5 analytics endpoints have zero tests; all tests only exercise Sheets path, never Postgres SQL
- MISSING: no value-weighted charts (value by color/rarity), no collection value over time, no deck analytics
- MISSING: no format legality breakdown (catalog_cards.legalities exists but unused in analytics)
- OVERLAP: Insights by_color/by_rarity/by_set duplicate Analytics charts with no cross-linking
- Top picks: (1) fix type endpoint repo violation, (2) add missing tests, (3) value distribution chart
- Competitive advantage: interactive collection-level drill-down analytics is genuinely novel vs Moxfield/EDHREC/Archidekt

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

## User Profile & Avatar Crop Exploration (2026-03-07)
- Full exploration completed, see product-ideation-explorer/user-profile-exploration.md
- CRITICAL BUG: avatar upload completely broken -- _validate_avatar_url() rejects data: URIs but ProfileModal sends base64
- MODERATE BUG: ProfileModal uses raw fetch() instead of api/client.ts (zero profile methods in client)
- Auth system well-implemented: OAuth, JWT blacklist, avatar proxy, admin bootstrap, 40+ tests
- ProfileModal has react-easy-crop (installed, working UI) but backend blocks the crop result
- No avatar cache invalidation after profile update
- No display name length validation
- Top fix: allow data: URIs in _validate_avatar_url (~30min, unblocks entire feature)
