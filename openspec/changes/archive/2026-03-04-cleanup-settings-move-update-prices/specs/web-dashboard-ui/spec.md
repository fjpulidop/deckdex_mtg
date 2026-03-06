## ADDED Requirements

### Requirement: Update Prices button in CardTable toolbar
The CardTable toolbar SHALL display an "Update Prices" button next to the "Import list" button when an update prices callback is provided. The button SHALL use a tertiary style (slate/gray outline, transparent background) and trigger a price update job that registers in the global jobs bar.

#### Scenario: Update Prices button visible on dashboard
- **WHEN** the user views the Dashboard with the CardTable
- **THEN** an "Update Prices" button SHALL be displayed after the "Import list" button
- **THEN** the button SHALL have a slate/gray outline style (tertiary importance)

#### Scenario: Clicking Update Prices triggers job
- **WHEN** the user clicks the "Update Prices" button
- **THEN** the system SHALL trigger a price update job via the backend
- **THEN** the button SHALL show "Starting..." while the job is being created
- **THEN** the job SHALL appear in the global jobs bar

#### Scenario: Button label is localized
- **WHEN** the application language is English
- **THEN** the button SHALL display "Update Prices"
- **WHEN** the application language is Spanish
- **THEN** the button SHALL display "Actualizar precios"

## MODIFIED Requirements

### Requirement: Import wizard includes Review step
The import wizard SHALL include 6 steps: upload → resolve → review → mode → progress → result. The resolve step replaces the previous preview step and includes format detection, card count, and per-card resolution status.

#### Scenario: Step indicator shows 6 steps
- **WHEN** the user opens the import page
- **THEN** the step indicator SHALL display 6 numbered steps

#### Scenario: Upload triggers resolve instead of preview
- **WHEN** the user uploads a file or submits pasted text
- **THEN** the wizard SHALL call the resolve endpoint and advance to the review step upon completion

## REMOVED Requirements

### Requirement: Settings Deck Actions section
**Reason**: Process Cards and Update Prices have been relocated. Process Cards is no longer needed; Update Prices is now in the CardTable toolbar.
**Migration**: Use the "Update Prices" button in the dashboard CardTable toolbar.
