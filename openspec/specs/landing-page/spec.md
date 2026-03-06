# Landing Page

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

### Requirement: BentoGrid cards display styled visual content
Each BentoCard SHALL display a styled gradient illustration with a relevant icon instead of raw placeholder text with pixel dimensions. The CardMatrix animated background SHALL be visible behind all landing page sections, providing additional visual depth.

#### Scenario: Visitor sees feature cards
- **WHEN** a visitor views the BentoGrid section on the landing page
- **THEN** each feature card SHALL show a visually styled illustration area with gradient colors and an icon relevant to the feature
- **AND** no raw dimension text (e.g., "600x500px") SHALL be visible

#### Scenario: Animated background visible behind sections
- **WHEN** a visitor loads the landing page
- **THEN** the CardMatrix animated background SHALL be visible behind the Hero, BentoGrid, FinalCTA, and Footer sections
- **THEN** the existing gradient styling of the landing page SHALL remain as the base layer beneath the animated background

### Requirement: GitHub links use correct repository URL
All GitHub links in the landing page SHALL point to the actual repository (`fjpulidop/deckdex-mtg`).

#### Scenario: BentoGrid contribute links
- **WHEN** a visitor views the BentoGrid section
- **THEN** the "fork" and "pull requests" links SHALL point to `https://github.com/fjpulidop/deckdex-mtg/fork` and `https://github.com/fjpulidop/deckdex-mtg/pulls` respectively

#### Scenario: FinalCTA contribute link
- **WHEN** a visitor views the FinalCTA section
- **THEN** the GitHub link SHALL point to `https://github.com/fjpulidop/deckdex-mtg`

### Requirement: No dead code in landing components
The landing page module SHALL NOT contain unused components.

### Requirement: No debug artifacts in public directory
The `frontend/public/` directory SHALL NOT contain debug image files.
