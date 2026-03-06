## ADDED Requirements

### Requirement: Error messages have role="alert"
All error message containers in the frontend SHALL have `role="alert"` so screen readers automatically announce them when they appear. This applies to all inline error divs in:
- CardFormModal
- SettingsModal
- ProfileModal
- DeckImportModal
- ImportListModal
- DeckBuilder createError
- Dashboard error state

#### Scenario: Form error is announced
- **WHEN** a form submission fails and an error message div appears
- **THEN** the error container SHALL have `role="alert"` so assistive technology announces it

### Requirement: Icon-only buttons have aria-label
All buttons that display only an icon (no visible text) SHALL have an `aria-label` attribute describing their action. Affected buttons include:
- Close (X) buttons in all modals (CardFormModal, CardDetailModal, SettingsModal, ProfileModal, DeckDetailModal, DeckCardPickerModal, DeckImportModal, ImportListModal, JobLogModal)
- Avatar/photo upload button in ProfileModal
- Footer social link icons (landing page)

#### Scenario: Close button is accessible
- **WHEN** a modal close button contains only an icon
- **THEN** the button SHALL have an `aria-label` (e.g., "Close") describing its action

### Requirement: Form label/input associations
All `<label>` elements in forms SHALL be associated with their corresponding `<input>`, `<select>`, or `<textarea>` elements via `htmlFor`/`id` pairs. This applies to all form fields in:
- CardFormModal (name, type, rarity, price, set fields)
- CardDetailModal edit form
- ProfileModal (display name)
- SettingsModal fields
- Filters (search, price min/max, rarity, type, set)

#### Scenario: Clicking label focuses input
- **WHEN** a user clicks a label text in a form
- **THEN** focus SHALL move to the associated input element

### Requirement: CardTable sortable headers are keyboard-accessible
Sortable column headers in CardTable SHALL be operable via keyboard and SHALL communicate sort state to assistive technology.

Each sortable `<th>` element SHALL:
- Have `tabIndex={0}` to be reachable via Tab
- Have `onKeyDown` handler that triggers sort on Enter or Space
- Have `aria-sort="ascending"`, `aria-sort="descending"`, or `aria-sort="none"` reflecting current sort state

#### Scenario: Keyboard user sorts table
- **WHEN** a sortable column header is focused and the user presses Enter or Space
- **THEN** the table SHALL sort by that column (same behaviour as clicking)

#### Scenario: Sort direction is communicated
- **WHEN** a column is sorted ascending
- **THEN** the column header SHALL have `aria-sort="ascending"`
- **WHEN** a column is sorted descending
- **THEN** the column header SHALL have `aria-sort="descending"`
- **WHEN** a column is not the current sort column
- **THEN** the column header SHALL have `aria-sort="none"`

### Requirement: QuantityCell is keyboard-accessible
The QuantityCell component in CardTable SHALL allow keyboard users to enter quantity edit mode. The quantity display element SHALL have `tabIndex={0}`, `role="button"`, and an `onKeyDown` handler that activates edit mode on Enter or Space.

#### Scenario: Keyboard user edits quantity
- **WHEN** the quantity display element is focused and the user presses Enter or Space
- **THEN** the component SHALL enter edit mode (same behaviour as clicking)
