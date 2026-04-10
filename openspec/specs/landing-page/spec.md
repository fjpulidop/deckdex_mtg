# Landing Page

### Requirement: Hero section shows bilingual app description card
The landing page Hero section SHALL display an inline bilingual description card in the right column, rendered in both English and Spanish simultaneously, instead of a static dashboard screenshot image. The card SHALL communicate what DeckDex does through a short title, a set of feature bullets, and a tagline.

#### Scenario: Hero description card renders
- **WHEN** a visitor loads the landing page (`/`)
- **THEN** the Hero right column SHALL render a styled card containing two side-by-side panels: one in English and one in Spanish
- **AND** no `<img>` element referencing `dashboard-preview.png` SHALL be present in the Hero

#### Scenario: Hero description card content
- **WHEN** the bilingual card is rendered
- **THEN** the English panel SHALL display the title, four feature bullets, and a tagline sourced from `hero.descCard.*` keys in `en.json`
- **AND** the Spanish panel SHALL display the same structure sourced from `hero.descCard.*` keys in `es.json`
- **AND** both panels SHALL be visible simultaneously regardless of the active application locale

#### Scenario: Hero image fallback removed
- **WHEN** a visitor loads the landing page
- **THEN** there SHALL be no `onError` image fallback mechanism in the Hero component
- **AND** the `frontend/public/dashboard-preview.png` file is no longer required by the landing page

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

### Requirement: CardMatrix animated background visible through landing sections
The CardMatrix animated canvas background SHALL be visually perceptible behind the Hero, BentoGrid, FinalCTA, and Footer sections of the landing page. No landing section element SHALL carry a fully-opaque background color that occludes the canvas.

#### Scenario: Canvas visible through Landing wrapper
- **WHEN** a visitor loads the landing page
- **THEN** the `Landing` page wrapper div SHALL have no background-color or background-gradient Tailwind class
- **AND** the CardMatrix canvas SHALL be visible through the transparent wrapper

#### Scenario: Hero section uses a transparent or semi-transparent background
- **WHEN** a visitor loads the landing page `/`
- **THEN** the Hero `<section>` element SHALL NOT carry any Tailwind background class that resolves to a solid color at 100% opacity (e.g., `bg-dracula-bg` without an opacity modifier)
- **AND** if a background tint is applied, it SHALL use an opacity modifier of `/20` or lower (e.g., `bg-dracula-bg/20` or a gradient from `dracula-bg/20` to `transparent`)
- **AND** the falling mana symbols from the CardMatrix canvas SHALL be visually perceptible through the Hero section background

#### Scenario: FinalCTA gradient uses opacity-modified stops
- **WHEN** a visitor views the FinalCTA section
- **THEN** the gradient background on the FinalCTA `<section>` SHALL use opacity-modified Tailwind color stops on all solid-color gradient steps (e.g., `from-dracula-bg/80`, `to-dracula-bg/80`)
- **AND** no gradient stop SHALL resolve to a fully-opaque solid color

#### Scenario: BentoGrid and Footer already comply
- **WHEN** a visitor views the BentoGrid or Footer sections
- **THEN** the BentoGrid `<section>` background SHALL use `bg-dracula-current/20` (20% opacity) or equivalent semi-transparent value — no change required
- **AND** the Footer `<footer>` background SHALL use `bg-dracula-bg/80` (80% opacity) or equivalent — no change required

#### Scenario: Body background provides solid fallback
- **WHEN** all landing section backgrounds are semi-transparent or transparent
- **THEN** the `body` element's `background-color: #282a36` (set in `index.css`) SHALL serve as the solid dark fallback
- **AND** no white flash or unexpected color SHALL appear in the absence of a section-level solid background

#### Scenario: Canvas visible under reduced motion
- **WHEN** `prefers-reduced-motion: reduce` is active
- **THEN** the CardMatrix SHALL render a single static frame (unchanged from existing behavior)
- **AND** the static frame SHALL still be visible through the transparent Hero section background

#### Scenario: Hero text remains readable
- **WHEN** the CardMatrix background is visible
- **THEN** the Hero headline, subtitle, and CTA buttons SHALL remain clearly readable against the background
- **AND** the reduced-opacity tint on the Hero section SHALL ensure sufficient contrast

### Requirement: Locale keys for Hero description card
The locale files SHALL include a `hero.descCard` key group in both `en.json` and `es.json` covering the title, feature bullets, and tagline displayed in the bilingual Hero card.

#### Scenario: English keys present
- **WHEN** `frontend/src/locales/en.json` is loaded
- **THEN** the following keys SHALL be defined: `hero.descCard.title`, `hero.descCard.feature1`, `hero.descCard.feature2`, `hero.descCard.feature3`, `hero.descCard.feature4`, `hero.descCard.tagline`

#### Scenario: Spanish keys present
- **WHEN** `frontend/src/locales/es.json` is loaded
- **THEN** the same six `hero.descCard.*` keys SHALL be present with Spanish translations

### Requirement: No dead code in landing components
The landing page module SHALL NOT contain unused components.

### Requirement: No debug artifacts in public directory
The `frontend/public/` directory SHALL NOT contain debug image files.
