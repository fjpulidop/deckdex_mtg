# Global Jobs UI (new capability)

## ADDED Requirements

### Requirement: App SHALL restore active jobs once on load

The application SHALL fetch and restore visibility of background jobs that were running before page refresh exactly once when the app (or the global job state provider) mounts. The restore SHALL use GET `/api/jobs` and SHALL populate the global job list with job_id, job_type, and start_time for jobs that are still running or pending. The restore SHALL NOT be tied to a specific route (e.g. Dashboard); it SHALL run at app level so that jobs are visible regardless of which page the user lands on.

#### Scenario: Restore jobs on app mount
- **WHEN** the application (or global jobs provider) mounts
- **THEN** system sends GET request to `/api/jobs` and populates the global job list with active/pending jobs from the response

#### Scenario: Restore visible regardless of initial route
- **WHEN** user opens the app directly on Settings (or any route other than Dashboard)
- **THEN** system still runs job restore once and displays any active jobs in the global jobs bar

#### Scenario: Handle restore API errors gracefully
- **WHEN** `/api/jobs` request fails during restore
- **THEN** system logs the error and continues without blocking the UI; no jobs are restored

### Requirement: App SHALL display active jobs bar on all main views

The system SHALL show a single fixed bottom bar when one or more background jobs exist. The bar SHALL be rendered at app (or layout) level and SHALL be visible on Dashboard, Settings, and any other top-level view. The bar SHALL list jobs vertically, SHALL allow opening progress/log modal per job, SHALL auto-remove completed jobs after a brief display (e.g. 5 seconds), and SHALL show cancelled state (e.g. orange + "Cancelled"). Job progress SHALL be updated via existing mechanisms (e.g. WebSocket or polling GET `/api/jobs/{id}`).

#### Scenario: Bar visible on Dashboard when jobs exist
- **WHEN** at least one job is in the global job list and user is on Dashboard
- **THEN** the fixed bottom jobs bar is visible at the bottom of the viewport

#### Scenario: Bar visible on Settings when jobs exist
- **WHEN** at least one job is in the global job list and user is on Settings
- **THEN** the fixed bottom jobs bar is visible at the bottom of the viewport

#### Scenario: Single bar instance app-wide
- **WHEN** user navigates from Dashboard to Settings (or vice versa) while jobs are active
- **THEN** the same jobs bar remains visible with the same jobs; no duplicate bar or loss of job state

### Requirement: Main content on all views SHALL not be covered by the jobs bar

When one or more background jobs are shown in the fixed bottom jobs bar, the main content area on every view (Dashboard and Settings) SHALL reserve sufficient bottom space so that the jobs bar does not overlap content. The user SHALL be able to see the full content (e.g. end of card table and pagination on Dashboard, end of Settings sections on Settings) without it being covered by the bar.

#### Scenario: Dashboard content not covered when jobs bar visible
- **WHEN** jobs bar is visible and user is on Dashboard
- **THEN** main content has bottom padding (or equivalent) so the card table and pagination remain fully visible above the bar

#### Scenario: Settings content not covered when jobs bar visible
- **WHEN** jobs bar is visible and user is on Settings
- **THEN** main content has bottom padding (or equivalent) so all Settings sections remain fully visible above the bar
