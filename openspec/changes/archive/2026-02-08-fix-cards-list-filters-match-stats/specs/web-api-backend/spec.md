## MODIFIED Requirements

### Requirement: Backend SHALL provide collection data endpoints

The system SHALL expose endpoints to retrieve card collection data from Google Sheets with robust price parsing. GET `/api/cards` SHALL accept optional query parameters that filter the collection before pagination, using the same semantics as GET `/api/stats`: `search` (name contains, case-insensitive), `rarity`, `type`, `set_name` (exact match), `price_min`, `price_max` (inclusive). When any of these filter parameters are provided, the system SHALL first filter the collection by those criteria and SHALL then apply `limit` and `offset` to the filtered result, so that the returned list and the statistics for the same filter set refer to the same subset of the collection. When no filter parameters are provided (other than limit/offset/search), behavior SHALL remain as before (list from full collection or search-only subset, then paginated).

#### Scenario: List all cards in collection
- **WHEN** client sends GET request to `/api/cards`
- **THEN** system returns JSON array of cards with name, type, price, rarity, and other metadata

#### Scenario: List cards with pagination
- **WHEN** client sends GET request to `/api/cards?limit=50&offset=100`
- **THEN** system returns 50 cards starting from offset 100

#### Scenario: Search cards by name
- **WHEN** client sends GET request to `/api/cards?search=lotus`
- **THEN** system returns only cards whose name contains "lotus" (case-insensitive)

#### Scenario: List cards filtered by set
- **WHEN** client sends GET request to `/api/cards?set_name=Adventures%20in%20the%20Forgotten%20Realms`
- **THEN** system returns only cards whose set_name equals "Adventures in the Forgotten Realms", and the number of cards returned (subject to limit/offset) SHALL be consistent with GET `/api/stats` with the same set_name (i.e. total count and list refer to the same filtered subset)

#### Scenario: List cards with multiple filters
- **WHEN** client sends GET request to `/api/cards` with two or more of search, rarity, type, set_name, price_min, price_max
- **THEN** system filters the collection by all provided criteria (same semantics as GET `/api/stats`: name contains search, exact match for rarity/type/set_name, price in [price_min, price_max]) and returns the paginated (limit/offset) slice of that filtered result

#### Scenario: Get single card details
- **WHEN** client sends GET request to `/api/cards/{card_name}`
- **THEN** system returns detailed JSON object for that card including all available metadata

#### Scenario: Parse price fields with multiple formats in collection cache
- **WHEN** caching collection data from Google Sheets
- **THEN** system uses same robust price parsing logic for CMC and price fields that handles European/US formats with or without thousands separators
