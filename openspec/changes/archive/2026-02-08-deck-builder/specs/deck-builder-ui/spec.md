# Deck Builder UI

New dashboard page for Commander-style decks (alpha): grid of decks, deck detail modal with sections and big image + hover swap, Delete and Add (card picker from collection).

## ADDED Requirements

### Requirement: New Decks page and nav link

The system SHALL provide a new page (e.g. route /decks or /commander) and a nav link in the header next to Analytics, labeled so users recognize it as the deck builder (e.g. "Commander" or "Decks"). The link SHALL show an "alpha" badge. The page SHALL be the main deck-builder view.

#### Scenario: User opens Decks page from nav

- **WHEN** the user clicks the Decks/Commander link in the header
- **THEN** the app navigates to the deck-builder route and displays the deck-builder view (grid and "+" tile)

#### Scenario: Alpha badge visible

- **WHEN** the user views the header
- **THEN** the Decks/Commander link displays an "alpha" badge (e.g. small label or pill)

### Requirement: Grid of decks with add tile

The deck-builder page SHALL display a grid of items. The first grid cell SHALL be a fixed "+" (add deck) tile; the remaining cells SHALL be one per existing deck (deck name; optional commander or card count). Tile size SHALL be roughly half the size of the dashboard stat cards (e.g. Total Cards). Clicking the "+" tile SHALL create a new deck (e.g. prompt for name or open empty deck modal); clicking a deck tile SHALL open the deck detail modal for that deck. When a deck has a commander, the deck tile SHALL use the commander card image as the full-tile background (top-aligned) with a uniform dark overlay so the deck name and text remain readable; when there is no commander, the tile SHALL use a neutral background.

#### Scenario: Deck tile with commander background

- **WHEN** a deck has a commander and the user views the deck grid
- **THEN** that deck's tile shows the commander card image as background with a dark overlay and readable text (e.g. deck name)

#### Scenario: Click plus to add deck

- **WHEN** the user clicks the "+" tile
- **THEN** the system creates a new deck (after name input if required) and either opens the deck detail modal for it or refreshes the grid so the new deck appears

#### Scenario: Click deck to open detail

- **WHEN** the user clicks a deck tile (not the "+")
- **THEN** the deck detail modal opens for that deck

### Requirement: Deck detail modal layout and actions

The deck detail modal SHALL list all cards in the deck grouped by section (e.g. Commander, Creatures, Sorceries, Instants, Enchantments, Artifacts, Planeswalkers, Lands, Other) derived from card type. The modal header SHALL be a single row containing: deck title, total deck value (e.g. €), mana curve chart, optional CMC filter chip when active, "Add card" button, and "Delete Deck" button. The modal SHALL show a large image area: by default the commander (or first card) image; when the user hovers over a card in the list, the large image SHALL switch to that card's image. The modal SHALL include a "Delete" button that deletes the deck and closes the modal. The modal SHALL include an "Add" button that opens a second modal (card picker) to select cards from the current collection to add to the deck. In dark theme, the mana curve chart axis labels SHALL be readable (e.g. light colour).

#### Scenario: Header in one row

- **WHEN** the user opens the deck detail modal
- **THEN** the header shows in one row: title, total value, mana curve, CMC chip (if used), Add card, Delete Deck

#### Scenario: Mana curve readable in dark mode

- **WHEN** the user views the deck detail modal in dark theme
- **THEN** the mana curve chart axis labels (CMC numbers) are visible (e.g. light text)

#### Scenario: Sections displayed by type

- **WHEN** the deck detail modal is open and the deck has cards
- **THEN** cards are grouped and displayed in sections (e.g. Commander, Creatures, Sorceries, etc.) according to card type

#### Scenario: Hover swaps big image

- **WHEN** the user hovers over a card row in the deck detail modal
- **THEN** the large image area updates to show that card's image (using the existing card image API by id)

#### Scenario: Delete deck from modal

- **WHEN** the user clicks the "Delete" button in the deck detail modal
- **THEN** the deck is deleted via the API, the modal closes, and the grid refreshes (deck no longer shown)

#### Scenario: Add opens card picker

- **WHEN** the user clicks the "Add" button in the deck detail modal
- **THEN** a second modal (card picker) opens on top, allowing the user to search/select cards from the collection to add to the deck

### Requirement: Card picker modal from collection

