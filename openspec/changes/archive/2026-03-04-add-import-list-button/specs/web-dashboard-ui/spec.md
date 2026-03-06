## ADDED Requirements

### Requirement: Import list button in CardTable toolbar
The CardTable toolbar SHALL display an "Import list" button next to the "Add card" button when an import callback is provided. The button SHALL navigate to the Import wizard (`/import`). The button SHALL use an outline/ghost style (indigo border, transparent background) to communicate secondary importance relative to the primary "Add card" button.

#### Scenario: Import list button visible on dashboard
- **WHEN** the user views the Dashboard with the CardTable
- **THEN** an "Import list" button SHALL be displayed next to the "Add card" button
- **THEN** the button SHALL have an indigo outline style (not solid fill)

#### Scenario: Clicking Import list navigates to import wizard
- **WHEN** the user clicks the "Import list" button
- **THEN** the application SHALL navigate to `/import`

#### Scenario: Button label is localized
- **WHEN** the application language is English
- **THEN** the button SHALL display "Import list"
- **WHEN** the application language is Spanish
- **THEN** the button SHALL display "Importar lista"
