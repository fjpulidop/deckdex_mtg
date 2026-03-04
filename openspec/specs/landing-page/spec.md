## ADDED Requirements

### Requirement: Hero section shows real dashboard screenshot
The landing page Hero section SHALL display an actual screenshot of the dashboard instead of a gradient placeholder.

#### Scenario: Hero image renders
- **WHEN** a visitor loads the landing page (`/`)
- **THEN** the Hero right column SHALL render an `<img>` element sourced from `/dashboard-preview.png`

#### Scenario: Hero image fallback
- **WHEN** the screenshot file does not exist (e.g., not yet generated)
- **THEN** the Hero SHALL fall back to the gradient placeholder without throwing an error

### Requirement: Live demo CTA in Hero
The Hero section SHALL include a secondary call-to-action link to the public demo route.

#### Scenario: Demo link visible before login
- **WHEN** an unauthenticated visitor views the landing page
- **THEN** a "Try live demo" button SHALL be visible alongside the sign-in button, linking to `/demo`

#### Scenario: Demo link not shown when authenticated
- **WHEN** an authenticated user views the landing page
- **THEN** the "Try live demo" button SHALL NOT be shown; only the "Go to Dashboard" button appears

### Requirement: Live demo CTA in FinalCTA
The FinalCTA section SHALL also include a secondary link to the demo route for visitors who scroll to the bottom without signing in.

#### Scenario: FinalCTA demo link visible before login
- **WHEN** an unauthenticated visitor views the FinalCTA section
- **THEN** a "Try live demo" secondary button SHALL be visible alongside the sign-in button

### Requirement: Footer rendered on landing page
The landing page SHALL render the Footer component.

#### Scenario: Footer visible at bottom of landing
- **WHEN** a visitor loads the landing page
- **THEN** the Footer component SHALL be rendered below the FinalCTA section
