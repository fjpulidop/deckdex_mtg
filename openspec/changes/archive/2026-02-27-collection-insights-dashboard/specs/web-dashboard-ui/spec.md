## ADDED Requirements

### Requirement: Collection Insights widget replaces Top 5 Most Valuable
The Dashboard SHALL display a Collection Insights widget in the position previously occupied by the TopValueCards component. The TopValueCards component SHALL be removed from the Dashboard.

#### Scenario: Insights widget visible on dashboard
- **WHEN** an authenticated user views the Dashboard
- **THEN** the Collection Insights widget SHALL be displayed between StatsCards and Filters
- **THEN** the Top 5 Most Valuable section SHALL NOT be displayed

### Requirement: Insights search autocomplete
The Collection Insights widget SHALL include a text input that filters the insight catalog by keyword matching as the user types.

#### Scenario: User types and sees matching questions
- **WHEN** the user types "value" in the insights search input
- **THEN** a dropdown SHALL appear showing insights whose keywords match (e.g. "How much is my collection worth?", "Where is my value concentrated by color?")

#### Scenario: User selects a question from autocomplete
- **WHEN** the user clicks a question in the autocomplete dropdown
- **THEN** the system SHALL execute that insight and display the response in the response area below
- **THEN** the dropdown SHALL close

### Requirement: Contextual suggestion chips
The Collection Insights widget SHALL display 5-6 suggestion chips below the search input. Chips represent the most relevant questions for the user's current collection state.

#### Scenario: Chips load on dashboard mount
- **WHEN** the Dashboard mounts
- **THEN** the widget SHALL fetch suggestions from `GET /api/insights/suggestions`
- **THEN** the returned insight IDs SHALL be rendered as clickable chips with icon and short label

#### Scenario: Chip hover effect
- **WHEN** the user hovers over a suggestion chip
- **THEN** the chip SHALL display an elevation effect (shadow-lg), slight scale increase (1.03), and border color change
- **THEN** the transition SHALL be smooth (200ms ease)

#### Scenario: Chip click executes insight
- **WHEN** the user clicks a suggestion chip
- **THEN** the system SHALL execute the corresponding insight and display the response

### Requirement: Rich response visualizations
The response area SHALL render different visualizations based on the `response_type` of the insight response.

#### Scenario: Value response renders big number with breakdown
- **WHEN** an insight returns `response_type: "value"`
- **THEN** the primary value SHALL be displayed in a large, bold font
- **THEN** if breakdown data is present, it SHALL be displayed below as secondary text

#### Scenario: Distribution response renders horizontal bars
- **WHEN** an insight returns `response_type: "distribution"`
- **THEN** each item SHALL be rendered as a labeled horizontal bar
- **THEN** bar width SHALL be proportional to the percentage value
- **THEN** for color-related distributions, bars SHALL use MTG color theming (yellow for W, blue for U, gray/black for B, red for R, green for G) and display Scryfall mana symbols via the existing `card-symbol` CSS classes

#### Scenario: List response renders ranked items
- **WHEN** an insight returns `response_type: "list"`
- **THEN** items SHALL be rendered as a numbered list
- **THEN** if `card_id` is present, the item SHALL be clickable and open the CardDetailModal
- **THEN** if `image_url` is present, a thumbnail SHALL be displayed

#### Scenario: Comparison response renders presence indicators
- **WHEN** an insight returns `response_type: "comparison"`
- **THEN** each item SHALL display a check (green) or cross (red) indicator based on the `present` boolean

#### Scenario: Timeline response renders period bars
- **WHEN** an insight returns `response_type: "timeline"`
- **THEN** items SHALL be rendered as horizontal bars grouped by period label

### Requirement: Response animations
All insight responses SHALL animate into view to provide visual feedback.

#### Scenario: Value type count-up animation
- **WHEN** a value response is rendered
- **THEN** the primary number SHALL animate from 0 to the final value (count-up effect)
- **THEN** breakdown items SHALL fade in with staggered delay (50ms per item)

#### Scenario: Distribution bars grow animation
- **WHEN** a distribution response is rendered
- **THEN** bars SHALL animate from 0 width to final width (400ms, ease-out)
- **THEN** bars SHALL be staggered (80ms delay per bar)

#### Scenario: List items slide-in animation
- **WHEN** a list response is rendered
- **THEN** items SHALL slide in from the left with staggered delay (60ms per item)

### Requirement: Mana symbol icons in color filter buttons
The Filters component color toggle buttons SHALL display Scryfall mana symbol SVGs instead of plain letter text.

#### Scenario: Color button shows mana symbol
- **WHEN** the Filters component renders the color toggle bar
- **THEN** each color button (W, U, B, R, G) SHALL display the corresponding Scryfall mana symbol using the `card-symbol card-symbol-{symbol}` CSS classes
- **THEN** the button SHALL retain its circular shape, hover effects, and active/inactive states

## MODIFIED Requirements

### Requirement: Dashboard layout
The Dashboard page SHALL display StatsCards, Collection Insights, Filters, and CardTable in that order. The page SHALL NOT display a title block — the navbar provides branding.

#### Scenario: Dashboard content order
- **WHEN** an authenticated user views the Dashboard
- **THEN** the page SHALL render in this order: StatsCards → Collection Insights → Filters → CardTable
- **THEN** no "DeckDex MTG" heading or "Manage your Magic: The Gathering collection" subtitle SHALL be present on the page

## REMOVED Requirements

### Requirement: Top 5 most valuable cards widget
**Reason**: Replaced by the interactive Collection Insights widget which provides the same data (via the `most_valuable` insight) plus 16 additional insights on demand.
**Migration**: The "most valuable cards" data is available as insight ID `most_valuable` in the new Collection Insights widget.
