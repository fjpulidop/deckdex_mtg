## MODIFIED Requirements

### Requirement: Logo navigates to home
The navbar logo/title SHALL be clickable and navigate to the Dashboard (home page). The logo area SHALL display "DeckDex" as the primary branding with a subtle "MTG" suffix or tagline to replace the subtitle previously shown on the Dashboard page.

#### Scenario: Logo click returns user to Dashboard
- **WHEN** user is on the Settings page
- **THEN** user clicks the "DeckDex" logo/title
- **THEN** the application navigates to the Dashboard page (path: `/`)

#### Scenario: Navbar shows app identity
- **WHEN** the navbar is rendered on any page
- **THEN** the logo area SHALL display "DeckDex" as the primary text
- **THEN** a subtle "MTG" text or tagline SHALL be visible near the logo to convey the app's purpose
- **THEN** the Dashboard page SHALL NOT display its own title or subtitle
