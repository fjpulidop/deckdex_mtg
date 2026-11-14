# Spec Delta

## Purpose

Defines how the text `price_eur` column, stored with a decimal comma, is interpreted numerically in collection filters, sorting and statistics.

## ADDED Requirements

### Requirement: Decimal-comma prices are numeric
The system SHALL treat `price_eur` values with either a decimal comma or a dot as numbers, and values that are not well-formed non-negative decimals (such as "N/A") as NULL.

#### Scenario: Comma value
- **WHEN** price_eur is "0,08"
- **THEN** it is interpreted as 0.08

#### Scenario: Junk value
- **WHEN** price_eur is "N/A"
- **THEN** it is interpreted as NULL

### Requirement: Price filters and sort are numeric
Price min/max filters, sorting by price and price statistics SHALL use the numeric interpretation, and filter bounds SHALL accept a decimal comma.

#### Scenario: Bounds with comma
- **WHEN** price_min is "1,5" and price_max is "10"
- **THEN** the query binds 1.5 and 10.0 and applies the numeric expression to both

#### Scenario: Sort by price
- **WHEN** sorting by price descending
- **THEN** the query orders by the numeric expression, NULLs last
