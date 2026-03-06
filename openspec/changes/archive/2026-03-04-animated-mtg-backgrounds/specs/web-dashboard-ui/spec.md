## ADDED Requirements

### Requirement: Animated background on app pages
All authenticated app pages SHALL render the AetherParticles animated background as a fixed, full-viewport decorative layer behind the page content.

#### Scenario: Background present on dashboard
- **WHEN** an authenticated user views the Dashboard
- **THEN** floating WUBRG-colored particles SHALL be visible drifting behind the dashboard content

#### Scenario: Background does not obstruct content
- **WHEN** the AetherParticles background is rendered
- **THEN** all page content (navbar, filters, tables, modals) SHALL render above the background layer
