# SQL Filtering Capability

SQL-level parameterized filtering and pagination for the Postgres collection repository.

## Overview

The `PostgresCollectionRepository` provides SQL-level filtering, aggregation, and pagination. Google Sheets users retain the existing Python in-memory path.

## Requirements

### Requirement: Filtered cards with total count
`get_cards_filtered(user_id, filters, limit, offset)` SHALL return `(List[Dict], int)` — the card list and the total count of matching cards (before LIMIT).

#### Scenario: Basic filtered query
- **GIVEN** a Postgres repository with 500 cards for user_id=1
- **WHEN** `get_cards_filtered(user_id=1, filters=CardFilters(rarity='rare'), limit=50, offset=0)` is called
- **THEN** returns `(cards, total)` where `len(cards) <= 50` and `total` equals the count of rare cards for user 1

#### Scenario: Pagination with offset
- **GIVEN** 200 cards matching the filter
- **WHEN** called with `limit=50, offset=50`
- **THEN** returns items 51-100 and `total=200`

#### Scenario: Search filter (case-insensitive)
- **WHEN** `filters.search = "lightning"` is provided
- **THEN** only cards whose name contains "lightning" (case-insensitive) are returned

### Requirement: Stats aggregation
`get_stats_aggregated(user_id, filters)` SHALL return a dict with `total_cards`, `total_value`, `average_price` computed via SQL aggregation (no row loading).

### Requirement: Analytics grouped
`get_analytics_grouped(user_id, filters, dimension)` SHALL return `List[Tuple[str, int]]` (label, count) sorted by count DESC, computed via SQL GROUP BY.

Supported dimensions: `rarity`, `color_identity`, `set_name`, `type_line`, `cmc`.

### Requirement: Filter options
`get_filter_options(user_id)` SHALL return `{'types': List[str], 'sets': List[str]}` — sorted distinct non-null values from `type_line` and `set_name` columns.

### Requirement: Parameterized queries only
All SQL queries SHALL use bound parameters (`:param` syntax). String interpolation into SQL is strictly forbidden.

### Requirement: Google Sheets fallback
When `CollectionRepository` is not a `PostgresCollectionRepository` (i.e., Google Sheets mode), all new methods SHALL fall back to the existing Python in-memory approach.
