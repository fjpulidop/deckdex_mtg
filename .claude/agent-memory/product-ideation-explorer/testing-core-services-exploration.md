# Testing Core/Services Exploration (2026-03-05)

## Scope

Deep investigation of testing gaps in:
- `deckdex/importers/` -- 5 parsers + format detection
- `backend/api/services/` -- 6 services
- `deckdex/storage/` -- 4 repositories
- Helper functions in `deckdex/storage/repository.py` (`_card_to_row`, `_row_to_card`, `_safe_cmc`, etc.)

## Existing Test Coverage

| Module | Tests? | Notes |
|--------|--------|-------|
| `importers/deck_text.py` | YES (12 tests) | Well-tested, good pattern to follow |
| `importers/moxfield.py` | ZERO | 25 lines, CSV parser |
| `importers/mtgo.py` | ZERO | 26 lines, regex parser |
| `importers/tappedout.py` | ZERO | 25 lines, CSV parser |
| `importers/generic_csv.py` | ZERO | 62 lines, column auto-detection |
| `importers/base.py` (detect_format) | ZERO | 45 lines, format detection |
| `services/insights_service.py` | ZERO | 906 lines, 17 insights + suggestion engine |
| `services/resolve_service.py` | ZERO | 89 lines, card resolution |
| `services/importer_service.py` | ZERO | 211 lines, heavy DB/async coupling |
| `services/processor_service.py` | ZERO | 455 lines, heavy threading/IO coupling |
| `services/scryfall_service.py` | ZERO | 166 lines, catalog-first resolution |
| `services/catalog_service.py` | ZERO | 202 lines, thin delegation layer |
| `storage/repository.py` helpers | ZERO | `_card_to_row`, `_row_to_card`, `_safe_cmc`, `_is_incomplete_card` |
| `storage/deck_repository.py` | PARTIAL | Only `find_card_ids_by_names` (8 tests) |
| `storage/job_repository.py` | ZERO | 103 lines, thin SQL |
| `storage/user_settings_repository.py` | ZERO | 78 lines, thin SQL |

## Analysis: Complexity vs. Coverage Matrix

### HIGH complexity, ZERO coverage (critical gaps)

1. **`insights_service.py`** (906 lines) -- The single biggest untested module
   - 17 insight handlers, each with non-trivial data transformation
   - `_normalize_color_identity()` -- complex parser handling lists, strings, WUBRG, comma-separated, bracket-wrapped
   - `_parse_price()` -- European/US number format handling with comma/dot ambiguity
   - `_parse_date()` -- multiple format fallbacks
   - `InsightsSuggestionEngine` -- weighted scoring based on collection signals
   - ALL are pure functions or take simple `List[Dict]` input -- highly testable with zero mocking

2. **`generic_csv.py`** (62 lines) -- Most complex importer
   - Auto-detection of name/qty/set columns from varied headers
   - Fallback logic (contains "name" -> first column)
   - Edge cases: missing columns, empty rows, bad qty values

3. **`importers/base.py` `detect_format()`** (45 lines) -- Format routing
   - Drives which parser gets called -- bug here = wrong parser for entire import
   - Header inspection logic for Moxfield vs TappedOut vs generic

### MEDIUM complexity, ZERO coverage

4. **`resolve_service.py`** (89 lines) -- Clean, testable
   - 3-tier resolution: exact catalog -> fuzzy catalog -> Scryfall autocomplete
   - Scryfall lookup cap (50 max)
   - Status transitions: matched / suggested / not_found
   - Requires mocking catalog_repo and card_fetcher (simple interfaces)

5. **`repository.py` helper functions** -- Data mapping layer
   - `_card_to_row()` / `_row_to_card()` -- bidirectional field mapping with renames (type<->type_line, price<->price_eur, number<->set_number)
   - `_safe_cmc()` -- handles NaN, "N/A", comma decimals
   - `_is_incomplete_card()` -- determines if card needs enrichment
   - Pure functions, zero mocking needed

6. **`scryfall_service.py`** (166 lines) -- Catalog-first with Scryfall fallback
   - `suggest_card_names()` and `resolve_card_by_name()`
   - `_map_catalog_card()` -- pure mapping function
   - Needs mocking of dependencies (catalog_repo, user_settings_repo, CardFetcher)

