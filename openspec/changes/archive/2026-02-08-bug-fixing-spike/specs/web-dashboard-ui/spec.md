## MODIFIED Requirements

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
