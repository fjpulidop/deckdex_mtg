## MODIFIED Requirements

### Requirement: Type-line distribution chart
The analytics dashboard SHALL include a Type Distribution chart showing the card count per primary MTG type (Creature, Land, Artifact, Enchantment, Planeswalker, Instant, Sorcery, Battle, Other) derived from the `type_line` field.

The chart SHALL be implemented as a horizontal bar chart (Recharts `BarChart` with `layout="vertical"`) using semantic per-type colours defined in `TYPE_COLORS` in `constants.ts`. Bars SHALL be sorted by descending count.

A backend endpoint `GET /api/analytics/type` SHALL aggregate primary types using the priority extraction rule: take the first word from the portion of `type_line` before the em-dash `—` that matches, in priority order: Creature > Land > Artifact > Enchantment > Planeswalker > Instant > Sorcery > Battle. Non-matching type lines SHALL be counted as "Other".

The endpoint SHALL accept the same filter query parameters as all other analytics endpoints: `search`, `rarity`, `type` (alias), `set_name`, `price_min`, `price_max`, `color_identity`, `cmc`.

**Implementation constraint**: The `GET /api/analytics/type` route SHALL delegate all database access to a public repository method (`CollectionRepository.get_type_line_data`). The route SHALL NOT access private repository methods (`_build_filter_clauses`, `_get_engine`) or import SQLAlchemy directly. Python-level primary-type extraction (`_extract_primary_type`) SHALL remain in the route layer and be applied to the rows returned by the repository.

#### Scenario: Standard type extraction
- **WHEN** a card has `type_line = "Legendary Creature — Dragon"`
- **THEN** it is counted under the "Creature" bucket

#### Scenario: Dual-type card uses priority order
- **WHEN** a card has `type_line = "Artifact Creature — Golem"`
- **THEN** it is counted under "Creature" (Creature ranks above Artifact)

#### Scenario: Land extraction
- **WHEN** a card has `type_line = "Basic Land — Forest"`
- **THEN** it is counted under "Land"

#### Scenario: Unknown type falls to Other
- **WHEN** a card has `type_line = ""` or an unrecognised value
- **THEN** it is counted under "Other"

#### Scenario: Null type_line falls to Other
- **WHEN** a card has `type_line = None`
- **THEN** it is counted under "Other"

#### Scenario: Repository delegation in Postgres mode
- **WHEN** a PostgreSQL repository is active and `GET /api/analytics/type` is called
- **THEN** the route calls `repo.get_type_line_data(user_id, filters)` to retrieve filtered (type_line, quantity) rows
- **AND** the route does not call any private repository method or import SQLAlchemy

#### Scenario: Sheets path uses in-memory collection
- **WHEN** no PostgreSQL repository is available (Sheets mode)
- **THEN** the route reads from the in-memory cached collection and applies `_extract_primary_type` over each card's `type_line` or `type` field

## ADDED Requirements

### Requirement: Repository method for type-line data retrieval
`CollectionRepository` SHALL expose a public method `get_type_line_data(user_id, filters)` that returns a list of dicts with keys `type_line` (str or None) and `quantity` (int) for all cards matching the given filters.

The default implementation in the ABC SHALL return an empty list. `PostgresCollectionRepository` SHALL override this method with a SQL query: `SELECT type_line, quantity FROM cards {where_clause}`, where the WHERE clause is built by the existing `_build_filter_clauses` internal helper (acceptable as same-class access).

#### Scenario: Default ABC returns empty list
- **WHEN** `CollectionRepository.get_type_line_data` is called on the base class
- **THEN** it returns `[]`

#### Scenario: Postgres returns filtered type_line rows
- **WHEN** `PostgresCollectionRepository.get_type_line_data` is called with a user_id and rarity filter
- **THEN** it returns only rows for cards belonging to that user with the matching rarity, each with `type_line` and `quantity` keys

#### Scenario: Postgres handles null type_line
- **WHEN** a card has a NULL `type_line` in the database
- **THEN** the returned dict for that card has `type_line: None` and `quantity` set to the card's quantity value

### Requirement: Test coverage for analytics color-identity endpoint
The test suite SHALL include tests for `GET /api/analytics/color-identity` covering: HTTP 200 response, response body is a JSON array, each element contains `color_identity` and `count` keys, and aggregation counts are correct for a known fixture collection.

