## ADDED Requirements

### Requirement: Demo displays hardcoded MTG card data
The interactive demo SHALL display a curated set of 10-15 hardcoded MTG cards with realistic data.

#### Scenario: Demo cards have complete data
- **WHEN** interactive demo initializes
- **THEN** each card SHALL have name, set, rarity, and price properties
- **THEN** card data SHALL use real MTG cards (e.g., Lightning Bolt, Black Lotus, Serra Angel, Mox Ruby)
- **THEN** prices SHALL reflect realistic market values (e.g., Lightning Bolt: $0.50, Black Lotus: $50,000)

#### Scenario: Demo cards are displayed in table
- **WHEN** demo renders
- **THEN** cards SHALL display in table format with columns: Name, Set, Rarity, Price
- **THEN** table SHALL be styled consistently with main dashboard CardTable
- **THEN** at least 5-6 rows SHALL be visible without scrolling

### Requirement: Demo search filters cards by name
The interactive demo SHALL allow users to search cards by name with real-time filtering.

#### Scenario: Search input is visible and functional
- **WHEN** demo renders
- **THEN** search input field SHALL be visible above card table
- **THEN** input SHALL have placeholder text (e.g., "Search cards...")
- **THEN** input SHALL be focused on component mount (optional, for UX)

#### Scenario: Search filters as user types
- **WHEN** user types "bolt" in search input
- **THEN** card table SHALL update in real-time (no submit button required)
- **THEN** only cards with "bolt" in name SHALL be visible (case-insensitive match)
- **THEN** results count SHALL update to show filtered total

#### Scenario: Empty search shows all cards
- **WHEN** search input is empty or cleared
- **THEN** all cards SHALL be visible in table
- **THEN** results count SHALL show total card count

#### Scenario: Search with no matches shows empty state
- **WHEN** user types search query that matches no cards (e.g., "xyz123")
- **THEN** table SHALL show empty state message (e.g., "No cards found")
- **THEN** results count SHALL show "0 cards"

### Requirement: Demo filters cards by rarity
The interactive demo SHALL allow users to filter cards by rarity using button toggles.

#### Scenario: Rarity filter buttons are visible
- **WHEN** demo renders
- **THEN** rarity filter buttons SHALL be visible (All, Common, Uncommon, Rare, Mythic)
- **THEN** "All" button SHALL be active by default
- **THEN** buttons SHALL be horizontally aligned and evenly spaced

#### Scenario: Clicking rarity filter updates results
- **WHEN** user clicks "Rare" rarity button
- **THEN** button SHALL transition to active state (highlighted background)
- **THEN** card table SHALL show only Rare rarity cards
- **THEN** results count SHALL update
- **THEN** previous active button SHALL return to inactive state

#### Scenario: All filter shows all cards
- **WHEN** user clicks "All" button after having a rarity filter active
- **THEN** card table SHALL show all cards regardless of rarity
- **THEN** results count SHALL show total card count

### Requirement: Demo combines search and rarity filters
The interactive demo SHALL support simultaneous search and rarity filtering.

#### Scenario: Search and filter work together
- **WHEN** user types "bolt" in search AND selects "Common" rarity
- **THEN** card table SHALL show only cards matching both criteria (name contains "bolt" AND rarity is Common)
- **THEN** results count SHALL reflect combined filter

#### Scenario: Clearing search preserves rarity filter
- **WHEN** user has both search and rarity filter active AND clears search input
- **THEN** rarity filter SHALL remain active
- **THEN** card table SHALL show all cards of selected rarity

#### Scenario: Selecting All rarity preserves search
- **WHEN** user has both search and rarity filter active AND clicks "All" rarity
- **THEN** search filter SHALL remain active
- **THEN** card table SHALL show all cards matching search (any rarity)

### Requirement: Demo displays results count
The interactive demo SHALL display a count of currently visible cards based on active filters.

#### Scenario: Results count updates with filters
- **WHEN** filters change (search or rarity)
- **THEN** results count text SHALL update immediately (e.g., "Results: 3 cards")
- **THEN** count SHALL accurately reflect number of visible rows in table

#### Scenario: Results count uses proper grammar
- **WHEN** exactly 1 card matches filters
- **THEN** results count SHALL display "1 card" (singular)
- **WHEN** 0 or 2+ cards match filters
- **THEN** results count SHALL display "X cards" (plural)

### Requirement: Demo is visually distinct from real dashboard
The interactive demo SHALL be clearly identifiable as demo data to avoid user confusion.

#### Scenario: Demo disclaimer is visible
- **WHEN** demo renders
- **THEN** disclaimer text "Demo data" or "Sample data" SHALL be prominently displayed
- **THEN** disclaimer SHALL use muted color (e.g., text-gray-500)

#### Scenario: Demo has visual boundary
- **WHEN** demo section renders on landing page
- **THEN** demo SHALL have border or background color distinct from surrounding content
- **THEN** demo SHALL have padding/margin to create visual separation

### Requirement: Demo is responsive on all devices
The interactive demo SHALL function on mobile, tablet, and desktop viewports.

#### Scenario: Demo table is scrollable on mobile
- **WHEN** demo renders on mobile (<768px)
- **THEN** card table SHALL be horizontally scrollable if columns don't fit
- **THEN** search and filter controls SHALL remain visible above table

#### Scenario: Rarity filters wrap on mobile
- **WHEN** demo renders on mobile (<768px)
- **THEN** rarity filter buttons SHALL wrap to multiple rows if needed
- **THEN** button touch targets SHALL be at least 44x44px

### Requirement: Demo has no backend dependencies
The interactive demo SHALL function entirely client-side without API calls.

#### Scenario: Demo works offline
- **WHEN** demo initializes
- **THEN** no network requests SHALL be made for card data
- **THEN** all card data SHALL be hardcoded in component or imported from constant

#### Scenario: Demo performance is instant
- **WHEN** user types in search or clicks filter
- **THEN** results SHALL update within 50ms (synchronous filtering)
- **THEN** no loading spinners or async operations SHALL be used

### Requirement: Demo encourages conversion after interaction
The interactive demo SHALL include call-to-action to encourage signup after user engagement.

#### Scenario: CTA is visible below demo
- **WHEN** demo section renders
- **THEN** CTA button "Create Your Free Account" SHALL be visible below demo table
- **THEN** button SHALL be primary styled and centered

#### Scenario: CTA navigates to signup
- **WHEN** user clicks demo CTA button
- **THEN** application SHALL navigate to `/login` route
