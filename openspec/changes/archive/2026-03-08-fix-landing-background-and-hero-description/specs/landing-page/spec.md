## MODIFIED Requirements

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

### Requirement: CardMatrix animated background visible through landing sections
The CardMatrix animated canvas background SHALL be visually perceptible behind the Hero, BentoGrid, FinalCTA, and Footer sections of the landing page. The `Landing` wrapper element SHALL NOT carry a background color or gradient that occludes the canvas.

#### Scenario: Canvas visible through Landing wrapper
- **WHEN** a visitor loads the landing page
- **THEN** the `Landing` page wrapper div SHALL have no background-color or background-gradient Tailwind class
- **AND** the CardMatrix canvas SHALL be visible through the transparent wrapper

#### Scenario: Canvas visible through Hero section
- **WHEN** a visitor views the Hero section
- **THEN** the Hero `<section>` element's background gradient opacity SHALL be at most 20% on slate and 10% on purple
- **AND** the falling mana symbols SHALL be perceptible behind the hero text and card

#### Scenario: Hero text remains readable
- **WHEN** the CardMatrix background is visible
- **THEN** the Hero headline, subtitle, and CTA buttons SHALL remain clearly readable against the background
- **AND** the reduced-opacity tint on the Hero section SHALL ensure sufficient contrast

## ADDED Requirements

### Requirement: Locale keys for Hero description card
The locale files SHALL include a `hero.descCard` key group in both `en.json` and `es.json` covering the title, feature bullets, and tagline displayed in the bilingual Hero card.

#### Scenario: English keys present
- **WHEN** `frontend/src/locales/en.json` is loaded
- **THEN** the following keys SHALL be defined: `hero.descCard.title`, `hero.descCard.feature1`, `hero.descCard.feature2`, `hero.descCard.feature3`, `hero.descCard.feature4`, `hero.descCard.tagline`

#### Scenario: Spanish keys present
- **WHEN** `frontend/src/locales/es.json` is loaded
- **THEN** the same six `hero.descCard.*` keys SHALL be present with Spanish translations