### LOW testability (high coupling, lower priority)

7. **`importer_service.py`** -- Tightly coupled to DB, async, threads
   - `_run_import()` does raw SQL, uses internal `_card_to_row`, accesses global deps
   - Would need significant mocking or refactoring
   - Better tested via integration tests with TestClient

8. **`processor_service.py`** -- Threading, stderr interception, tqdm parsing
   - `ProgressCapture` is testable (regex parsing)
   - Full service needs MagicCardProcessor mock + event loop
   - Better tested via integration tests

9. **`catalog_service.py`** -- Mostly thin delegation
   - `search()`, `autocomplete()`, `get_card()` are one-liners
   - `start_sync()` is complex but mostly threading/coordination
   - Low value to unit test the thin wrappers

## Prioritized Improvement Ideas

### #1 WINNER: InsightsService Unit Tests
**Impact/Effort: 10/10**

Why this is the single highest-impact improvement:
- **906 lines of untested business logic** -- largest untested module by far
- **100% pure computation** -- no DB, no network, no async, no mocking needed
- **High bug surface** -- `_normalize_color_identity()` handles 8+ input formats; `_parse_price()` handles European number formatting; median calculation, percentage math, date parsing
- **Real user-facing value** -- insights drive the analytics dashboard; bugs here = wrong numbers shown to users
- **Fast to write** -- pass `List[Dict]` in, assert result dict out; pattern exists in `test_deck_text_parser.py`
- **17 independent handlers** -- each is a focused test target with clear inputs/outputs

Key test scenarios:
- `_normalize_color_identity()`: None, empty string, "[]", single letter "R", list ["R","G"], comma-separated "R,G", bracket-wrapped "['R', 'G']", word format "blue", mixed case, invalid values
- `_parse_price()`: None, empty, "1.50", "1,50" (EU), "1.234,56" (EU thousands), "1,234.56" (US thousands), negative, zero, non-numeric
- `_parse_date()`: ISO with/without microseconds, date-only, invalid strings, None
- Each insight handler: empty collection, single card, cards with/without prices, cards with/without dates, cards with various rarities/colors/sets
- `InsightsSuggestionEngine`: empty collection, large collection, recent activity boost, duplicates boost, missing colors boost
- Edge cases: division by zero in percentages, empty price lists for avg/median

Estimated effort: **Medium** (1-2 sessions, ~200-300 lines of tests)

### #2: Importers + detect_format Tests
**Impact/Effort: 9/10**

Why:
- All 4 remaining importers + `detect_format()` have ZERO tests
- Importers are pure functions (string in -> list of ParsedCard out)
- `detect_format()` is the routing brain -- if it misclassifies, the entire import fails silently
- Small files (25-62 lines each) = fast to test comprehensively
- Real-world CSV variations are common (users export from different tools)

Key test scenarios:
- `detect_format()`: .txt -> mtgo, CSV with Count/Name/Edition -> moxfield, CSV with Qty/Name/Set -> tappedout, unknown CSV -> generic, empty content, no filename
- `moxfield.parse()`: standard CSV, missing Name rows skipped, Count as float "2.0", missing Edition -> None, empty content
- `mtgo.parse()`: standard "4 Lightning Bolt", comment lines skipped, blank lines, zero quantity -> 1, cards with commas
- `tappedout.parse()`: standard CSV, similar edge cases as moxfield
- `generic_csv.parse()`: auto-detect "card name" column, "amount" qty column, fallback to first column, no headers, empty rows, partial rows

Estimated effort: **Small** (1 session, ~100-150 lines of tests)

### #3: Repository Helper Function Tests
**Impact/Effort: 8/10**

Why:
- `_card_to_row()` and `_row_to_card()` are the data boundary between API and DB
- Field mapping bugs here cause silent data loss (e.g., "price" -> "price_eur" rename)
- `_safe_cmc()` handles numeric edge cases (NaN, "N/A", comma decimals)
- All pure functions, zero mocking
- Used by every card operation in the system

