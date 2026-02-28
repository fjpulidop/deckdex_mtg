# Web Dashboard UI

React (Vite, port 5173). **Overview:** Dashboard layout (top to bottom): Collection Insights widget, Filters, CardTable. No static stats cards. **Table:** sortable (name, type, rarity, price, Added); default sort newest first (created_at desc); 50 cards/page; rows clickable → card detail modal; Edit/Delete do not open detail. **Mana symbols:** Scryfall-style SVGs in card text (`.card-symbol`); no raw {W}/{U}. Color filter buttons use mana symbol SVGs (not plain letters). **Filters:** search, rarity, type, set, price range; active filters as removable chips; result count; Clear Filters. GET /api/cards with same params. **Jobs:** Restore on app mount (GET /api/jobs); Process Cards and Update Prices in Settings → Deck Actions. Progress modal: WebSocket + GET /api/jobs/{id} for initial state; Minimize + Stop; elapsed timer. Bottom bar: fixed when jobs exist; single app-wide bar (global-jobs-ui); content area reserves space so bar doesn’t overlap. **Styling:** Tailwind v4; theme (light/dark). **Data:** TanStack Query. **Errors:** Toast on API failure; ErrorBoundary. **Nav:** Settings, Analytics (beta) → /analytics.

### Requirements (compact)

- **Dashboard layout:** Collection Insights → Filters → CardTable. No title block (navbar provides branding). No static stats cards.
- **Collection Insights:** Interactive widget with search/autocomplete (keyword matching against catalog), 5-6 contextual suggestion chips, animated response area. Fetches catalog from GET /api/insights/catalog, suggestions from GET /api/insights/suggestions, executes via POST /api/insights/{id}.
- **Filters:** GET /api/cards with search, rarity, type, set_name, price_min, price_max; chips + result count + Clear Filters; no client-side filter of unfiltered response. Color buttons use `card-symbol card-symbol-{W|U|B|R|G}` SVGs.
- **Table:** Sort by name/type/rarity/price/Added (numeric for price, lexicographic others; empty price last). Default: Added desc (newest first). Added column sortable, shows date when created_at present.
- **Jobs bar:** One bar at app level when jobs exist; Dashboard does not render its own. Main content (Dashboard + Settings) reserves bottom space so bar doesn’t overlap.
- **Settings:** Deck Actions last section: Process Cards (scope), Update Prices; trigger → job in global bar.
- **Job modal:** Open from bar; progress + log; close dismisses; live updates.
- **Card row click:** Opens detail modal (not Edit/Delete). Table wired to modal + image API by card id.
- **Add card:** Single name field + autocomplete (collection + Scryfall); no type/rarity/price/set inputs; Edit modal keeps all fields.
- **Nav:** Analytics (beta) link next to Settings → /analytics; route /analytics renders Analytics page (analytics-dashboard spec); responsive + theme.

### Requirement: Collection Insights widget replaces Top 5 Most Valuable
The Dashboard SHALL display a Collection Insights widget. The TopValueCards component has been removed.

#### Scenario: Insights widget visible on dashboard
- **WHEN** an authenticated user views the Dashboard
- **THEN** the Collection Insights widget SHALL be displayed before Filters
- **THEN** no "Top 5 Most Valuable" section SHALL be displayed

### Requirement: Insights search autocomplete
The Collection Insights widget SHALL include a text input that filters the insight catalog by keyword matching as the user types.

#### Scenario: User types and sees matching questions
- **WHEN** the user types "value" in the insights search input
- **THEN** a dropdown SHALL appear showing insights whose keywords match

#### Scenario: User selects a question from autocomplete
- **WHEN** the user clicks a question in the autocomplete dropdown
- **THEN** the system SHALL execute that insight and display the response in the response area below
- **THEN** the dropdown SHALL close

### Requirement: Contextual suggestion chips
The Collection Insights widget SHALL display 5-6 suggestion chips below the search input. Chips represent the most relevant questions for the user's current collection state.

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
- **THEN** the primary value SHALL be displayed in a large, bold font with count-up animation
- **THEN** if breakdown data is present, it SHALL fade in with staggered delay (50ms per item)

#### Scenario: Distribution response renders horizontal bars
- **WHEN** an insight returns `response_type: "distribution"`
- **THEN** each item SHALL be rendered as a labeled horizontal bar (grow animation 400ms ease-out, 80ms stagger)
- **THEN** for color-related distributions, bars SHALL use MTG color theming and display Scryfall mana symbols via `card-symbol` CSS classes

#### Scenario: List response renders ranked items
- **WHEN** an insight returns `response_type: "list"`
- **THEN** items SHALL slide in from the left with staggered delay (60ms per item)
- **THEN** if `card_id` is present, the item SHALL be clickable and open the CardDetailModal

#### Scenario: Comparison response renders presence indicators
- **WHEN** an insight returns `response_type: "comparison"`
- **THEN** each item SHALL display a check (green) or cross (red) indicator with scale-in bounce animation

#### Scenario: Timeline response renders period bars
- **WHEN** an insight returns `response_type: "timeline"`
- **THEN** items SHALL be rendered as horizontal bars grouped by period label with staggered grow animation

### Requirement: Mana symbol icons in color filter buttons
The Filters component color toggle buttons SHALL display Scryfall mana symbol SVGs instead of plain letter text.

#### Scenario: Color button shows mana symbol
- **WHEN** the Filters component renders the color toggle bar
- **THEN** each color button (W, U, B, R, G) SHALL display the corresponding Scryfall mana symbol using the `card-symbol card-symbol-{symbol}` CSS classes
- **THEN** the button SHALL retain its circular shape, hover effects, and active/inactive states

## Requirements
### Requirement: Login page replaces anonymous access
The frontend SHALL display a login page for unauthenticated users instead of showing the dashboard directly.

#### Scenario: Unauthenticated user sees login page
- **WHEN** an unauthenticated user opens the application
- **THEN** the app SHALL redirect to `/login` and display a "Continue with Google" button

#### Scenario: Authenticated user sees dashboard
- **WHEN** an authenticated user opens the application at `/`
- **THEN** the app SHALL display the dashboard with that user's cards and stats

### Requirement: All pages wrapped in ProtectedRoute
Every page (Dashboard, Settings, Analytics, Decks) SHALL be wrapped in a `ProtectedRoute` component that redirects to `/login` when the user is not authenticated.

#### Scenario: ProtectedRoute redirects unauthenticated user
- **WHEN** an unauthenticated user navigates to `/settings`
- **THEN** the app SHALL redirect to `/login`

#### Scenario: ProtectedRoute allows authenticated user
- **WHEN** an authenticated user navigates to `/settings`
- **THEN** the app SHALL render the Settings page normally

### Requirement: Loading state during auth check
The app SHALL show a loading indicator while checking authentication status on mount (not the login page and not the dashboard).

#### Scenario: Loading spinner during auth check
- **WHEN** the app is checking the authentication status (`isLoading = true`)
- **THEN** the app SHALL display a centered loading spinner or skeleton
- **THEN** the app SHALL NOT flash the login page or the dashboard

