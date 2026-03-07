## MODIFIED Requirements

### Requirement: All modals use AccessibleModal
Every modal dialog in the application SHALL use `AccessibleModal` as its outermost wrapper. The following modals SHALL use `AccessibleModal`:
- CardFormModal
- CardDetailModal
- SettingsModal
- ProfileModal
- DeckDetailModal
- DeckCardPickerModal
- DeckImportModal
- ImportListModal
- JobLogModal
- ConfirmModal

#### Scenario: CardFormModal has dialog semantics
- **WHEN** the add/edit card modal is open
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`

#### Scenario: DeckDetailModal has dialog semantics
- **WHEN** the deck detail modal is open
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`

#### Scenario: SettingsModal has dialog semantics
- **WHEN** the settings modal is open
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`

#### Scenario: ConfirmModal has dialog semantics
- **WHEN** a confirmation modal is open
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`
- **THEN** the overlay element SHALL have `aria-labelledby` pointing to the modal title heading id
- **THEN** Tab focus SHALL be trapped within the modal panel
- **THEN** pressing Escape SHALL call `onCancel`
- **THEN** clicking the overlay background SHALL call `onCancel`
- **THEN** `document.body` SHALL have `overflow: hidden` while the modal is open
- **THEN** focus SHALL be restored to the triggering element when the modal closes

## ADDED Requirements

### Requirement: ConfirmModal prompt label/input association
When `ConfirmModal` renders a prompt input (i.e., `promptLabel` prop is provided), the `<label>` SHALL have `htmlFor="confirm-modal-prompt"` and the `<input>` SHALL have `id="confirm-modal-prompt"`.

#### Scenario: Clicking the prompt label focuses the input
- **WHEN** `ConfirmModal` is open with a `promptLabel`
- **AND** the user clicks the label text
- **THEN** focus SHALL move to the prompt `<input>`

### Requirement: DeckCardPickerModal search input label
The `DeckCardPickerModal` search input SHALL have an `aria-label` attribute that describes its purpose in the user's current language.

#### Scenario: Search input is announced by screen readers
- **WHEN** a screen reader user focuses the search input in `DeckCardPickerModal`
- **THEN** the screen reader SHALL announce a label equivalent to "Search cards" (locale-appropriate)

### Requirement: Job status changes announced to screen readers
The `JobsBottomBar` component SHALL include an `aria-live="polite"` region for each active job entry. The region SHALL announce the terminal status of the job (completed, cancelled, failed) when the job finishes.

The region SHALL:
- Be visually hidden (using `sr-only` Tailwind class)
- Have `aria-atomic="true"` so the full status string is announced as a single unit
- Contain the job's status text when `isFinished` is true, and be empty while the job is running
- NOT announce intermediate progress percentages (to avoid noise)

#### Scenario: Job completion announced
- **WHEN** an active job transitions to a finished state (complete, cancelled, or error)
- **THEN** the `aria-live` region SHALL contain the terminal status text
- **THEN** a screen reader SHALL announce the status after its current utterance completes

#### Scenario: Running job is not announced repeatedly
- **WHEN** a job is in progress and its progress percentage updates
- **THEN** the `aria-live` region SHALL remain empty
- **THEN** a screen reader SHALL NOT announce progress tick updates
