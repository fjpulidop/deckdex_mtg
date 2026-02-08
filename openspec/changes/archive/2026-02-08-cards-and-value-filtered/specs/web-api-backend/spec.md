## MODIFIED Requirements

### Requirement: Backend SHALL provide collection statistics endpoint

The system SHALL calculate and return aggregate statistics about the collection with robust price parsing that handles multiple European and US number formats. GET `/api/stats` SHALL accept optional query parameters that filter the collection before aggregation: `search` (name contains, case-insensitive), `rarity`, `type`, `set_name` (exact match), `price_min`, `price_max` (numeric, inclusive). When any of these parameters are provided, the system SHALL return total_cards, total_value, and average_price for the subset of the collection matching those filters only. When no filter parameters are provided, the system SHALL return aggregates for the entire collection. The stats cache SHALL be keyed by the set of filter parameters so that unfiltered and each distinct filtered request have separate cache entries (e.g. 30s TTL per entry).

#### Scenario: Get collection summary statistics
- **WHEN** client sends GET request to `/api/stats`
- **THEN** system returns JSON with total_cards, total_value, average_price, last_updated timestamp

#### Scenario: Get stats for filtered collection
- **WHEN** client sends GET request to `/api/stats` with one or more of search, rarity, type, set_name, price_min, price_max
- **THEN** system filters the collection by those criteria (same semantics as dashboard: name contains search, exact match for rarity/type/set_name, price in [price_min, price_max]) and returns total_cards, total_value, average_price, last_updated for the filtered subset only

#### Scenario: Statistics cached to avoid excessive Sheets API calls
- **WHEN** client requests stats within 30 seconds of previous request with the same set of filter parameters
- **THEN** system returns cached statistics for that filter combination without recomputing

#### Scenario: Cache key includes filter parameters
- **WHEN** client requests stats with filter params A and later with different filter params B (or no params)
- **THEN** system does not return the cached result from A for request B; each distinct filter combination has its own cache entry

#### Scenario: Parse European price format with thousands separator
- **WHEN** Google Sheets returns price as "1.234,56" (European format with thousands separator)
- **THEN** system correctly parses it as 1234.56 and includes it in total_value calculation

#### Scenario: Parse European price format without thousands separator
- **WHEN** Google Sheets returns price as "123,45" (European format without thousands separator)
- **THEN** system correctly parses it as 123.45 and includes it in total_value calculation

#### Scenario: Parse US price format with thousands separator
- **WHEN** Google Sheets returns price as "1,234.56" (US format with comma thousands separator)
- **THEN** system correctly parses it as 1234.56 and includes it in total_value calculation

#### Scenario: Skip invalid price formats gracefully
- **WHEN** price value cannot be parsed as a number
- **THEN** system logs the error and excludes that card from total_value but continues processing remaining cards

#### Scenario: Skip N/A prices
- **WHEN** card has price value "N/A"
- **THEN** system excludes that card from total_value and average_price calculations
