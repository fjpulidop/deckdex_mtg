# Web Dashboard UI

React (Vite, port 5173). **Overview:** 2-column grid: Total Cards, Total Value (subtitle Avg: €X.XX); 30s auto-refresh; skeleton loaders. No price chart in MVP (no history DB). **Table:** 50 cards/page; name, type, rarity, price, set; pagination; sort by column. Rows clickable to open card detail modal (image + data); Edit/Delete do not open detail modal. **Filters:** search by name; by rarity, type, set, price range (min/max); active filters as removable chips; result count (e.g. "Showing X cards"); Clear Filters. **Jobs:** On mount GET /api/jobs → restore backgroundJobs. Buttons: Process Cards, Update Prices → POST, open progress modal; disable when running. **Progress modal:** 0% "Connecting…"; WebSocket → update bar and "Processing X/Y"; errors in scrollable list; complete → summary (processed, success, errors, duration); Done → close and refetch. Stop → POST cancel, "Stopping…", orange bar; cancelled → "Process cancelled — progress X/Y (Z%)". Minimize + Stop side by side; elapsed timer in header (12s / 2m 34s / 1h 5m). On reopen: GET /api/jobs/{id} for initial state (no 0% flash); if already complete → show result without WebSocket. **WebSocket:** Reconnect up to 3× backoff; "Reconnecting…"; failure → "Connection lost" + Refresh (REST). **Styling:** Tailwind v4 (@tailwindcss/postcss, @import "tailwindcss"); bg-black/50 not bg-opacity-*; responsive grid. **Data:** TanStack Query (cache, isLoading, error + retry). **Errors:** Toast on API failure (5s); process errors → count + CSV link. **Access:** localhost:5173; backend down → friendly error + retry; ErrorBoundary for render errors. **Bottom bar:** Fixed bottom when jobs exist; list jobs vertically; completed → show 5s then remove; cancelled → orange + "Cancelled"; poll GET /api/jobs/{id} every 2s. Modern browsers.

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

The system SHALL restore visibility of background jobs that were running before page refresh by fetching job state from the backend.

#### Scenario: Fetch active jobs from backend on mount
- **WHEN** Dashboard component mounts
- **THEN** system sends GET request to `/api/jobs` to retrieve all active and recently completed jobs

#### Scenario: Populate background jobs list from backend response
- **WHEN** `/api/jobs` returns list of jobs
- **THEN** system populates backgroundJobs state with job_id, job_type, and start_time for each job

#### Scenario: Skip job restoration if backend returns empty list
- **WHEN** `/api/jobs` returns empty array
- **THEN** system does not display any jobs panel (no jobs to restore)

#### Scenario: Handle job restoration API errors gracefully
- **WHEN** `/api/jobs` request fails
- **THEN** system logs error but continues loading dashboard without blocking UI

### Requirement: Dashboard SHALL display active background jobs in fixed bottom bar

The system SHALL show a fixed bottom bar (not floating pills) when background jobs exist, improving visual alignment with action buttons.

#### Scenario: Show fixed bottom bar for background jobs
- **WHEN** one or more jobs are in backgroundJobs list
- **THEN** system displays a fixed bar anchored to bottom of viewport spanning full width

#### Scenario: Position bottom bar above viewport floor
- **WHEN** bottom bar is visible
- **THEN** system positions it with `fixed bottom-0 left-0 right-0` styling with white background and top border shadow

#### Scenario: Multiple background jobs displayed vertically
- **WHEN** multiple jobs are running
- **THEN** system stacks job entries vertically in the bottom bar (not side-by-side)

#### Scenario: Click to re-open progress modal
- **WHEN** user clicks a job entry in the bottom bar
- **THEN** system re-opens the progress modal for that job with current progress state

#### Scenario: Auto-remove completed jobs
- **WHEN** a background job completes (success, error, or cancelled)
- **THEN** system shows completion status briefly (5 seconds) then removes it from the bottom bar

#### Scenario: Display cancelled job in bottom bar
- **WHEN** a background job is cancelled
- **THEN** system shows orange background with cancel icon and "Cancelled" label

#### Scenario: Job progress via polling
- **WHEN** a job is displayed in the bottom bar
- **THEN** system polls GET `/api/jobs/{id}` every 2 seconds to update progress percentage and status

#### Scenario: Hide bottom bar when no jobs exist
- **WHEN** backgroundJobs list is empty
- **THEN** system does not render the bottom bar (conditional rendering)

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

### Requirement: Main content SHALL not be covered by the jobs bar

When one or more background jobs are shown in the fixed bottom jobs bar, the main content area (stats, filters, card table, and pagination controls) SHALL be adjusted so that the jobs bar does not overlap it. The user SHALL always be able to see the bottom of the card table and the pagination controls (e.g. next/previous) without them being covered by the bar, whether one job or multiple jobs are displayed.

#### Scenario: Table and pagination visible with one job
- **WHEN** at least one job is active and the jobs bar is visible at the bottom
- **THEN** the main content has sufficient bottom spacing (or equivalent layout) so that the end of the card table and the pagination controls remain visible above the bar

#### Scenario: Table and pagination visible with multiple jobs
- **WHEN** two or more jobs are active and the jobs bar grows in height
- **THEN** the main content adjusts so that the card table end and pagination controls remain visible and are not covered by the bar

#### Scenario: No overlap when scrolling to bottom
- **WHEN** the user scrolls to the bottom of the dashboard while jobs are active
- **THEN** the last row of the table and the pagination controls are fully visible and not obscured by the jobs bar

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
