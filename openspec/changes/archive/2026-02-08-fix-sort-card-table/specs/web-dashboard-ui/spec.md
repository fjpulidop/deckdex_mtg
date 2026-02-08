## ADDED Requirements

### Requirement: Card table SHALL sort columns by appropriate type (numeric vs string)

The card table SHALL support sort by column (name, type, rarity, price). Sort SHALL be applied to the full set of cards (all rows provided to the table) before pagination, so that the same order is consistent across every page. The Price column SHALL be sorted by numeric value (ascending or descending); empty or non-numeric price values SHALL be placed last in both directions. All other sortable columns (name, type, rarity) SHALL be sorted lexicographically (string comparison). Sort direction SHALL be toggleable per column and SHALL be indicated in the UI (e.g. arrow).

#### Scenario: Price column sorts by numeric value ascending
- **WHEN** the user sorts by Price ascending (e.g. clicks Price header until ascending)
- **THEN** the table SHALL order rows by price from lowest to highest numeric value (e.g. 7, 9, 81), not by string order (e.g. 7, 81, 9)

#### Scenario: Price column sorts by numeric value descending
- **WHEN** the user sorts by Price descending
- **THEN** the table SHALL order rows by price from highest to lowest numeric value (e.g. 81, 9, 7)

#### Scenario: Non-numeric or empty price sorts last
- **WHEN** some cards have missing or non-numeric price and the user sorts by Price (asc or desc)
- **THEN** those rows SHALL appear last in the sorted list; numeric prices SHALL be ordered correctly among themselves

#### Scenario: Name, type, and rarity columns sort lexicographically
- **WHEN** the user sorts by Name, Type, or Rarity (asc or desc)
- **THEN** the table SHALL order rows by string comparison for that column (current behaviour unchanged)

#### Scenario: Sort applies to all pages
- **WHEN** the user sorts by any column and the result spans multiple pages
- **THEN** the table SHALL apply the sort to the full card list first, then paginate; changing page SHALL show the next segment of that same global order (e.g. page 2 continues the order from page 1)
