# Tasks: InsightsService Unit Tests

## Task List

- [x] **TASK-1**: Create `tests/test_insights_service.py` with all unit tests
  - Import helpers: `_normalize_color_identity`, `_parse_price`, `_parse_date`
  - Import: `InsightsService`, `InsightsSuggestionEngine`, `INSIGHTS_CATALOG`
  - Define `SAMPLE_CARDS` fixture with R/U/B/G/W cards and varied price/date data
  - Implement all helper tests (REQ-1)
  - Implement execute dispatch tests (REQ-4)
  - Implement all 17 handler tests with non-empty and empty collections (REQ-2, REQ-3)
  - Implement `InsightsSuggestionEngine` tests (REQ-5)
