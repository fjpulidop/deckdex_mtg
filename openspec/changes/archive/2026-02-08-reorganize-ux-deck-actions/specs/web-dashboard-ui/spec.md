# Web Dashboard UI (delta: reorganize-ux-deck-actions)

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Dashboard SHALL restore active jobs on page load

**Replaced by global-jobs-ui:** The application SHALL restore visibility of background jobs once at app (or global provider) mount, not when the Dashboard mounts. Dashboard SHALL NOT perform its own GET `/api/jobs` for job restore; job restore SHALL be the responsibility of the global jobs UI (see global-jobs-ui spec).

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

## REMOVED Requirements

### Requirement: Dashboard SHALL show Process Cards and Update Prices in an Actions block

**Reason:** Deck actions (Process Cards, Update Prices) are moved to Settings under "Deck Actions" to reduce dashboard clutter and group them with configuration.

**Migration:** Use Settings → Deck Actions to start Process Cards or Update Prices. The jobs bar remains visible app-wide so progress can be seen from any page.
