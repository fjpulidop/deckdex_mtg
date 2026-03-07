# Deck Builder UI — Delta Spec (Refinement)

This delta adds explicit acceptance criteria to the existing `openspec/specs/deck-builder-ui/spec.md`. All sections below are additions to existing requirements; no existing requirements are removed or modified.

---

## ADDED Acceptance Criteria: Commander image background (Requirement: Grid of decks with add tile)

### Scenario: Deck tile with no commander shows neutral background

- **GIVEN** a deck that has no commander assigned (`commander_card_id` is null)
- **WHEN** the user views the deck grid
- **THEN** that deck's tile renders with a neutral background (`bg-gray-200` in light mode, `bg-gray-700` in dark mode) and no image or dark overlay is rendered

### Scenario: Deck tile with commander shows image even when image fetch is slow

- **GIVEN** a deck that has a commander assigned
- **WHEN** the commander card image has not yet loaded (image hook returns `src: null`)
- **THEN** the tile renders with a neutral background (no broken image, no overlay) until the image resolves

### Scenario: Deck tile dark overlay ensures text contrast

- **GIVEN** a deck tile with a commander card background image rendered
- **WHEN** the user views the deck tile in any theme
- **THEN** a semi-transparent dark overlay (`bg-black/55`) covers the full tile so that the deck name and card count text remain readable against the image

---

## ADDED Acceptance Criteria: Mana curve dark mode (Requirement: Deck detail modal layout and actions)

### Scenario: Mana curve axis ticks inherit dark mode color from parent

- **GIVEN** the deck detail modal is open in dark theme
- **WHEN** the mana curve chart renders
- **THEN** the `XAxis` tick labels resolve their color from the parent element's CSS `color` property (Tailwind `dark:text-gray-200` = `#e5e7eb`), not from SVG default black, so that CMC numbers are clearly visible on the dark background

---

## ADDED Acceptance Criteria: Deck import Commander section header (Requirement: Import deck from text modal)

### Scenario: Import text with Commander section header sets commander flag

- **GIVEN** the user pastes a deck list containing `//Commander` followed by one or more card lines, then one or more cards under `//Mainboard`
- **WHEN** the user submits the import
- **THEN** cards under `//Commander` are imported with `is_commander: true` and appear in the Commander section of the deck detail modal, and cards under `//Mainboard` are imported with `is_commander: false`

### Scenario: Commander section header is case-insensitive

- **GIVEN** the user pastes a deck list with `//COMMANDER` (any casing)
- **WHEN** the user submits the import
- **THEN** cards under that section are treated as commander cards (`is_commander: true`)

### Scenario: Non-Commander section header resets commander flag

- **GIVEN** the user pastes a deck list with `//Commander` cards followed by `//Sideboard` or `//Mainboard` cards
- **WHEN** the user submits the import
- **THEN** cards after the non-Commander section header are imported with `is_commander: false`
