## ADDED Requirements

### Requirement: AetherParticles background renders on app pages
The app SHALL render an AetherParticles animated background on all authenticated pages (dashboard, settings, analytics, decks, import, admin) and the demo page.

#### Scenario: Particles visible on dashboard
- **WHEN** an authenticated user navigates to /dashboard
- **THEN** floating particles in WUBRG mana colors SHALL be visible behind the page content
- **THEN** the particles SHALL drift slowly across the viewport

#### Scenario: Particles visible on other app pages
- **WHEN** an authenticated user navigates to /settings, /analytics, /decks, /import, or /admin
- **THEN** the AetherParticles background SHALL be rendered behind page content

#### Scenario: Particles do not appear on landing or login
- **WHEN** a visitor views the landing page (/) or login page (/login)
- **THEN** the AetherParticles background SHALL NOT be rendered

### Requirement: CardMatrix background renders on landing page
The landing page SHALL render a CardMatrix animated background showing mana symbols slowly falling.

#### Scenario: Mana symbols visible on landing
- **WHEN** a visitor loads the landing page (/)
- **THEN** mana symbols ({W}, {U}, {B}, {R}, {G}, {T}, {X}) SHALL fall slowly in columns behind the page content
- **THEN** each symbol SHALL be colored according to its mana type

#### Scenario: CardMatrix does not appear on app pages
- **WHEN** a user navigates to /dashboard or any other authenticated route
- **THEN** the CardMatrix background SHALL NOT be rendered

### Requirement: Backgrounds respect light and dark theme
Both background components SHALL adapt their appearance based on the current theme.

#### Scenario: Dark mode appearance
- **WHEN** the theme is set to dark
- **THEN** particles and symbols SHALL use brighter, more luminous WUBRG colors
- **THEN** maximum opacity SHALL be approximately 0.3

#### Scenario: Light mode appearance
- **WHEN** the theme is set to light
- **THEN** particles and symbols SHALL use muted, desaturated WUBRG colors
- **THEN** maximum opacity SHALL be approximately 0.15

### Requirement: Backgrounds respect reduced motion preference
Both background components SHALL honor the user's `prefers-reduced-motion` system setting.

#### Scenario: Reduced motion enabled
- **WHEN** the user's OS has `prefers-reduced-motion: reduce` enabled
- **THEN** both background components SHALL render a single static frame without animation

#### Scenario: Reduced motion not set
- **WHEN** the user has no reduced motion preference
- **THEN** backgrounds SHALL animate normally

### Requirement: Backgrounds do not interfere with interaction
Both background components SHALL be purely decorative and not block user interaction.

#### Scenario: Click-through to content
- **WHEN** a user clicks anywhere on the page
- **THEN** the click SHALL pass through the background canvas to the underlying content
- **THEN** the background canvas SHALL have `pointer-events: none`

### Requirement: Background rendering is performant
Both background components SHALL maintain smooth performance without impacting app responsiveness.

#### Scenario: Frame rate is capped
- **WHEN** the background animation is running
- **THEN** the animation loop SHALL be capped at 30 FPS maximum

#### Scenario: Canvas resizes with viewport
- **WHEN** the browser window is resized
- **THEN** the canvas SHALL resize to match the new viewport dimensions
- **THEN** the resize SHALL be debounced to avoid excessive redraws