Key test scenarios:
- `_card_to_row()`: full card dict, minimal card, None values stripped, type->type_line mapping, price->price_eur mapping, number->set_number mapping, cmc normalization
- `_row_to_card()`: reverse mapping, created_at serialization, quantity default to 1, None-stripping (keeps id and quantity)
- `_safe_cmc()`: int, float, NaN, "N/A", "3,5" (comma decimal), "", None, invalid string
- `_is_incomplete_card()`: card with type_line (complete), card without (incomplete), card with empty type_line

Estimated effort: **Small** (1 session, ~80-120 lines of tests)

### #4: ResolveService Tests
**Impact/Effort: 7/10**

Why:
- Clean 3-tier resolution logic with clear states (matched/suggested/not_found)
- Scryfall lookup cap (50) is a correctness-critical feature
- Simple interface to mock (catalog_repo.search_by_name, fetcher.autocomplete)
- New service, likely to evolve -- tests prevent regressions

Key test scenarios:
- Exact catalog match -> status "matched"
- Fuzzy catalog matches -> status "suggested" with top 3
- No catalog, Scryfall exact match -> status "matched"
- No catalog, Scryfall suggestions -> status "suggested"
- No match anywhere -> status "not_found"
- Scryfall disabled -> skip even if catalog misses
- Scryfall cap reached (51st card) -> no more API calls
- Catalog exception -> graceful fallback to Scryfall
- Scryfall exception -> graceful fallback to not_found
- Empty parsed_cards list -> empty results

Estimated effort: **Small** (1 session, ~100-130 lines of tests)

### #5: ScryallService `_map_catalog_card` + suggest/resolve Tests
**Impact/Effort: 6/10**

Why:
- `_map_catalog_card()` is a pure mapping function (easy to test)
- `suggest_card_names()` and `resolve_card_by_name()` have catalog-first-then-Scryfall logic
- Needs mocking of `get_catalog_repo()`, `get_user_settings_repo()`, `CardFetcher`
- More mocking overhead than insights/importers

Key test scenarios:
- `_map_catalog_card()`: maps type_line->type, price_usd->price, oracle_text->description
- `suggest_card_names()`: query too short (<2 chars) -> empty, catalog hit -> return, catalog empty + scryfall enabled -> fallback, scryfall disabled -> empty
- `resolve_card_by_name()`: from_collection match, catalog match, scryfall fallback with price/color mapping, empty name -> CardNotFoundError

Estimated effort: **Medium** (1 session, ~120-160 lines of tests)

### #6: ProgressCapture Tests (processor_service.py)
**Impact/Effort: 5/10**

Why:
- `ProgressCapture` class is isolated and testable despite being in a complex service
- Regex parsing of tqdm output is fragile -- worth testing
- Cancellation logic via `cancel_event` is critical for UX

Key test scenarios:
- Write text matching tqdm pattern -> callback invoked with correct current/total/percentage
- Write non-matching text -> no callback
- Buffer management (>4096 chars truncated)
- Cancel event set -> raises JobCancelledException on write()
- Cancel event set -> raises JobCancelledException on flush()

Estimated effort: **Small** (~40-60 lines of tests)

## Recommendation

**Start with #1 (InsightsService)** as the single highest-impact improvement.

Rationale:
1. It is the largest untested module (906 lines) with the most complex pure logic
2. It requires ZERO mocking -- just construct `InsightsService(cards=[...])` and call `.execute("insight_id")`
3. The helper functions (`_normalize_color_identity`, `_parse_price`, `_parse_date`) have the most edge cases and are most likely to contain or attract bugs
4. It directly powers the analytics dashboard -- user-visible impact
5. Test patterns from `test_deck_text_parser.py` transfer directly

After InsightsService, the next batch should be #2 (importers) + #3 (repository helpers) as they are both small-effort, high-value, zero-mocking targets that can be done together in a single session.

## Architectural Observations

- **Services with heavy coupling** (importer_service, processor_service) would benefit from refactoring to extract testable logic. For example, `_run_import()` does both enrichment and SQL -- separating enrichment into a pure function would make it testable.
- **Repository tests** for the SQL-executing methods (not the helpers) are better done as integration tests with a real DB or SQLite. The mock-heavy approach in `test_deck_repository.py` is fragile.
- The conftest.py pattern with `SAMPLE_CARDS` could be extended with card fixtures that include the fields insights_service needs (color_identity, price, created_at, rarity, set_name).
