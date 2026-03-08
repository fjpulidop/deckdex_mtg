# Proposal: Import Test Coverage Gaps

## What and Why

The import routes test suite (`tests/test_import_routes.py`) covers 14 of 16 required deliverables from the `import-routes-tests` spec. Two gaps remain:

1. **Scryfall fallback cap validation**: `ResolveService` enforces a hard cap of 50 Scryfall lookups per resolve call (`SCRYFALL_LOOKUP_CAP = 50` in `backend/api/services/resolve_service.py`). This prevents runaway API usage when resolving large card lists. The cap logic is untested: no test verifies that cards beyond position 50 are not sent to Scryfall even when Scryfall is enabled and more than 50 unresolved cards exist in the input.

2. **Fixture scope violation**: The `import_client` fixture in `test_import_routes.py` (line 66) uses `scope="module"`. Every other fixture in the test suite — `conftest.py`, `test_decks.py`, `test_admin_routes.py`, `test_insights_routes.py`, `test_settings_scryfall_credentials_routes.py` — uses `scope="function"`. The project-wide convention (documented in MEMORY.md and confirmed by code review) is `scope="function"` to prevent cross-test pollution when mocked dependencies bleed state across tests.

## Product Motivation

Import correctness is a trust-critical feature. Users who paste 60+ card decklists expect all cards to resolve, but users should not be surprised by unbounded Scryfall API consumption. The 50-card cap is a documented policy boundary and must be tested so regressions are caught immediately.

Fixture scope correctness is a test-infrastructure concern. A module-scoped client with a mocked limiter and a shared `dependency_overrides` dict can cause state from one test to pollute the next, making failures non-deterministic and hard to debug — exactly the class of issue documented as a recurring pitfall in this project's memory.

## Scope

- **In scope**: Two new test functions in `tests/test_import_routes.py` plus changing the `import_client` fixture scope from `module` to `function`.
- **Out of scope**: Adding new production logic, changing `resolve_service.py`, adding new endpoints, or modifying any existing passing tests.

## Success Criteria

1. A test `test_import_resolve_scryfall_cap_not_exceeded` passes, asserting that when 55 unresolved cards are submitted with Scryfall enabled, the mock `fetcher.autocomplete` is called at most 50 times.
2. The `import_client` fixture uses `scope="function"`, matching every other fixture in the suite.
3. All existing 19 import route tests continue to pass.
4. `pytest tests/test_import_routes.py` exits 0 with no warnings about fixture scope.
