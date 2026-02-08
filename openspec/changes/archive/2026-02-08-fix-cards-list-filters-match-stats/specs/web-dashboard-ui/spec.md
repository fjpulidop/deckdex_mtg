## MODIFIED Requirements

### Requirement: Dashboard SHALL provide card filtering by all table dimensions

The system SHALL allow users to filter the card table by name (search), rarity, type, set, and price range. The dashboard SHALL request GET `/api/cards` with the current filter parameters (search, rarity, type, set_name, price_min, price_max) so that the displayed card list is the same subset used for Total Cards, Total Value, and Average Price; the list SHALL NOT be produced by client-side filtering of a larger unfiltered response. Filter controls SHALL be presented in a single filter bar consistent with existing Tailwind styling (rounded-lg, shadow, focus:ring-blue-500). The system SHALL show active filters as removable chips and SHALL display a result count that updates when filters change. A single "Clear Filters" action SHALL reset all filters.

#### Scenario: Filter cards by name search
- **WHEN** the user types in the search box
- **THEN** the system requests GET `/api/cards` with the search parameter and displays the returned list; the result count and table reflect that list

#### Scenario: Filter by rarity
- **WHEN** the user selects a rarity filter (e.g. "Rare") from the rarity dropdown
- **THEN** the system requests GET `/api/cards` with the rarity parameter and displays the returned list; the result count and table reflect that list

#### Scenario: Filter by type
- **WHEN** the user selects a type from the type dropdown (options derived from loaded card data)
- **THEN** the system requests GET `/api/cards` with the type parameter and displays the returned list; the result count and table reflect that list

#### Scenario: Filter by set
- **WHEN** the user selects a set from the set dropdown (options derived from loaded card data)
- **THEN** the system requests GET `/api/cards` with the set_name parameter and displays the returned list; the result count and table SHALL match the Total Cards and Total Value shown in the stats cards for that set

#### Scenario: Filter by price range
- **WHEN** the user enters an optional min and/or max price (decimal, EUR)
- **THEN** the system requests GET `/api/cards` with price_min/price_max and displays the returned list; the result count and table reflect that list; empty min or max means no bound on that side

#### Scenario: Active filters shown as removable chips
- **WHEN** one or more filters are active (non-default rarity, type, set, or price range)
- **THEN** the system displays each active filter as a chip (or tag) with a control to remove that filter; removing a chip SHALL clear only that filter and leave others unchanged

#### Scenario: Result count visible
- **WHEN** the user views the filter bar or changes any filter
- **THEN** the system displays a result count (e.g. "Showing X cards" or "X results") that reflects the current filtered list length

#### Scenario: Clear all filters
- **WHEN** the user clicks "Clear Filters"
- **THEN** the system resets search, rarity, type, set, and price to their defaults and requests GET `/api/cards` without filter params (or with search only if retained); the table and result count reflect the response

#### Scenario: Multiple filters combine
- **WHEN** the user applies more than one filter (e.g. rarity Rare and set "Dominaria")
- **THEN** the system requests GET `/api/cards` with all active filter parameters and displays the returned list; the list and stats SHALL show the same subset
