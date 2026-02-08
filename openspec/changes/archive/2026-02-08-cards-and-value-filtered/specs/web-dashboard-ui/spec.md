## MODIFIED Requirements

### Requirement: Dashboard SHALL display collection overview

The system SHALL provide a dashboard page that visualizes collection statistics in a streamlined 2-column layout without non-persistent temporal metadata. The dashboard SHALL request stats from the backend with the current filter parameters (search, rarity, type, set, price_min, price_max) so that the displayed Total Cards, Total Value, and Average Price reflect the filtered collection and remain correct regardless of list limit or pagination. The displayed values SHALL be exactly those returned by GET `/api/stats` with those parameters.

#### Scenario: Display summary statistics cards in 2-column grid
- **WHEN** user opens dashboard
- **THEN** system displays 2 cards in responsive grid: Total Cards (left) and Total Value (right)

#### Scenario: Display average price as subtitle under Total Value
- **WHEN** Total Value card is rendered
- **THEN** system displays average price in smaller gray text below the total value amount (format: "Avg: €X.XX")

#### Scenario: Stats requested with current filter parameters
- **WHEN** user has one or more filters active (search, rarity, type, set, price range)
- **THEN** system sends GET request to `/api/stats` with the same filter parameters and displays the returned total_cards, total_value, and average_price in the stats cards

#### Scenario: Stats update when filters change
- **WHEN** user changes any filter (search, rarity, type, set, or price range)
- **THEN** system refetches stats with the new filter parameters and updates the displayed Total Cards, Total Value, and Average Price to match the filtered set

#### Scenario: Statistics auto-refresh every 30 seconds
- **WHEN** user remains on dashboard
- **THEN** system automatically refetches stats every 30 seconds (with current filter parameters) without page reload

#### Scenario: Loading state while fetching data
- **WHEN** dashboard is loading collection data
- **THEN** system displays skeleton loaders for 2 stat cards (not 3)
