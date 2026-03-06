## Why

`InsightsService` (906 lines, 17 handlers) has zero test coverage. It is a
pure-computation module that takes `List[Dict]` as input and returns structured
results — ideal for fast, hermetic unit tests that need no database, no HTTP,
and no mocks. A regression in any handler would be invisible until runtime.

## What Changes

- Add `tests/test_insights_service.py` with comprehensive pytest unit tests.
- Cover all 17 insight handlers, 3 helper functions, and `InsightsSuggestionEngine`.

## Capabilities

### New Capabilities
- `insights-service-tests`: Unit test suite for `InsightsService` covering helpers,
  all 17 handlers, empty-collection edge cases, and the suggestion engine.

### Modified Capabilities
<!-- none — no spec-level requirement changes -->

## Impact

- New file: `tests/test_insights_service.py`
- No production code changes.
- No new dependencies (pytest already in use).

## Non-goals

- API-layer tests for `/api/insights` endpoints (separate concern).
- Integration tests against a real database or Scryfall.
- Frontend tests for the Insights UI.
