# Analytics Dashboard (beta)

Library analytics dashboard: metrics, charts, and drill-down over the card collection. Beta feature; no specific chart library mandated; usability and consistency with the rest of the dashboard required.

### Requirement: Analytics page SHALL display summary KPIs for the current context

The system SHALL display at least two summary metrics for the current filter/drill-down context: total card count and total value (e.g. EUR). Optionally, average price SHALL be shown as a subtitle or secondary metric. These values SHALL be fetched from the backend using the same filter parameters as the rest of the dashboard (search, rarity, type, set_name, price_min, price_max, and any drill-down slice). The KPIs SHALL update when the user changes context (e.g. by clicking a chart segment).

#### Scenario: Display card count and total value for full collection
- **WHEN** user opens Analytics with no filters applied
- **THEN** system displays total number of cards and total value (e.g. "€X.XX") for the entire collection

#### Scenario: KPIs update when drill-down context changes
- **WHEN** user clicks a segment in a chart (e.g. "Rare" in rarity chart)
- **THEN** system recalculates and displays card count and total value for that subset only; all other charts and KPIs reflect the same subset

### Requirement: Analytics page SHALL show distribution by rarity

The system SHALL display a chart (e.g. bar or column) showing the number of cards per rarity (Common, Uncommon, Rare, Mythic Rare, or other values present in the data). The chart SHALL be based on backend aggregation data. Each data point or segment SHALL be clickable to set the drill-down context to that rarity.

#### Scenario: Rarity chart shows counts per rarity
- **WHEN** user views the Analytics page
- **THEN** system displays a chart with one bar or segment per rarity and the count of cards for that rarity in the current context

#### Scenario: Clicking a rarity filters the dashboard context
- **WHEN** user clicks a rarity in the rarity chart
- **THEN** system updates the active context to that rarity; KPIs and all other charts SHALL refetch with that rarity filter applied

### Requirement: Analytics page SHALL show distribution by color identity

The system SHALL display a chart (e.g. bar, pie, or donut) showing the number of cards per color identity (W, U, B, R, G, colorless, or combinations as returned by the backend). The chart SHALL be based on backend aggregation. Each segment or category SHALL be clickable to set the drill-down context to that color identity.

#### Scenario: Color identity chart shows counts per color
- **WHEN** user views the Analytics page
- **THEN** system displays a chart with one segment or bar per color identity (or grouped) and the count of cards in the current context

#### Scenario: Clicking a color identity filters the dashboard context
- **WHEN** user clicks a color identity in the color chart
- **THEN** system updates the active context to that color identity; KPIs and all other charts SHALL refetch with that filter applied

### Requirement: Analytics page SHALL show distribution by CMC (converted mana cost)

The system SHALL display a chart (e.g. bar or histogram) showing the number of cards per CMC bucket (e.g. 0, 1, 2, … 7+). The chart SHALL be based on backend aggregation. Each bucket SHALL be clickable to set the drill-down context to that CMC range.

#### Scenario: CMC chart shows counts per mana cost bucket
- **WHEN** user views the Analytics page
- **THEN** system displays a chart with buckets for CMC and the count of cards in each bucket in the current context

#### Scenario: Clicking a CMC bucket filters the dashboard context
- **WHEN** user clicks a CMC bucket in the chart
- **THEN** system updates the active context to that CMC; KPIs and all other charts SHALL refetch with that filter applied

### Requirement: Analytics page SHALL show distribution by set (top N)

The system SHALL display a chart (e.g. bar or list) showing the number of cards per set, limited to a reasonable number (e.g. top 10 or 15 sets by count) to keep the chart readable. The chart SHALL be based on backend aggregation. Each set SHALL be clickable to set the drill-down context to that set.

#### Scenario: Set chart shows top sets by card count
- **WHEN** user views the Analytics page
- **THEN** system displays a chart with the top N sets (e.g. 10) by card count in the current context

#### Scenario: Clicking a set filters the dashboard context
- **WHEN** user clicks a set in the set chart
- **THEN** system updates the active context to that set; KPIs and all other charts SHALL refetch with that set filter applied

### Requirement: Analytics page SHALL support clearing drill-down context

The system SHALL provide a clear control (e.g. "View all" or "Clear filters" button or chip) that resets the drill-down context to the full collection (or to the user's explicit filters only, if any). When the user activates this control, all charts and KPIs SHALL refetch without drill-down filters.

#### Scenario: Clear context resets to full collection
- **WHEN** user has applied a drill-down (e.g. clicked "Rare") and then clicks "View all" or equivalent
- **THEN** system clears the drill-down context and refetches all data for the full collection; all charts and KPIs update accordingly

#### Scenario: Active context is visible to the user
- **WHEN** a drill-down filter is active (e.g. rarity = Rare)
- **THEN** system displays the active context (e.g. as a chip or subtitle) so the user knows which subset is being shown

### Requirement: Analytics page SHALL handle loading and empty states

The system SHALL show a loading state (e.g. skeleton loaders or spinners) while analytics data is being fetched. When the collection is empty or the filtered subset has no cards, the system SHALL display an empty state (e.g. message and optional illustration) instead of empty charts. Error states (e.g. API failure) SHALL be surfaced with a clear message and retry option where appropriate.

#### Scenario: Loading state while fetching analytics
- **WHEN** Analytics page is loading aggregation data
- **THEN** system displays loading indicators for KPIs and charts (e.g. skeletons) until data is available

#### Scenario: Empty state when no cards in context
- **WHEN** the current context (full collection or drill-down) has zero cards
- **THEN** system displays an empty state message (e.g. "No cards in this view") and does not show misleading zeroed charts without explanation

#### Scenario: Error state with retry
- **WHEN** analytics API request fails
- **THEN** system displays an error message and, where applicable, a retry control; user can retry without leaving the page

### Requirement: Analytics charts SHALL be visually consistent and accessible

Charts SHALL use a consistent palette and typography aligned with the rest of the application (including light/dark theme). Labels and axes SHALL be readable; color SHALL not be the only way to convey meaning where possible. The spec does not mandate a specific charting library but SHALL require that the chosen implementation meets these consistency and accessibility expectations.

#### Scenario: Charts respect theme
- **WHEN** user has light or dark theme enabled
- **THEN** analytics charts use colors and backgrounds consistent with that theme

#### Scenario: Chart elements have visible labels or legends
- **WHEN** user views any analytics chart
- **THEN** categories (e.g. rarity, color, set) are identifiable via labels, legends, or tooltips so that meaning is clear
