# Web Dashboard UI

React (Vite, port 5173). **Overview:** 2-column grid: Total Cards, Total Value (subtitle Avg: €X.XX); 30s auto-refresh; skeleton loaders. No price chart in MVP (no history DB). **Table:** 50 cards/page; name, type, rarity, price, set; pagination; sort by column. Rows clickable to open card detail modal (image + data); Edit/Delete do not open detail modal. **Filters:** search by name; by rarity, type, set, price range (min/max); active filters as removable chips; result count (e.g. "Showing X cards"); Clear Filters. **Jobs:** App restores jobs on load (GET /api/jobs); Process Cards and Update Prices are in Settings → Deck Actions. POST to start; disable when running. **Progress modal:** 0% "Connecting…"; WebSocket → update bar and "Processing X/Y"; errors in scrollable list; complete → summary (processed, success, errors, duration); Done → close and refetch. Stop → POST cancel, "Stopping…", orange bar; cancelled → "Process cancelled — progress X/Y (Z%)". Minimize + Stop side by side; elapsed timer in header (12s / 2m 34s / 1h 5m). On reopen: GET /api/jobs/{id} for initial state (no 0% flash); if already complete → show result without WebSocket. **WebSocket:** Reconnect up to 3× backoff; "Reconnecting…"; failure → "Connection lost" + Refresh (REST). **Styling:** Tailwind v4 (@tailwindcss/postcss, @import "tailwindcss"); bg-black/50 not bg-opacity-*; responsive grid. **Data:** TanStack Query (cache, isLoading, error + retry). **Errors:** Toast on API failure (5s); process errors → count + CSV link. **Access:** localhost:5173; backend down → friendly error + retry; ErrorBoundary for render errors. **Bottom bar:** Fixed bottom when jobs exist; list jobs vertically; completed → show 5s then remove; cancelled → orange + "Cancelled"; poll GET /api/jobs/{id} every 2s. Modern browsers.

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

### Requirement: Dashboard SHALL restore active jobs on page load

The application SHALL restore visibility of background jobs once at app (or global provider) mount, not when the Dashboard mounts. Dashboard SHALL NOT perform its own GET `/api/jobs` for job restore; job restore SHALL be the responsibility of the global jobs UI (see global-jobs-ui spec).

#### Scenario: No job restore on Dashboard mount
- **WHEN** Dashboard component mounts
- **THEN** Dashboard does NOT send GET `/api/jobs` for the purpose of restoring jobs; restore is done at app level

#### Scenario: Jobs visible on Dashboard from global state
- **WHEN** user is on Dashboard and global job list has one or more jobs
- **THEN** those jobs are displayed in the app-wide bottom bar (provided by global jobs UI)

### Requirement: Dashboard SHALL display active background jobs in fixed bottom bar

The application SHALL show the fixed bottom jobs bar when background jobs exist, at app (or layout) level, so it is visible on Dashboard and Settings. The Dashboard SHALL NOT render its own instance of the jobs bar; the bar SHALL be rendered once by the global jobs UI. Behavior of the bar (position, vertical list, click to open modal, auto-remove completed, cancelled state, polling) SHALL be unchanged and SHALL apply to the single app-wide bar.

#### Scenario: Bar shown at app level when jobs exist
- **WHEN** one or more jobs are in the global job list
- **THEN** the application displays a single fixed bar at the bottom of the viewport, visible on whichever route is active (Dashboard or Settings)

#### Scenario: Dashboard does not render a separate jobs bar
- **WHEN** Dashboard is rendered
- **THEN** Dashboard does NOT render its own ActiveJobs (or equivalent) component; the bar is rendered by the global jobs layer

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

### Requirement: Main content SHALL not be covered by the jobs bar

When one or more background jobs are shown in the fixed bottom jobs bar, the main content area on **every** view (Dashboard and Settings) SHALL reserve bottom space so the jobs bar does not overlap content. Dashboard content (stats, filters, card table, pagination) and Settings content (all sections) SHALL remain fully visible above the bar.

#### Scenario: Table and pagination visible with one job (Dashboard)
- **WHEN** at least one job is active and the user is on Dashboard
- **THEN** the main content has sufficient bottom spacing so that the end of the card table and pagination controls remain visible above the bar

#### Scenario: Settings sections visible with jobs bar
- **WHEN** at least one job is active and the user is on Settings
- **THEN** the main content has sufficient bottom spacing so that all Settings sections (including Deck Actions) remain visible above the bar

#### Scenario: No overlap when scrolling to bottom (any view)
- **WHEN** the user scrolls to the bottom of Dashboard or Settings while jobs are active
- **THEN** the content is fully visible and not obscured by the jobs bar

