# Spec Delta

## Purpose

Defines numeric interpretation of text EUR prices for PostgreSQL collection filters, sorting and quantity-weighted statistics.

## ADDED Requirements

### Requirement: Decimal-comma prices are numeric
PostgreSQL price queries SHALL normalize decimal commas to dots and interpret unsigned whole numbers or decimals with digits on both sides of the separator numerically. Other text and missing prices SHALL have a NULL numeric interpretation.

#### Scenario: Comma value
- **WHEN** price_eur is "0,08"
- **THEN** its numeric interpretation is 0.08

#### Scenario: Dot and integer values
- **WHEN** price_eur is "1.00" or "3"
- **THEN** its numeric interpretation is 1 or 3 respectively

#### Scenario: Junk value
- **WHEN** price_eur is "N/A", empty, "1.2.3", "-1", or "1."
- **THEN** its numeric interpretation is NULL

### Requirement: Price filters and sort are numeric
PostgreSQL minimum and maximum price bounds SHALL compare numeric price interpretations and accept comma-decimal bounds. Price sorting SHALL order numeric interpretations in the requested direction, placing NULL prices last and using card ID in the same direction to break ties.

#### Scenario: Bounds with comma
- **WHEN** price_min is "1,5" and price_max is "10"
- **THEN** numeric bounds of 1.5 and 10.0 are applied inclusively

#### Scenario: Sort by price
- **WHEN** sorting ascending over prices "10,00", "2,00" and "N/A"
- **THEN** the order is "2,00", "10,00", "N/A"

### Requirement: Price statistics interpret numeric text
PostgreSQL collection statistics SHALL use normalized numeric prices for quantity-weighted total value and average price. Non-numeric prices SHALL contribute no value or priced quantity to the average; total card quantity SHALL still include them. Empty numeric aggregates SHALL return zero, with returned total value and average rounded to two decimal places.

#### Scenario: Mixed valid and unavailable prices
- **WHEN** a filtered collection has two copies priced "0,08" and one copy priced "N/A"
- **THEN** total_cards is 3, total_value is 0.16 and average_price is 0.08
