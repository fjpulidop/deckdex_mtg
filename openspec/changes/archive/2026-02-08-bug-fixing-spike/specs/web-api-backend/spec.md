## MODIFIED Requirements

### Requirement: Backend SHALL provide collection statistics endpoint

The system SHALL calculate and return aggregate statistics about the collection with robust price parsing that handles multiple European and US number formats.

#### Scenario: Get collection summary statistics
- **WHEN** client sends GET request to `/api/stats`
- **THEN** system returns JSON with total_cards, total_value, average_price, last_updated timestamp

#### Scenario: Statistics cached to avoid excessive Sheets API calls
- **WHEN** client requests stats within 30 seconds of previous request
- **THEN** system returns cached statistics without querying Google Sheets

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

### Requirement: Backend SHALL provide collection data endpoints

The system SHALL expose endpoints to retrieve card collection data from Google Sheets with robust price parsing.

#### Scenario: List all cards in collection
- **WHEN** client sends GET request to `/api/cards`
- **THEN** system returns JSON array of cards with name, type, price, rarity, and other metadata

#### Scenario: List cards with pagination
- **WHEN** client sends GET request to `/api/cards?limit=50&offset=100`
- **THEN** system returns 50 cards starting from offset 100

#### Scenario: Search cards by name
- **WHEN** client sends GET request to `/api/cards?search=lotus`
- **THEN** system returns only cards whose name contains "lotus" (case-insensitive)

#### Scenario: Get single card details
- **WHEN** client sends GET request to `/api/cards/{card_name}`
- **THEN** system returns detailed JSON object for that card including all available metadata

#### Scenario: Parse price fields with multiple formats in collection cache
- **WHEN** caching collection data from Google Sheets
- **THEN** system uses same robust price parsing logic for CMC and price fields that handles European/US formats with or without thousands separators
