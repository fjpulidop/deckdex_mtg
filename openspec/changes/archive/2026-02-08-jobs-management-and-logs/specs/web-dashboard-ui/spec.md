# Web Dashboard UI (delta: jobs-management-and-logs)

## ADDED Requirements

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

Each job entry in the bottom jobs bar SHALL provide a control (e.g. button or link) that opens a modal (or equivalent overlay) dedicated to that job. The modal SHALL display that job’s progress (e.g. percentage, current/total, elapsed time) and log or progress output so the user can see how the job is advancing.

#### Scenario: Open job log modal from bar
- **WHEN** the user activates the “View log” (or equivalent) control on a job in the bottom bar
- **THEN** a modal opens showing that job’s progress and log (or progress and errors) for the selected job

#### Scenario: Modal shows live progress
- **WHEN** the modal is open for a running job
- **THEN** the modal shows up-to-date progress (e.g. percentage, current/total) and any log or error output, updating as the job runs (e.g. via existing WebSocket or polling)

#### Scenario: Modal can be closed
- **WHEN** the user closes the modal (e.g. close button or overlay click)
- **THEN** the modal is dismissed and the user returns to the dashboard view; the job continues in the bar as before
