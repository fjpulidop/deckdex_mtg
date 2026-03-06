# Accessible Modals

Reusable `AccessibleModal` wrapper component providing full keyboard and screen reader accessibility for all modal dialogs in the DeckDex frontend.

### Requirement: AccessibleModal wrapper component
The system SHALL provide a reusable `AccessibleModal` React component that wraps all modal dialogs in the application, providing full keyboard and screen reader accessibility.

The component SHALL accept these props:
- `isOpen: boolean` — controls visibility
- `onClose: () => void` — called on Escape key or overlay click
- `titleId: string` — `id` of the heading element inside the modal panel (used for `aria-labelledby`)
- `children: React.ReactNode` — the modal panel content
- `className?: string` — optional extra classes for the overlay

The component SHALL:
- Render nothing when `isOpen` is false
- Render a full-screen overlay (`fixed inset-0`) with `role="dialog"`, `aria-modal="true"`, `aria-labelledby={titleId}`
- Close (call `onClose`) when the overlay background is clicked
- Close when the Escape key is pressed
- Trap Tab focus within the modal panel (cycling through all focusable descendants)
- Auto-focus the first focusable element inside the panel when opened
- Restore focus to the previously focused element when closed
- Add `overflow-hidden` to `document.body` while open; restore on close

#### Scenario: Modal is announced as dialog by screen reader
- **WHEN** a modal opens
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`
- **THEN** the overlay element SHALL have `aria-labelledby` pointing to the modal title heading id

#### Scenario: Focus is trapped within the modal
- **WHEN** the modal is open and focus is on the last focusable element inside it
- **THEN** pressing Tab SHALL move focus to the first focusable element inside the modal
- **WHEN** the modal is open and focus is on the first focusable element inside it
- **THEN** pressing Shift+Tab SHALL move focus to the last focusable element inside the modal

#### Scenario: Escape closes the modal
- **WHEN** the modal is open and the user presses Escape
- **THEN** `onClose` SHALL be called

#### Scenario: Overlay click closes the modal
- **WHEN** the modal is open and the user clicks the overlay background (outside the panel)
- **THEN** `onClose` SHALL be called

#### Scenario: Focus auto-moves on open
- **WHEN** a modal opens
- **THEN** focus SHALL automatically move to the first focusable element inside the modal panel

#### Scenario: Focus is restored on close
- **WHEN** a modal closes
- **THEN** focus SHALL return to the element that had focus immediately before the modal opened

### Requirement: All modals use AccessibleModal
Every modal dialog in the application SHALL use `AccessibleModal` as its outermost wrapper. The following modals SHALL be refactored to use `AccessibleModal`:
- CardFormModal
- CardDetailModal
- SettingsModal
- ProfileModal
- DeckDetailModal
- DeckCardPickerModal
- DeckImportModal
- ImportListModal
- JobLogModal

#### Scenario: CardFormModal has dialog semantics
- **WHEN** the add/edit card modal is open
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`

#### Scenario: DeckDetailModal has dialog semantics
- **WHEN** the deck detail modal is open
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`

#### Scenario: SettingsModal has dialog semantics
- **WHEN** the settings modal is open
- **THEN** the overlay element SHALL have `role="dialog"` and `aria-modal="true"`