### Requirement: Settings SHALL provide a Deck Actions section

The Settings page SHALL include a section titled "Deck Actions" that SHALL be the last section on the page (after Scryfall API credentials and Import from file). The section SHALL use the same card style as other Settings sections (e.g. white/dark card with rounded corners and shadow). Inside the section, the system SHALL provide: (1) Process Cards control with scope choice (e.g. new added cards only, or all cards) and (2) Update Prices control. Triggering either action SHALL POST to the existing backend endpoints and SHALL register the started job with the global job state so the job appears in the app-wide jobs bar. Buttons SHALL be disabled while a start request is in progress.

#### Scenario: Deck Actions is last section with same card style
- **WHEN** user opens Settings
- **THEN** a section "Deck Actions" is present after Scryfall credentials and Import from file, with the same section/card styling as the other two sections

#### Scenario: Process Cards and Update Prices available in Deck Actions
- **WHEN** user is on Settings
- **THEN** Process Cards (with scope dropdown) and Update Prices controls are available inside the Deck Actions section

#### Scenario: Starting a job from Settings shows it in global jobs bar
- **WHEN** user starts Process Cards or Update Prices from Settings
- **THEN** the new job appears in the fixed bottom jobs bar and remains visible when user navigates to Dashboard or stays on Settings

### Requirement: Each job SHALL offer a way to view progress and log in a modal

Each job entry in the bottom jobs bar SHALL provide a control (e.g. button or link) that opens a modal (or equivalent overlay) dedicated to that job. The modal SHALL display that job's progress (e.g. percentage, current/total, elapsed time) and log or progress output so the user can see how the job is advancing.

#### Scenario: Open job log modal from bar
- **WHEN** the user activates the "View log" (or equivalent) control on a job in the bottom bar
- **THEN** a modal opens showing that job's progress and log (or progress and errors) for the selected job

#### Scenario: Modal shows live progress
- **WHEN** the modal is open for a running job
- **THEN** the modal shows up-to-date progress (e.g. percentage, current/total) and any log or error output, updating as the job runs (e.g. via existing WebSocket or polling)

#### Scenario: Modal can be closed
- **WHEN** the user closes the modal (e.g. close button or overlay click)
- **THEN** the modal is dismissed and the user returns to the dashboard view; the job continues in the bar as before

### Requirement: Card table rows SHALL be clickable to open card detail modal

The system SHALL allow the user to click on a card table row to open a read-only card detail modal. Clicks on row actions (Edit, Delete) SHALL NOT open the detail modal; only clicking the row itself SHALL trigger opening the modal.

#### Scenario: Clicking a row opens card detail modal
- **WHEN** the user clicks on a card row in the table (and not on Edit or Delete)
- **THEN** the system opens the card detail modal with that card's data and loads its image

#### Scenario: Clicking Edit does not open detail modal
- **WHEN** the user clicks the Edit button on a row
- **THEN** the system performs the edit action (e.g. opens edit form) and does NOT open the card detail modal

#### Scenario: Clicking Delete does not open detail modal
- **WHEN** the user clicks the Delete button on a row
- **THEN** the system performs the delete action and does NOT open the card detail modal

#### Scenario: Dashboard wires table to card detail modal
- **WHEN** the dashboard renders the card table
- **THEN** the table is configured with a row-click handler that opens the card detail modal for the clicked card, and the modal receives the selected card and uses the image API for that card's id

### Requirement: Add card form SHALL have only name input with autocomplete

The Add card modal SHALL display a single required field for card name. The name field SHALL support autocomplete with suggestions from the collection and, when applicable, from the catalog (Scryfall). The form SHALL NOT display input fields for type, rarity, price, or set when adding a card; those values SHALL be obtained by the system when the user selects a suggestion (from collection or catalog) and SHALL be sent in the create request. The Edit card modal SHALL continue to display and allow editing of name, type, rarity, price, and set for existing cards.

#### Scenario: Add card modal shows only name field
- **WHEN** the user opens the Add card modal
- **THEN** the form SHALL show one text input for card name (with autocomplete) and Add/Cancel actions; it SHALL NOT show inputs for type, rarity, price, or set

#### Scenario: Name field shows debounced autocomplete dropdown
- **WHEN** the user types in the Add card name field
- **THEN** after a short debounce (e.g. 250–300 ms) the system SHALL show a dropdown with suggestions (collection and optionally catalog), with sections labeled e.g. "In your collection" and "Other cards" when both are present

#### Scenario: Edit card modal still has all fields
- **WHEN** the user opens the Edit card modal for an existing card
- **THEN** the form SHALL show editable fields for name, type, rarity, price, and set as today; behaviour SHALL be unchanged from current Edit card flow
