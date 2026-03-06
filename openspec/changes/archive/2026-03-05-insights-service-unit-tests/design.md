## Design: InsightsService Unit Tests

### Approach

Pure unit tests — no mocking required. `InsightsService` is a pure-computation
class that accepts `List[Dict[str, Any]]` and returns structured dicts. Tests
construct the service with controlled card fixtures and assert on outputs.

### File Structure

```
tests/
  test_insights_service.py   ← new file (all tests here)
```

### Test Organization

```
test_insights_service.py
  # Helper: _normalize_color_identity
  test_normalize_color_identity_none_returns_C
  test_normalize_color_identity_empty_string_returns_C
  test_normalize_color_identity_empty_list_literal_returns_C
  test_normalize_color_identity_single_letter
  test_normalize_color_identity_list_of_letters
  test_normalize_color_identity_comma_separated
  test_normalize_color_identity_list_string_with_quotes
  test_normalize_color_identity_full_color_name_blue
  test_normalize_color_identity_wubrg_ordering_preserved
  test_normalize_color_identity_invalid_returns_C

  # Helper: _parse_price
  test_parse_price_none_returns_none
  test_parse_price_empty_string_returns_none
  test_parse_price_float_string
  test_parse_price_integer
  test_parse_price_eu_decimal_comma
  test_parse_price_eu_thousands_and_decimal
  test_parse_price_us_thousands_separator
  test_parse_price_negative_returns_none
  test_parse_price_non_numeric_returns_none

  # Helper: _parse_date
  test_parse_date_none_returns_none
  test_parse_date_empty_string_returns_none
  test_parse_date_iso_full
  test_parse_date_iso_with_microseconds
  test_parse_date_date_only
  test_parse_date_space_separator
  test_parse_date_invalid_returns_none

  # InsightsService — execute dispatch
  test_execute_unknown_id_raises_value_error
  test_execute_returns_standard_envelope

  # Summary handlers
  test_total_value_empty_collection
  test_total_value_with_priced_cards
  test_total_value_partial_price_data
  test_total_cards_empty
  test_total_cards_nonzero
  test_avg_card_value_no_prices
  test_avg_card_value_single_card
  test_avg_card_value_multiple_cards

  # Distribution handlers
  test_by_color_counts_colors
  test_by_color_colorless_fallback
  test_by_rarity_counts_rarities
  test_by_set_top_sets
  test_value_by_color_distributes_value
  test_value_by_set_ranks_sets

  # Ranking handlers
  test_most_valuable_top10
  test_most_valuable_empty
  test_least_valuable_sorted_ascending
  test_most_collected_set_counts

  # Patterns handlers
  test_duplicates_no_dupes
  test_duplicates_with_dupes
  test_missing_colors_all_present
  test_missing_colors_some_missing
  test_no_price_all_priced
  test_no_price_some_unpriced
  test_singleton_sets_none
  test_singleton_sets_some

  # Activity handlers
  test_recent_additions_none_recent
  test_recent_additions_some_recent
  test_monthly_summary_no_dates
  test_monthly_summary_with_dates
  test_biggest_month_no_dates
  test_biggest_month_with_dates

  # InsightsSuggestionEngine
  test_suggestions_empty_collection
  test_suggestions_with_dupes_boosts_duplicates
  test_suggestions_recent_activity_boosts_recent_additions
  test_suggestions_missing_colors_boosts_missing_colors
  test_suggestions_large_collection_boosts_distribution
  test_suggestions_unpriced_cards_boosts_no_price
  test_suggestions_returns_at_most_limit
  test_suggestions_all_ids_valid
```

### Key Fixtures

```python
MINIMAL_CARDS = []  # empty collection

SAMPLE_CARDS = [
    {"id": 1, "name": "Lightning Bolt", "rarity": "common",
     "set_name": "M10", "price": "0.50", "color_identity": "R",
     "created_at": "2026-01-15T10:00:00"},
    {"id": 2, "name": "Counterspell", "rarity": "uncommon",
     "set_name": "M10", "price": "1.20", "color_identity": "U",
     "created_at": "2026-01-20T12:00:00"},
    {"id": 3, "name": "Dark Ritual", "rarity": "common",
     "set_name": "LEA", "price": "2.00", "color_identity": "B",
     "created_at": "2025-12-01T09:00:00"},
]
```

### Import Strategy

Import helpers directly from the module to test them in isolation:
```python
from backend.api.services.insights_service import (
    InsightsService,
    InsightsSuggestionEngine,
    _normalize_color_identity,
    _parse_price,
    _parse_date,
)
```
