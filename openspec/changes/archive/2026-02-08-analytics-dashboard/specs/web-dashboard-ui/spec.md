## ADDED Requirements

### Requirement: Navigation SHALL include link to Analytics (beta)

The system SHALL provide a navigation link labeled "Analytics (beta)" that is visible in the same area as the Settings link (e.g. header of the main dashboard or shared app header). The link SHALL route to `/analytics`. The link SHALL be present on the main dashboard view so users can reach Analytics without going to Settings first.

#### Scenario: Analytics link visible next to Settings
- **WHEN** user is on the Dashboard (home) page
- **THEN** the header (or equivalent nav) displays both "Settings" and "Analytics (beta)" links in the same region (e.g. side by side or in the same group)

#### Scenario: Analytics link navigates to Analytics page
- **WHEN** user clicks "Analytics (beta)"
- **THEN** application navigates to route `/analytics` and displays the Analytics dashboard page as defined in the analytics-dashboard spec

### Requirement: Analytics page SHALL be a dedicated route and page

The application SHALL register route `/analytics` and SHALL render a dedicated Analytics page component that implements the analytics dashboard (KPIs, charts, drill-down, empty/loading/error states) per the analytics-dashboard spec. The page SHALL be responsive and SHALL use the same theme (light/dark) and styling conventions as the rest of the web dashboard.

#### Scenario: Route /analytics renders Analytics page
- **WHEN** user navigates to `/analytics` (via link or URL)
- **THEN** the application renders the Analytics page; no other page content (e.g. main card table) is shown

#### Scenario: Analytics page is responsive and themed
- **WHEN** user views the Analytics page
- **THEN** layout adapts to viewport size and uses the same light/dark theme as the rest of the app (e.g. ThemeContext or equivalent)
