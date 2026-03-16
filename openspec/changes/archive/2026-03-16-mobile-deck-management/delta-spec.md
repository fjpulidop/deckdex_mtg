# Delta Spec: deck-builder-ui

This file records the changes to `openspec/specs/deck-builder-ui/spec.md` introduced by the mobile-deck-management change. All existing requirements remain valid; the additions below extend them with mobile-specific behaviour.

---

## ADDED Requirement: Touch-optimized tap targets across all deck UI

All interactive elements in the deck builder UI (deck grid tiles, card rows, action buttons, picker rows) SHALL have a minimum touch target size of 44 × 44 px on mobile viewports (viewport width < 768 px). This applies to:

- Deck grid tiles: minimum height 100 px.
- Card rows in `DeckDetailModal`: minimum row height 44 px.
- Card rows in `DeckCardPickerModal`: minimum row height 44 px.
- Action buttons: minimum height 44 px.

### Scenario: Card row is reachable by thumb

- **WHEN** the user views the deck detail modal on a mobile viewport (< 768 px)
- **THEN** each card row is tall enough to tap reliably without zooming (minimum 44 px height)

---

## ADDED Requirement: Full-screen modals on mobile viewports

The `DeckDetailModal`, `DeckCardPickerModal`, and `DeckImportModal` SHALL each display as full-screen overlays (no overlay padding, panel fills the viewport entirely, no rounded corners) when the viewport width is below 768 px. On viewports 768 px and above, the existing modal layout (max-width, rounded corners, overlay backdrop) is preserved unchanged.

### Scenario: Detail modal fills screen on phone

- **WHEN** the user opens a deck on a viewport narrower than 768 px
- **THEN** the deck detail modal fills the entire screen with no visible outer overlay padding

### Scenario: Picker modal fills screen on phone

- **WHEN** the user opens the card picker on a viewport narrower than 768 px
- **THEN** the card picker modal fills the entire screen

---

## ADDED Requirement: Mobile sticky action bar in DeckDetailModal

On viewports narrower than 768 px, the deck detail modal SHALL render a sticky action bar fixed to the bottom of the screen containing the primary actions: Add card, Export, Import, Delete deck. This bar SHALL be hidden on viewports 768 px and above, where the existing header row action buttons are used. Each button in the bar SHALL meet the 44 px minimum height requirement. The Delete button SHALL retain a destructive visual treatment (e.g. red colour). The bar SHALL account for the device safe-area-inset-bottom (notched phones) so the home indicator does not overlap buttons.

### Scenario: Action bar visible on mobile

- **WHEN** the user opens a deck detail modal on a viewport narrower than 768 px
- **THEN** a sticky bar at the bottom of the screen shows Add card, Export, Import, and Delete deck buttons, each at minimum 44 px tall

### Scenario: Action bar hidden on desktop

- **WHEN** the user opens a deck detail modal on a viewport 768 px or wider
- **THEN** the sticky action bar is not visible; action buttons appear in the header row as before

---

## ADDED Requirement: Image panel hidden on mobile in DeckDetailModal

On viewports narrower than 768 px, the left image preview panel in the deck detail modal SHALL be hidden to maximise the card list area. The mana curve and total value SHALL remain visible in the header.

### Scenario: Image panel hidden on narrow viewport

- **WHEN** the user opens a deck detail modal on a viewport narrower than 768 px
- **THEN** the large card image panel is not displayed; the full width is used for the card list

---

## ADDED Requirement: Swipe-to-remove gesture on card rows

On touch/stylus input devices (pointer type is not mouse), swiping a card row in the deck detail modal at least 72 px to the left SHALL trigger a remove action for that card. During the swipe, a red "Remove" affordance SHALL be revealed behind the row. On mouse pointer devices, this gesture is inactive; the existing hover-reveal remove button is used instead.

### Scenario: Swipe removes card on touch device

- **WHEN** the user swipes a card row at least 72 px to the left on a touch device and releases
- **THEN** the card is removed from the deck (same outcome as clicking the remove button)

### Scenario: Partial swipe snaps back

- **WHEN** the user swipes a card row less than 72 px and releases
- **THEN** the row returns to its original position and no removal occurs

### Scenario: Swipe does not activate on mouse

- **WHEN** a mouse user interacts with card rows
- **THEN** swipe-to-remove is inactive; only the existing hover remove button is shown

---

## MODIFIED Requirement: Remove card from deck (existing, extended)

The existing requirement ("the user SHALL be able to remove a card from the deck") is extended as follows:

- On mouse/pointer devices: the per-row remove button is revealed on hover (existing behaviour preserved).
- On touch devices with viewport < 768 px: the remove button is always visible on each row (not hidden behind `opacity-0 group-hover`), in addition to the swipe-to-remove gesture.

### Scenario: Remove button always visible on mobile

- **WHEN** the user views the deck detail modal on a touch device with viewport < 768 px
- **THEN** the remove button on each card row is always visible (not dependent on hover state)

---

## ADDED Requirement: DeckCardPickerModal — full-width confirm button on mobile

On viewports narrower than 768 px, the "Add to Deck" confirm button in the card picker footer SHALL be full-width. On wider viewports, the existing right-aligned button width is preserved.

### Scenario: Full-width add button on mobile

- **WHEN** the user views the card picker on a viewport narrower than 768 px
- **THEN** the "Add to Deck" button spans the full footer width for easy thumb access