#### Scenario: Color identity returns 200
- **WHEN** `GET /api/analytics/color-identity` is called with a mocked empty collection (Sheets path)
- **THEN** the response status is 200

#### Scenario: Color identity response shape
- **WHEN** `GET /api/analytics/color-identity` is called with a mocked collection containing cards with color identities "R", "U", ""
- **THEN** the response is a list where each element has `color_identity` (str) and `count` (int) keys

#### Scenario: Color identity aggregation correctness
- **WHEN** the collection contains 2 Red cards and 1 Blue card
- **THEN** the response includes an entry for the normalized Red identity with count 2 and an entry for normalized Blue with count 1

### Requirement: Test coverage for analytics CMC endpoint
The test suite SHALL include tests for `GET /api/analytics/cmc` covering: HTTP 200 response, response body is a JSON array, each element contains `cmc` and `count` keys, CMC bucket ordering (numeric values ascending, "7+" after "6", "Unknown" last), and edge cases (null CMC maps to "Unknown", float CMC ≥ 7.0 maps to "7+").

#### Scenario: CMC returns 200
- **WHEN** `GET /api/analytics/cmc` is called with a mocked empty collection (Sheets path)
- **THEN** the response status is 200

#### Scenario: CMC response shape
- **WHEN** `GET /api/analytics/cmc` is called with a mocked collection
- **THEN** the response is a list where each element has `cmc` (str) and `count` (int) keys

#### Scenario: Null CMC maps to Unknown
- **WHEN** a card has `cmc = None`
- **THEN** it is counted in the "Unknown" bucket

#### Scenario: CMC >= 7 maps to 7+
- **WHEN** a card has `cmc = 8`
- **THEN** it is counted in the "7+" bucket

#### Scenario: CMC bucket ordering
- **WHEN** the collection contains cards with cmc 0, 3, 8, and None
- **THEN** the result list is ordered: "0", "3", "7+", "Unknown"

### Requirement: Test coverage for analytics type endpoint
The test suite SHALL include tests for `GET /api/analytics/type` covering: HTTP 200 response, response body is a JSON array, each element contains `type_line` and `count` keys, and primary-type extraction is correct for known type_line values (Creature priority over Artifact, Land extraction, Other fallback).

#### Scenario: Type endpoint returns 200
- **WHEN** `GET /api/analytics/type` is called with a mocked empty collection (Sheets path)
- **THEN** the response status is 200

#### Scenario: Type response shape
- **WHEN** `GET /api/analytics/type` is called with a mocked collection
- **THEN** the response is a list where each element has `type_line` (str) and `count` (int) keys

#### Scenario: Creature extracted from legendary creature type_line
- **WHEN** the collection contains a card with `type` = "Legendary Creature — Dragon"
- **THEN** the "Creature" bucket count is 1

#### Scenario: Other for unrecognized type
- **WHEN** the collection contains a card with `type` = "" or None
- **THEN** the "Other" bucket count is incremented

#### Scenario: Priority order — Creature wins over Artifact
- **WHEN** the collection contains a card with `type` = "Artifact Creature — Golem"
- **THEN** the card is counted under "Creature", not "Artifact"

### Requirement: Test coverage for price history endpoint
The test suite SHALL include tests for `GET /api/cards/{id}/price-history` covering: 501 response when no Postgres repo is available (Sheets mode), 404 response when the card does not exist, and 200 response with correct `PriceHistoryResponse` shape when the card exists and has history.

#### Scenario: Price history returns 501 in Sheets mode
- **WHEN** `get_collection_repo` returns None and `GET /api/cards/1/price-history` is called
- **THEN** the response status is 501

#### Scenario: Price history returns 404 for missing card
- **WHEN** `get_collection_repo` returns a mock repo whose `get_card_by_id` returns None
- **THEN** `GET /api/cards/99/price-history` returns 404

#### Scenario: Price history returns 200 with correct shape
- **WHEN** `get_collection_repo` returns a mock repo whose `get_card_by_id` returns a card and `get_price_history` returns a list of price points
- **THEN** `GET /api/cards/1/price-history` returns 200 with a body containing `card_id`, `currency`, and `points` (list of objects with `recorded_at`, `price`, `source`, `currency`)
