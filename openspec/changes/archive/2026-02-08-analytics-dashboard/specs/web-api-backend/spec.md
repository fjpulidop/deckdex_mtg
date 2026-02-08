## ADDED Requirements

### Requirement: Backend SHALL provide analytics aggregation endpoints

The system SHALL expose HTTP endpoints that return aggregated data for the analytics dashboard. Endpoints SHALL accept the same optional filter query parameters as GET `/api/stats`: `search`, `rarity`, `type`, `set_name`, `price_min`, `price_max`. When provided, aggregation SHALL be computed over the filtered subset of the collection only. Responses SHALL be JSON structures suitable for direct use by charts (e.g. lists of { key, count } or { bucket, value }). At least the following aggregations SHALL be available: by rarity, by color identity, by CMC (converted mana cost), and by set (with support for top-N or limit). Implementation SHALL use efficient queries (e.g. SQL GROUP BY) over the backing store (PostgreSQL when configured).

#### Scenario: Get aggregation by rarity
- **WHEN** client sends GET request to the analytics rarity endpoint (e.g. GET `/api/analytics/rarity`) with optional search, rarity, type, set_name, price_min, price_max
- **THEN** system returns JSON array of { rarity, count } (or equivalent) for the filtered collection; counts SHALL match the number of cards in each rarity in that subset

#### Scenario: Get aggregation by color identity
- **WHEN** client sends GET request to the analytics color-identity endpoint (e.g. GET `/api/analytics/color-identity`) with optional filter parameters
- **THEN** system returns JSON array of { color_identity, count } (or equivalent) for the filtered collection; color identity MAY be normalized (e.g. "W", "U", "WU", "C" for colorless) as defined by the API contract

#### Scenario: Get aggregation by CMC
- **WHEN** client sends GET request to the analytics CMC endpoint (e.g. GET `/api/analytics/cmc`) with optional filter parameters
- **THEN** system returns JSON array of { cmc, count } (or bucketed, e.g. "7+") for the filtered collection; CMC SHALL be derived from the card model (numeric or bucketed)

#### Scenario: Get aggregation by set (top N)
- **WHEN** client sends GET request to the analytics set endpoint (e.g. GET `/api/analytics/sets`) with optional filter parameters and optional limit (e.g. top 10)
- **THEN** system returns JSON array of { set_name, count } (or equivalent) ordered by count descending, limited to the requested N, for the filtered collection

#### Scenario: Filter parameters apply to all analytics endpoints
- **WHEN** client sends a request to any analytics aggregation endpoint with one or more of search, rarity, type, set_name, price_min, price_max
- **THEN** system filters the collection using the same semantics as GET `/api/stats` (name contains search, exact match for rarity/type/set_name, price in [price_min, price_max]) and returns aggregates for that subset only

#### Scenario: Analytics summary (KPIs) available
- **WHEN** client needs total card count and total value for the current filter context for the Analytics page
- **THEN** system SHALL provide this via an existing or new endpoint (e.g. GET `/api/stats` with same params, or GET `/api/analytics/summary`) so that KPIs and charts use the same filtered subset
