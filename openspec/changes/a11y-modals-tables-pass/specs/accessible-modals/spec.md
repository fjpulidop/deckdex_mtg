## MODIFIED Requirements

### Requirement: All modals use AccessibleModal
Every modal dialog in the application SHALL use `AccessibleModal` as its outermost wrapper. The following modals SHALL use `AccessibleModal`:
- CardFormModal
- CardDetailModal (main modal and image lightbox)
- SettingsModal
- ProfileModal (main modal and crop sub-modal)
- DeckDetailModal (main modal and image lightbox)
- DeckCardPickerModal
- DeckImportModal
- ImportListModal
- JobLogModal
- ConfirmModal

For nested dialogs (crop sub-modal within `ProfileModal`, lightboxes within `CardDetailModal` and
`DeckDetailModal`), each nested dialog SHALL be wrapped in its own `AccessibleModal` instance.

#### Scenario: ProfileModal crop sub-modal has dialog semantics
- **WHEN** the crop adjustment dialog is open inside `ProfileModal`
- **THEN** it SHALL have `role="dialog"` and `aria-modal="true"`
- **THEN** Tab focus SHALL be trapped within the crop panel
- **THEN** pressing Escape SHALL close the crop dialog only (not the outer `ProfileModal`)
- **THEN** the first focusable element inside the crop panel SHALL receive focus automatically

#### Scenario: CardDetailModal image lightbox has dialog semantics
- **WHEN** the image lightbox overlay is open
- **THEN** it SHALL have `role="dialog"` and `aria-modal="true"`
- **THEN** the dialog SHALL be labelled by a visually hidden title element
- **THEN** Tab focus SHALL be trapped within the lightbox
- **THEN** pressing Escape SHALL close the lightbox
- **THEN** focus SHALL return to the image zoom trigger after the lightbox closes

#### Scenario: DeckDetailModal image lightbox has dialog semantics
- **WHEN** the image lightbox overlay is open inside `DeckDetailModal`
- **THEN** it SHALL have `role="dialog"` and `aria-modal="true"`
- **THEN** the dialog SHALL be labelled by a visually hidden title element
- **THEN** Tab focus SHALL be trapped within the lightbox
- **THEN** pressing Escape SHALL close the lightbox

## ADDED Requirements

### Requirement: DeckCardPickerModal search input label
The `DeckCardPickerModal` search input SHALL have an `aria-label` attribute that describes its
purpose in the user's current language using the i18n key `deckCardPicker.searchLabel`.

#### Scenario: Search input is announced by screen readers
- **WHEN** a screen reader user focuses the search input in `DeckCardPickerModal`
- **THEN** the screen reader SHALL announce a label equivalent to "Search cards" (locale-appropriate)
- **THEN** the label SHALL NOT disappear when the user begins typing

### Requirement: DeckImportModal textarea label
The `DeckImportModal` textarea SHALL have a programmatically associated `<label>` element via
matching `htmlFor` / `id` attributes.

#### Scenario: Textarea is announced with its label
- **WHEN** a screen reader user focuses the deck list textarea in `DeckImportModal`
- **THEN** the screen reader SHALL announce the label text (equivalent to "Deck list")
- **THEN** the label SHALL be visible to sighted users

### Requirement: SettingsModal file inputs have labels
Both file inputs in `SettingsModal` SHALL have programmatically associated labels:
- The Scryfall credentials file input SHALL have a visually-hidden label via `htmlFor` / `id`
- The collection import file input SHALL have a visually-hidden label via `htmlFor` / `id`

#### Scenario: File input is announced with context
- **WHEN** a screen reader user focuses a file input in `SettingsModal`
- **THEN** the screen reader SHALL announce a label describing the file input's purpose
- **THEN** the announcement SHALL not rely solely on the `placeholder` attribute

### Requirement: Image lightbox accessible name
Each image lightbox dialog (`CardDetailModal`, `DeckDetailModal`) SHALL have an accessible name
provided via a visually hidden `<span>` referenced by `aria-labelledby` on the `AccessibleModal`.

The visually hidden span SHALL use the card's name in the label text (e.g., "Card image: Lightning
Bolt") using the i18n key pattern `cardDetail.lightboxTitle` / `deckDetail.lightboxTitle`.

#### Scenario: Lightbox is announced as a labeled dialog
- **WHEN** a screen reader user opens the image lightbox
- **THEN** the screen reader SHALL announce the dialog role and its label (e.g., "Card image:
  Lightning Bolt, dialog")
- **THEN** focus SHALL move to the dismissal button inside the lightbox panel
