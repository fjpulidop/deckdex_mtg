## ADDED Requirements

### Requirement: Public demo route
The system SHALL expose a public route `/demo` that renders the Dashboard UI with mock data, requiring no authentication.

#### Scenario: Unauthenticated visitor accesses /demo
- **WHEN** an unauthenticated user navigates to `/demo`
- **THEN** the Dashboard UI SHALL render (CollectionInsights, Filters, CardTable) without redirecting to `/login`

#### Scenario: Demo banner is visible
- **WHEN** the `/demo` page is rendered
- **THEN** a dismissible banner SHALL appear at the top indicating the user is viewing a demo, with a link to sign in

#### Scenario: Demo does not make API calls
- **WHEN** the `/demo` page is rendered
- **THEN** no requests SHALL be made to `/api/cards`, `/api/insights/catalog`, or `/api/insights/suggestions`

### Requirement: Demo mock data
The system SHALL provide realistic hardcoded MTG card data for the demo route.

#### Scenario: Demo card list
- **WHEN** `/demo` renders the CardTable
- **THEN** it SHALL display at least 30 cards with varied rarities (Common, Uncommon, Rare, Mythic), multiple sets, and realistic Scryfall-consistent prices

#### Scenario: Demo insights catalog
- **WHEN** `/demo` renders CollectionInsights
- **THEN** the autocomplete catalog SHALL contain at least 5 insight entries with icons and categories matching the real catalog structure

#### Scenario: Demo suggestion chips
- **WHEN** `/demo` renders CollectionInsights
- **THEN** at least 3 suggestion chips SHALL be visible representing common insights (e.g., most valuable cards, rarity breakdown)

### Requirement: Demo filtering
The demo route SHALL support all Dashboard filter interactions (search, rarity, type, set, price, color) operating entirely on the local mock dataset.

#### Scenario: Search within demo cards
- **WHEN** a visitor types in the search input on `/demo`
- **THEN** the card table SHALL filter the mock cards in real time, matching on card name or set

#### Scenario: Rarity filter on demo cards
- **WHEN** a visitor selects a rarity filter on `/demo`
- **THEN** only mock cards matching that rarity SHALL be displayed

### Requirement: Demo screenshot tooling
The system SHALL provide a Playwright script that captures a screenshot of `/demo` for use as the landing page Hero image.

#### Scenario: Script generates screenshot
- **WHEN** `npm run screenshot:demo` is executed with the dev server running
- **THEN** a PNG file SHALL be saved to `frontend/public/dashboard-preview.png` at 1280×800 resolution

#### Scenario: Script waits for content
- **WHEN** the script navigates to `/demo`
- **THEN** it SHALL wait until the card table rows are visible before capturing, ensuring the screenshot shows populated data
