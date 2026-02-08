# API Tests

Automated tests for the backend API (health, stats, cards list) with mocked collection data.

### Requirement: Backend API SHALL have automated tests for health endpoint

The project SHALL include automated tests that call GET `/api/health` and assert the response status is 200 and the response body includes the expected service name, version, and status fields, so that the health contract is validated without external services.

#### Scenario: Health returns 200 and expected body
- **WHEN** the test client sends GET request to `/api/health`
- **THEN** the response status code SHALL be 200 and the JSON body SHALL contain `service`, `version`, and `status` (e.g. "DeckDex MTG API", "0.1.0", "healthy")

### Requirement: Backend API SHALL have automated tests for stats endpoint

The project SHALL include automated tests that call GET `/api/stats` with mocked collection data and assert the response shape and values (total_cards, total_value, average_price, last_updated). Tests SHALL cover at least: empty collection, non-empty collection with parseable prices, and optionally filtered requests (e.g. by rarity or set_name), so that the stats contract is validated without a real database or Google Sheets.

#### Scenario: Stats with empty collection
- **WHEN** the test client sends GET request to `/api/stats` with mocked collection returning an empty list
- **THEN** the response status code SHALL be 200 and the JSON body SHALL contain total_cards 0, total_value 0.0, average_price 0.0, and a last_updated string

#### Scenario: Stats with non-empty collection
- **WHEN** the test client sends GET request to `/api/stats` with mocked collection returning one or more cards with valid price values
- **THEN** the response status code SHALL be 200 and the JSON body SHALL contain total_cards, total_value, average_price, and last_updated consistent with the mocked data (e.g. total_value and average_price derived from parsed prices)

#### Scenario: Stats with filter parameters
- **WHEN** the test client sends GET request to `/api/stats` with query parameters (e.g. rarity, set_name) and mocked collection that includes matching and non-matching cards
- **THEN** the response status code SHALL be 200 and the returned total_cards and total_value SHALL reflect only the subset of the mocked collection that matches the filter semantics (name contains, exact match for rarity/type/set_name, price range inclusive)

### Requirement: Backend API SHALL have automated tests for cards list endpoint

The project SHALL include automated tests that call GET `/api/cards` with mocked collection data and assert the response is a JSON array, status 200, and that pagination (limit/offset) and optional filters (search, rarity, type, set_name, price_min, price_max) reduce or shape the list correctly, so that the cards list contract is validated without a real database or Google Sheets.

#### Scenario: Cards list with empty collection
- **WHEN** the test client sends GET request to `/api/cards` with mocked collection returning an empty list
- **THEN** the response status code SHALL be 200 and the response body SHALL be a JSON array of length 0

#### Scenario: Cards list returns mocked cards
- **WHEN** the test client sends GET request to `/api/cards` with mocked collection returning one or more card objects
- **THEN** the response status code SHALL be 200 and the response body SHALL be a JSON array of cards whose count and content are consistent with the mocked collection (subject to default limit)

#### Scenario: Cards list respects limit and offset
- **WHEN** the test client sends GET request to `/api/cards?limit=2&offset=1` with mocked collection of at least three cards
- **THEN** the response status code SHALL be 200 and the response body SHALL be a JSON array of at most 2 cards, corresponding to the second and third card in the filtered order (offset 1, limit 2)

#### Scenario: Cards list with filter parameters
- **WHEN** the test client sends GET request to `/api/cards` with one or more of search, rarity, type, set_name, price_min, price_max and mocked collection that includes matching and non-matching cards
- **THEN** the response status code SHALL be 200 and the returned array SHALL contain only cards that match the filter semantics (same as GET `/api/stats`: name contains search, exact match for rarity/type/set_name, price in range)
