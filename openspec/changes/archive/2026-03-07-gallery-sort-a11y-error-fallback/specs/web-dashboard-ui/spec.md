# Delta Spec: web-dashboard-ui — Gallery Refinements

Base spec: `openspec/specs/web-dashboard-ui/spec.md`

This delta adds requirements for gallery-specific behaviors only. All existing requirements in the base spec remain in force.

---

## Requirement: Gallery view exposes sort controls

The CardGallery component SHALL render sort controls in its toolbar whenever the `onSortChange` prop is provided. Sort controls SHALL appear on the right side of the toolbar row, separated from action buttons (Add card, Import list, Update Prices).

Sort controls SHALL consist of:
- A labeled `<select>` for choosing the sort column (name, type, rarity, price, Added).
- A toggle `<button>` that cycles between ascending and descending direction, with an `aria-label` that describes the resulting action ("Sort ascending" / "Sort descending").

The sort column options SHALL reuse the same column set as the CardTable view, and SHALL use the existing `cardTable.columns.*` locale keys for option labels.

### Scenario: Gallery sort select changes sort column

- **GIVEN** the gallery view is active and sort controls are rendered
- **WHEN** the user changes the sort column select
- **THEN** the `onSortChange` callback SHALL be called with the new column key and the current sort direction
- **THEN** the gallery SHALL re-render with cards in the new sort order (after parent re-fetch)

### Scenario: Gallery sort direction toggle cycles direction

- **GIVEN** the gallery view is active and sort controls are rendered
- **WHEN** the user clicks the direction toggle button
- **THEN** the `onSortChange` callback SHALL be called with the current column key and the opposite direction
- **THEN** the toggle button `aria-label` SHALL reflect the action that will be taken on the next click

### Scenario: Gallery sort state is shared with table view

- **GIVEN** the user has set sort to "Price descending" in gallery view
- **WHEN** the user switches to table view
- **THEN** the table view SHALL reflect the same sort column and direction

---

## Requirement: Gallery grid has list semantics

The CardGallery grid container SHALL have `role="list"`. Each card tile SHALL be wrapped in an element with `role="listitem"`.

This enables assistive technology to announce the number of items in the grid and allows users to navigate between items using list navigation shortcuts.

### Scenario: Screen reader announces item count

- **GIVEN** the gallery view is active with cards loaded
- **WHEN** a screen reader user focuses into the card grid
- **THEN** the assistive technology SHALL be able to enumerate grid items as a list with a count

---

## Requirement: Image error shows static fallback placeholder

When a card image fails to load, the CardGallery tile SHALL display a static placeholder instead of the loading skeleton animation.

The error placeholder SHALL:
- Be visually distinct from the loading state (no `animate-pulse`)
- Include an icon or visual indicator that the image is unavailable
- Display localized "Image unavailable" text (`cardDetail.imageUnavailable`)
- Not retry the fetch (the error is permanent for the session — `useImageCache` does not retry)

The loading skeleton (animate-pulse) SHALL only be shown when the image is genuinely in-flight (`loading: true`).

### Scenario: Image fetch failure renders static placeholder

- **GIVEN** a card tile whose image fetch returns an error
- **WHEN** the tile is rendered
- **THEN** a static placeholder with "Image unavailable" text SHALL be displayed
- **THEN** the pulsing skeleton animation SHALL NOT be shown

### Scenario: In-flight image renders loading skeleton

- **GIVEN** a card tile whose image is being fetched
- **WHEN** the tile is rendered
- **THEN** the pulsing skeleton animation SHALL be displayed
- **THEN** no error placeholder SHALL be shown

---

## Requirement: Gallery tile shows quantity badge for multi-copy cards

When a card's `quantity` field is greater than 1, the CardGallery tile SHALL display a numeric badge indicating the quantity owned.

The badge SHALL:
- Be positioned in the top-right corner of the tile
- Display the numeric quantity value
- Include an accessible label (`gallery.quantityBadge`) for screen readers
- Be visible at all times once the tile is in the viewport (not dependent on image load state)
- Not be interactive (clicking the badge SHALL have the same effect as clicking the tile — opening the card detail modal)

### Scenario: Multi-copy card shows badge

- **GIVEN** a card with quantity = 3
- **WHEN** the gallery tile is rendered
- **THEN** a badge displaying "3" SHALL be visible in the top-right corner of the tile

### Scenario: Single-copy card shows no badge

- **GIVEN** a card with quantity = 1 (or quantity not set)
- **WHEN** the gallery tile is rendered
- **THEN** no quantity badge SHALL be displayed
