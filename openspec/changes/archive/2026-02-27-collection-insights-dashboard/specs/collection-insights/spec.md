## ADDED Requirements

### Requirement: Insight catalog defines available questions
The system SHALL maintain a catalog of predefined insight questions. Each question SHALL have: an `id` (unique string), `label_key` (i18n key), `label` (English display text), `keywords` (array of search terms for autocomplete matching), `category` (one of: summary, distribution, ranking, patterns, activity), `icon` (emoji or icon identifier), `response_type` (one of: value, distribution, list, comparison, timeline), and `popular` (boolean, whether eligible for suggestion chips).

#### Scenario: Catalog contains all 17 insights
- **WHEN** the catalog is loaded
- **THEN** it SHALL contain exactly these insight IDs grouped by category:
  - summary: `total_value`, `total_cards`, `avg_card_value`
  - distribution: `by_color`, `by_rarity`, `by_set`, `value_by_color`, `value_by_set`
  - ranking: `most_valuable`, `least_valuable`, `most_collected_set`
  - patterns: `duplicates`, `missing_colors`, `no_price`, `singleton_sets`
  - activity: `recent_additions`, `monthly_summary`, `biggest_month`

#### Scenario: Each catalog entry has i18n-ready label key
- **WHEN** an insight entry is retrieved from the catalog
- **THEN** it SHALL have a `label_key` field following the pattern `insights.<id>.question`

### Requirement: Insight execution returns rich typed responses
The system SHALL execute an insight by ID and return a response containing: `insight_id`, `question` (display text), `answer_text` (human-readable answer string), `response_type`, and a `data` object whose shape depends on the response type.

#### Scenario: Value response type
- **WHEN** insight `total_value` is executed
- **THEN** the response SHALL have `response_type: "value"` and `data` containing `primary_value` (formatted string), optional `unit`, and optional `breakdown` array of `{label, value}` objects

#### Scenario: Distribution response type
- **WHEN** insight `by_color` is executed
- **THEN** the response SHALL have `response_type: "distribution"` and `data` containing `items` array where each item has `label`, `count`, `percentage` (number 0-100), and optional `color` (CSS color or mana symbol key)

#### Scenario: List response type
- **WHEN** insight `most_valuable` is executed
- **THEN** the response SHALL have `response_type: "list"` and `data` containing `items` array where each item has `name`, `detail` (e.g. formatted price), optional `card_id`, and optional `image_url`

#### Scenario: Comparison response type
- **WHEN** insight `missing_colors` is executed
- **THEN** the response SHALL have `response_type: "comparison"` and `data` containing `items` array where each item has `label`, `present` (boolean), and optional `detail`

#### Scenario: Timeline response type
- **WHEN** insight `monthly_summary` is executed
- **THEN** the response SHALL have `response_type: "timeline"` and `data` containing `items` array where each item has `period` (e.g. "Feb 2026"), `count`, and optional `value` (monetary)

### Requirement: Contextual suggestions rotate based on collection signals
The system SHALL analyze the user's collection to determine which insight questions are most relevant and return the top 5-6 insight IDs as suggestions.

#### Scenario: Recent activity boosts activity insights
- **WHEN** the user has added cards within the last 7 days
- **THEN** suggestions SHALL include `recent_additions`

#### Scenario: Duplicates detected boosts patterns insights
- **WHEN** the collection contains cards with duplicate names
- **THEN** suggestions SHALL include `duplicates`

#### Scenario: Missing colors boosts comparison insights
- **WHEN** the collection does not contain all 5 MTG colors (WUBRG)
- **THEN** suggestions SHALL include `missing_colors`

#### Scenario: Cards without price boosts data quality insights
- **WHEN** the collection contains cards with null or empty price
- **THEN** suggestions SHALL include `no_price`

#### Scenario: Large collection boosts distribution insights
- **WHEN** the collection contains more than 100 cards
- **THEN** suggestions SHALL include at least one distribution insight (e.g. `by_color` or `value_by_set`)

#### Scenario: Total value always suggested as fallback
- **WHEN** no other signal is strong enough to fill all suggestion slots
- **THEN** `total_value` SHALL be included as a universal fallback suggestion

### Requirement: Insights operate on authenticated user's collection
All insight computations SHALL be scoped to the authenticated user's cards only.

#### Scenario: Insight returns user-scoped data
- **WHEN** an authenticated user executes insight `total_value`
- **THEN** the computed value SHALL reflect only that user's cards, not all cards in the database

#### Scenario: Unauthenticated request rejected
- **WHEN** an unauthenticated client calls any insights endpoint
- **THEN** the system SHALL return HTTP 401

### Requirement: Insight computations handle missing data gracefully
Each insight SHALL handle null, empty, or invalid field values without errors.

#### Scenario: Cards with no price excluded from value calculations
- **WHEN** computing `total_value` and some cards have null or non-numeric price
- **THEN** those cards SHALL be excluded from the sum without error
- **THEN** the `answer_text` SHALL still report the total for cards with valid prices

#### Scenario: Cards with no created_at excluded from activity insights
- **WHEN** computing `recent_additions` and some cards have no `created_at` field
- **THEN** those cards SHALL be excluded from activity-based insights without error