The card picker modal SHALL allow the user to select cards from the current collection (same data as Dashboard: GET /api/cards with optional search/filters). The user SHALL be able to filter by card type (e.g. Any, Creature, Instant, Sorcery, Enchantment, Artifact, Planeswalker, Land) and by colour identity (WUBRG mana symbols, toggle; cursor pointer). The list SHALL support sort by: Name, Mana cost (low to high), Mana cost (high to low). Each row SHALL show the card name, type line when present, and the mana cost with mana symbol icons (ManaText) on the right. The user SHALL be able to select one or more cards and confirm; on confirm, the selected cards SHALL be added to the current deck via the deck API and the picker SHALL close. The picker SHALL have a way to close/cancel without adding (e.g. Cancel button or Escape).

#### Scenario: Filter by type and colour

- **WHEN** the user sets a type filter (e.g. Creature) or toggles one or more colour symbols in the picker
- **THEN** the list shows only cards matching the type (substring) and having all selected colours in colour identity

#### Scenario: Sort by mana cost

- **WHEN** the user selects "Mana cost (low to high)" or "Mana cost (high to low)" in the picker
- **THEN** the list is ordered by converted mana cost accordingly

#### Scenario: Row shows mana cost with icons

- **WHEN** the user views the card list in the picker
- **THEN** each row shows the card name (and type when present) and the mana cost with mana symbol icons on the right

#### Scenario: Select and add cards

- **WHEN** the user selects one or more cards in the picker and confirms (e.g. "Add" or "Confirm")
- **THEN** the system calls the API to add those cards to the deck, closes the picker, and the deck detail modal shows the updated list

#### Scenario: Cancel picker

- **WHEN** the user cancels or closes the card picker (e.g. Cancel, Escape)
- **THEN** the picker closes and no cards are added; the deck detail modal remains open

### Requirement: Remove card from deck and edit deck name

The deck detail view SHALL allow the user to remove a card from the deck (e.g. per-row remove or context action). The deck SHALL support editing its name (e.g. inline edit or a name field in the modal); the system SHALL persist the name change via PATCH /api/decks/{id}.

#### Scenario: Remove card from deck

- **WHEN** the user triggers remove for a card in the deck detail modal
- **THEN** the system calls the API to remove that card from the deck and updates the modal list

#### Scenario: Edit deck name

- **WHEN** the user changes the deck name (e.g. in an input in the modal) and confirms
- **THEN** the system calls PATCH /api/decks/{id} with the new name and the UI reflects the updated name (e.g. in modal title and grid)

### Requirement: Set as Commander for legendary creatures

For cards in the deck that are legendary creatures (type contains "Legendary" and "Creature"), the deck detail view SHALL offer a "Set as Commander" action. When the user selects it, that card SHALL become the deck commander (and any previous commander SHALL be unset). The system SHALL persist this via the deck API (e.g. PATCH deck card is_commander).

#### Scenario: Set legendary creature as commander

- **WHEN** the user triggers "Set as Commander" on a legendary creature in the deck detail modal
- **THEN** the system sets that card as commander (and unsets any other), persists via API, and the UI updates (Commander section, big image default)

### Requirement: Card detail from deck (same as Dashboard)

When viewing a deck, the user SHALL be able to open the full card detail modal for any card in the list, using the same component and options as on the main Dashboard (view details, edit, update price, delete, etc.). Opening a card from the deck list SHALL not remove it from the deck unless the user deletes the card from the collection in that modal.

#### Scenario: Open card detail from deck list

- **WHEN** the user clicks a card row in the deck detail modal (e.g. to view details)
- **THEN** the same card detail modal as on the Dashboard opens (with image, price, edit, update price, delete, etc.)

### Requirement: Deck list row: quantity, name, mana cost with icons

In the deck detail modal, each card row SHALL display: quantity (number of identical copies) to the left of the card name; the card name; and the mana cost with mana symbols (icons) to the right of the name. Quantity SHALL only be shown when greater than one (or always as a number to the left of the name).

#### Scenario: Row shows quantity and mana cost

- **WHEN** the deck detail modal lists cards
- **THEN** each row shows quantity (e.g. "2" or "1") to the left of the name, the card name, and the mana cost with symbol icons to the right

### Requirement: Hover shows image and price

When the user hovers over a card row in the deck detail modal, the large preview area SHALL show that card's image and, directly below the image, the card's price (e.g. €X.XX or N/A).

#### Scenario: Hover shows image and price

- **WHEN** the user hovers over a card row in the deck detail modal
- **THEN** the large preview area shows that card's image and the card's price displayed below the image
