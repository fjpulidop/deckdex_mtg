# Web Dashboard UI (delta: ux-cards-filter-improvements)

## ADDED Requirements

### Requirement: Dashboard SHALL provide card filtering by all table dimensions

The system SHALL allow users to filter the card table by name (search), rarity, type, set, and price range. Filter controls SHALL be presented in a single filter bar consistent with existing Tailwind styling (rounded-lg, shadow, focus:ring-blue-500). The system SHALL show active filters as removable chips and SHALL display a result count that updates when filters change. A single "Clear Filters" action SHALL reset all filters.

#### Scenario: Filter cards by name search
- **WHEN** the user types in the search box
- **THEN** the system filters cards to those whose name matches the search term (case-insensitive), and the result count and table update accordingly

#### Scenario: Filter by rarity
- **WHEN** the user selects a rarity filter (e.g. "Rare") from the rarity dropdown
- **THEN** the system shows only cards with that rarity, and the result count and table update accordingly

#### Scenario: Filter by type
- **WHEN** the user selects a type from the type dropdown (options derived from loaded card data)
- **THEN** the system shows only cards with that type, and the result count and table update accordingly

#### Scenario: Filter by set
- **WHEN** the user selects a set from the set dropdown (options derived from loaded card data)
- **THEN** the system shows only cards from that set, and the result count and table update accordingly

#### Scenario: Filter by price range
- **WHEN** the user enters an optional min and/or max price (decimal, EUR)
- **THEN** the system shows only cards whose price falls within that range (inclusive), and the result count and table update accordingly; empty min or max means no bound on that side

#### Scenario: Active filters shown as removable chips
- **WHEN** one or more filters are active (non-default rarity, type, set, or price range)
- **THEN** the system displays each active filter as a chip (or tag) with a control to remove that filter; removing a chip SHALL clear only that filter and leave others unchanged

#### Scenario: Result count visible
- **WHEN** the user views the filter bar or changes any filter
- **THEN** the system displays a result count (e.g. "Showing X cards" or "X results") that reflects the current filtered list length

#### Scenario: Clear all filters
- **WHEN** the user clicks "Clear Filters"
- **THEN** the system resets search, rarity, type, set, and price to their defaults and the table and result count reflect the unfiltered (or name-only, if search is retained per product choice) result set

#### Scenario: Multiple filters combine
- **WHEN** the user applies more than one filter (e.g. rarity Rare and set "Dominaria")
- **THEN** the system shows only cards that satisfy all active filters simultaneously
