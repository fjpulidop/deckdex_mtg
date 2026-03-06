## ADDED Requirements

### Requirement: BentoGrid cards display styled visual content
Each BentoCard SHALL display a styled gradient illustration with a relevant icon instead of raw placeholder text with pixel dimensions.

#### Scenario: Visitor sees feature cards
- **WHEN** a visitor views the BentoGrid section on the landing page
- **THEN** each feature card SHALL show a visually styled illustration area with gradient colors and an icon relevant to the feature
- **AND** no raw dimension text (e.g., "600x500px") SHALL be visible

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

#### Scenario: InteractiveDemo removed
- **WHEN** the landing page source is inspected
- **THEN** `InteractiveDemo.tsx` SHALL NOT exist in the `components/landing/` directory

### Requirement: No debug artifacts in public directory
The `frontend/public/` directory SHALL NOT contain debug image files.

#### Scenario: Debug images removed
- **WHEN** the public directory is inspected
- **THEN** `debug-demo.png` and `debug-landing.png` SHALL NOT be present
