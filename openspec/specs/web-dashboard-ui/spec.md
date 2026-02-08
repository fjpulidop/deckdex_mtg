## ADDED Requirements

### Requirement: Dashboard SHALL display collection overview

The system SHALL provide a dashboard page that visualizes collection statistics in a streamlined 2-column layout without non-persistent temporal metadata.

#### Scenario: Display summary statistics cards in 2-column grid
- **WHEN** user opens dashboard
- **THEN** system displays 2 cards in responsive grid: Total Cards (left) and Total Value (right)

#### Scenario: Display average price as subtitle under Total Value
- **WHEN** Total Value card is rendered
- **THEN** system displays average price in smaller gray text below the total value amount (format: "Avg: €X.XX")

#### Scenario: Statistics auto-refresh every 30 seconds
- **WHEN** user remains on dashboard
- **THEN** system automatically refetches stats every 30 seconds without page reload

#### Scenario: Loading state while fetching data
- **WHEN** dashboard is loading collection data
- **THEN** system displays skeleton loaders for 2 stat cards (not 3)

### ~~Requirement: Dashboard SHALL display price visualization chart~~ REMOVED

Removed from MVP. No local database exists to track historical price snapshots. Google Sheets only stores current values. Displaying mock/placeholder data is misleading. Future: add SQLite to snapshot daily collection totals, then re-introduce chart.

### Requirement: Dashboard SHALL display card collection table

The system SHALL provide a table listing cards in the collection with key metadata.

#### Scenario: Display cards in paginated table
- **WHEN** user views card table
- **THEN** system displays 50 cards per page with name, type, rarity, price, and set

#### Scenario: Navigate between table pages
- **WHEN** user clicks pagination controls
- **THEN** system loads next/previous 50 cards without full page reload

#### Scenario: Sort table by column
- **WHEN** user clicks column header (e.g., Price)
- **THEN** system sorts cards by that column ascending or descending

### Requirement: Dashboard SHALL provide card filtering

The system SHALL allow users to filter the card table by various criteria.

#### Scenario: Filter cards by name search
- **WHEN** user types in search box
- **THEN** system filters cards to show only those matching the search term (case-insensitive)

#### Scenario: Filter by rarity
- **WHEN** user selects rarity filter (e.g., "rare")
- **THEN** system shows only cards of that rarity

#### Scenario: Clear all filters
- **WHEN** user clicks "Clear Filters" button
- **THEN** system resets all filters and shows full collection

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

### Requirement: Dashboard SHALL provide action buttons for processes

The system SHALL allow users to trigger background processes from the UI.

#### Scenario: Trigger process new cards
- **WHEN** user clicks "Process Cards" button
- **THEN** system sends POST to `/api/process` and opens progress modal

#### Scenario: Trigger update prices
- **WHEN** user clicks "Update Prices" button
- **THEN** system sends POST to `/api/prices/update` and opens progress modal

#### Scenario: Disable action buttons during active process
- **WHEN** a process is currently running
- **THEN** system disables process buttons and shows "Processing..." indicator

### Requirement: Dashboard SHALL display progress modal during processes

The system SHALL show a modal with real-time progress when background processes are executing.

#### Scenario: Open modal when process starts
- **WHEN** user triggers a process
- **THEN** system opens modal showing progress bar at 0%, "Connecting..." message

#### Scenario: Update progress bar in real-time
- **WHEN** WebSocket receives progress event
- **THEN** system updates progress bar percentage and "Processing X/Y cards" text

#### Scenario: Display errors as they occur
- **WHEN** WebSocket receives error event
- **THEN** system adds error to scrollable error list in modal showing card name and error message

#### Scenario: Show completion summary
- **WHEN** WebSocket receives complete event
- **THEN** system shows success message with total processed, success count, error count, and duration

#### Scenario: Close modal after completion
- **WHEN** process completes and user clicks "Done"
- **THEN** system closes modal and refetches collection data to show updates

#### Scenario: Stop running job from modal
- **WHEN** user clicks "Stop" button in progress modal while job is running
- **THEN** system sends POST to `/api/jobs/{job_id}/cancel`
- **AND** button shows "Stopping..." disabled state while request is in flight
- **AND** progress bar changes to orange color while cancelling

#### Scenario: Display cancelled state in modal
- **WHEN** WebSocket receives complete event with `status: cancelled`
- **THEN** system shows orange-styled completion message: "Process cancelled — progress was at X/Y cards (Z%)"
- **AND** header changes to "Process Cancelled"

#### Scenario: Stop and Minimize buttons coexist
- **WHEN** job is running and modal is open
- **THEN** system shows red "Stop" button and gray "Minimize" button side by side in footer

