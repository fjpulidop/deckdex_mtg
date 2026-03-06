# Spec: InsightsService Unit Tests

## Requirements

### REQ-1: Helper function coverage
All three private helpers MUST have unit tests covering:
- `_normalize_color_identity`: None, "", "[]", single letter, list of letters, comma-separated string, Python-list-repr string, full color names (e.g. "blue"→"U"), WUBRG ordering, and invalid input.
- `_parse_price`: None, "", valid float string, integer, EU decimal comma, EU thousands+decimal, US thousands separator, negative value, non-numeric string.
- `_parse_date`: None, "", ISO datetime with microseconds, ISO datetime without microseconds, space-separated datetime, date-only, invalid string.

### REQ-2: All 17 insight handlers tested
Each of the 17 insight IDs MUST have at least one test via `InsightsService.execute()`:
- Summary (3): `total_value`, `total_cards`, `avg_card_value`
- Distribution (5): `by_color`, `by_rarity`, `by_set`, `value_by_color`, `value_by_set`
- Ranking (3): `most_valuable`, `least_valuable`, `most_collected_set`
- Patterns (4): `duplicates`, `missing_colors`, `no_price`, `singleton_sets`
- Activity (3): `recent_additions`, `monthly_summary`, `biggest_month`

### REQ-3: Empty collection edge cases
Each insight handler MUST be tested with an empty card list to verify graceful handling (no exceptions, sensible answer_text).

### REQ-4: Execute dispatch
- `execute()` with unknown ID MUST raise `ValueError`.
- `execute()` MUST return dict with keys: `insight_id`, `question`, `answer_text`, `response_type`, `data`.

### REQ-5: InsightsSuggestionEngine coverage
- Empty collection returns non-empty suggestion list.
- Duplicates signal boosts `duplicates` insight.
- Recent activity signal boosts `recent_additions`.
- Missing colors signal boosts `missing_colors`.
- Large collection (>100 cards) boosts distribution insights.
- Unpriced cards boost `no_price`.
- Result length never exceeds requested limit.
- All returned IDs are valid insight IDs from the catalog.

### REQ-6: Test style
- pytest functions (NOT unittest.TestCase).
- No mocking needed (pure computation).
- Tests live in `tests/test_insights_service.py`.
