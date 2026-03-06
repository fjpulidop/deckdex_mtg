## MODIFIED Requirements

### Requirement: Import list button in CardTable toolbar
The CardTable toolbar SHALL display an "Import list" button next to the "Add card" button when an import callback is provided. The button SHALL open an Import List modal. The button SHALL use an outline/ghost style (indigo border, transparent background) to communicate secondary importance relative to the primary "Add card" button.

#### Scenario: Import list button visible on dashboard
- **WHEN** the user views the Dashboard with the CardTable
- **THEN** an "Import list" button SHALL be displayed next to the "Add card" button
- **THEN** the button SHALL have an indigo outline style (not solid fill)

#### Scenario: Clicking Import list opens modal
- **WHEN** the user clicks the "Import list" button
- **THEN** an Import List modal SHALL open with file/text input tabs

#### Scenario: Button label is localized
- **WHEN** the application language is English
- **THEN** the button SHALL display "Import list"
- **WHEN** the application language is Spanish
- **THEN** the button SHALL display "Importar lista"

## ADDED Requirements

### Requirement: Import List modal with file and text input
The Import List modal SHALL provide two input modes via a tab toggle: file upload (drag-and-drop zone + file picker) and text paste (textarea). The modal SHALL follow the CardFormModal overlay pattern (fixed overlay, click-outside-to-close).

#### Scenario: Modal displays file/text tabs
- **WHEN** the Import List modal opens
- **THEN** it SHALL display a tab toggle with "File" and "Text" options
- **THEN** the "Text" tab SHALL be selected by default

#### Scenario: File tab shows drag-and-drop zone
- **WHEN** the user selects the "File" tab
- **THEN** a drag-and-drop zone SHALL be displayed accepting `.csv` and `.txt` files
- **THEN** a "Select file" button SHALL be available as alternative

#### Scenario: Text tab shows textarea
- **WHEN** the user selects the "Text" tab
- **THEN** a textarea SHALL be displayed for pasting card lists
- **THEN** a "Continue" button SHALL be enabled only when the textarea is non-empty

#### Scenario: Submit resolves cards and navigates to review
- **WHEN** the user submits a file or text via the modal
- **THEN** the modal SHALL call `api.importResolve()` and show a loading state
- **THEN** on success, the modal SHALL close and navigate to `/import` with the resolved data in route state
- **THEN** on error, the modal SHALL display the error message and remain open

#### Scenario: Click outside closes modal
- **WHEN** the user clicks outside the modal content area
- **THEN** the modal SHALL close without submitting

### Requirement: Import page accepts pre-resolved data from route state
The Import page SHALL check for `resolveData` in React Router location state on mount. If present, it SHALL skip the upload and resolve steps and display the review step immediately.

#### Scenario: Import page receives pre-resolved data
- **WHEN** the Import page loads with `resolveData` in route state
- **THEN** the page SHALL skip to the review step with the provided data
- **THEN** the route state SHALL be cleared to prevent stale data on refresh

#### Scenario: Import page loads without route state
- **WHEN** the Import page loads without route state
- **THEN** the page SHALL display the upload step as normal
