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