#### Scenario: Display elapsed time in modal header
- **WHEN** process modal is open
- **THEN** system displays live elapsed time counter in header (clock icon, monospaced font)
- **AND** timer updates every second while job is running
- **AND** timer freezes at final duration when job completes/cancels/fails
- **AND** elapsed time format is adaptive: "12s", "2m 34s", "1h 5m 12s"

### Requirement: Dashboard SHALL preserve progress on modal reopen

The system SHALL not lose progress state when the user minimizes and re-opens a progress modal.

#### Scenario: Fetch initial progress from REST on modal reopen
- **WHEN** user re-opens a progress modal from the ActiveJobs floating panel
- **THEN** system immediately fetches `GET /api/jobs/{id}` to get current progress
- **AND** uses REST response as initial progress state (no 0% flash)
- **AND** WebSocket events take over for real-time updates once connected

#### Scenario: Handle already-completed job on reopen
- **WHEN** user re-opens modal for a job that finished while minimized
- **THEN** system detects `complete`/`error`/`cancelled` status from REST response
- **AND** immediately shows completion message without waiting for WebSocket

### Requirement: Dashboard SHALL handle WebSocket disconnections

The system SHALL gracefully handle network interruptions during progress tracking.

#### Scenario: Auto-reconnect on disconnect
- **WHEN** WebSocket connection drops during active process
- **THEN** system attempts to reconnect up to 3 times with exponential backoff

#### Scenario: Show connection status
- **WHEN** WebSocket is disconnected
- **THEN** system displays "Reconnecting..." message in progress modal

#### Scenario: Allow manual refresh on connection failure
- **WHEN** reconnection attempts exhausted
- **THEN** system shows "Connection lost" message with "Refresh" button to query job status via REST

### Requirement: Dashboard SHALL use Tailwind CSS v4 for styling

The system SHALL style all UI components using Tailwind CSS v4 utility classes with `@tailwindcss/postcss` plugin.

#### Scenario: Tailwind CSS v4 configuration
- **WHEN** building or serving the frontend
- **THEN** system uses `@import "tailwindcss"` directive in index.css (NOT the v3 `@tailwind base/components/utilities` directives)
- **AND** postcss.config.js references `@tailwindcss/postcss` plugin (NOT `tailwindcss` directly)
- **AND** no `tailwind.config.js` is required (Tailwind v4 auto-detects content)

#### Scenario: Tailwind v4 compatible classes
- **WHEN** applying opacity to background colors
- **THEN** system uses slash syntax (e.g., `bg-black/50`) instead of deprecated `bg-opacity-*` utilities

#### Scenario: Responsive layout on desktop
- **WHEN** user views dashboard on desktop (>1024px width)
- **THEN** system displays grid layout with stats cards in row and chart/table below

#### Scenario: Consistent spacing and colors
- **WHEN** viewing all components
- **THEN** system uses consistent spacing (p-4, gap-4), colors from Tailwind palette, and typography scale

### Requirement: Dashboard SHALL use TanStack Query for data fetching

The system SHALL manage API state using TanStack Query (React Query).

#### Scenario: Cache API responses
- **WHEN** user navigates away from dashboard and returns
- **THEN** system shows cached data immediately while refetching in background

#### Scenario: Handle loading states
- **WHEN** initial data fetch is in progress
- **THEN** TanStack Query provides isLoading state for rendering skeletons

#### Scenario: Handle error states
- **WHEN** API request fails
- **THEN** TanStack Query provides error object for displaying error message with retry button

### Requirement: Dashboard SHALL display error notifications

The system SHALL show user-friendly error messages when operations fail.

#### Scenario: API error notification
- **WHEN** API request returns error status
- **THEN** system displays toast notification with error message and auto-dismisses after 5 seconds

#### Scenario: Failed card lookup notification
- **WHEN** process completes with errors
- **THEN** system shows notification with count of failed cards and link to error CSV

### Requirement: Dashboard SHALL be accessible via browser

The system SHALL be accessible through modern web browsers on localhost.

#### Scenario: Access dashboard via localhost
- **WHEN** user navigates to http://localhost:5173
- **THEN** system loads React application and displays dashboard

#### Scenario: Display error page when backend unavailable
- **WHEN** user opens dashboard and backend API is not running
- **THEN** system displays friendly error page with backend connection instructions and a retry button

#### Scenario: Catch React render errors
- **WHEN** a React component throws an error during rendering
- **THEN** ErrorBoundary catches the error and displays a fallback UI with error details and a refresh button

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

#### Scenario: Support modern browsers
- **WHEN** user accesses with Chrome, Firefox, Edge, or Safari (last 2 versions)
- **THEN** system renders correctly with all features functional
