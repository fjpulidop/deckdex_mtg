# Delta spec — API Tests (api-test-coverage-gaps)

Base spec: `openspec/specs/api-tests/spec.md`

This delta adds requirements that were missing from the base spec and documents the fixture scoping rule that must be enforced across all API test files.

---

## Addition: Fixture scoping requirement

All pytest fixtures in `tests/` that set `app.dependency_overrides` MUST use `scope="function"`.
All `unittest.TestCase` classes in `tests/` that set `app.dependency_overrides` MUST do so in `setUpClass`/`tearDownClass` (class-scoped), NOT at module level.

Module-level override installation (e.g. `app.dependency_overrides[dep] = ...` at the top of a test file) is **prohibited** because it permanently mutates the shared `app` singleton and causes cross-test pollution when pytest collects multiple test files in the same process.

### Fixture teardown rule

Every fixture or `tearDownClass` that adds a key to `app.dependency_overrides` MUST remove it using `app.dependency_overrides.pop(key, None)` — never `app.dependency_overrides.clear()`, which would destroy overrides set by other modules.

---

## Addition: Stats endpoint — additional filtering scenarios

### Scenario: Stats with set_name filter returns filtered subset

- WHEN `GET /api/stats/?set_name=LEA` is called with collection containing M10 and LEA cards
- THEN response is 200 with `total_cards` reflecting only LEA cards and `total_value` reflecting only their prices

### Scenario: Stats with search filter returns name-matched subset

- WHEN `GET /api/stats/?search=bolt` is called with collection containing "Lightning Bolt" and other cards
- THEN response is 200 with `total_cards=1` (only Lightning Bolt matches)

### Scenario: Stats with multi-filter (rarity + set_name) returns intersection

- WHEN `GET /api/stats/?rarity=common&set_name=M10` is called with the standard 3-card fixture
- THEN response is 200 with `total_cards=2` (Lightning Bolt and Counterspell match both filters)

---

## Addition: Cards list endpoint — additional filtering and sort scenarios

### Scenario: Cards list with rarity filter returns only matching cards

- WHEN `GET /api/cards/?rarity=mythic+rare` is called with the standard 3-card fixture
- THEN response is 200, `items` contains exactly 1 card (Black Lotus), `total=1`

### Scenario: Cards list with search filter returns name-matched cards

- WHEN `GET /api/cards/?search=bolt` is called with the standard 3-card fixture
- THEN response is 200, `items` contains exactly 1 card (Lightning Bolt), `total=1`

### Scenario: Cards list with unknown sort_by does not error

- WHEN `GET /api/cards/?sort_by=invalid_column` is called
- THEN response is 200 (route silently falls back to `created_at`)

### Scenario: Cards list with invalid sort_dir does not error

- WHEN `GET /api/cards/?sort_dir=sideways` is called
- THEN response is 200 (route silently falls back to `desc`)

---

## Pre-existing requirements confirmed complete (no changes needed)

- Health endpoint: covered by `TestHealth` in `tests/test_api.py`
- Deck CRUD + 404 scenarios: covered by `tests/test_decks.py` (27 tests, `scope="function"` fixture)
- Deck card management: covered by `tests/test_decks.py`
- 501 when PostgreSQL unavailable: covered by `test_501_when_no_postgres` in `tests/test_decks.py`
