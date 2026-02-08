# Web Dashboard UI (Delta)

New Settings screen and CRUD actions on cards. Existing dashboard and filter requirements unchanged.

## ADDED Requirements

### Requirement: Navigation SHALL include a link to Settings

The application layout SHALL provide a navigation entry (e.g. "Settings" link or button) that navigates to the Settings route. The Settings route SHALL render the Settings page as specified in the settings-screen capability.

#### Scenario: User can open Settings from navigation
- **WHEN** the user clicks the Settings entry in the navigation
- **THEN** the application SHALL navigate to the Settings route and SHALL display the Settings page

### Requirement: Settings page SHALL implement Import from Google Sheets flow

The Settings page SHALL include the "Import from Google Sheets" section with states: not connected (show "Connect with Google"), connected (show connection status and sheet picker), importing (show progress), and result (success count or error). Behavior SHALL match the settings-screen and google-oauth-import specs.

#### Scenario: Connect with Google from Settings
- **WHEN** the user is on Settings and not connected, and clicks "Connect with Google"
- **THEN** the application SHALL navigate to or open the backend OAuth URL so the user can authorize with Google

#### Scenario: Choose sheet and import after connection
- **WHEN** the user is connected and selects a spreadsheet (and optionally worksheet) and clicks Import
- **THEN** the application SHALL call the import endpoint and SHALL display the result (number imported or error)

### Requirement: Settings page SHALL implement Import from local file flow

The Settings page SHALL include the "Import from local file" section with file upload (and optionally paste). The user SHALL be able to select or drop a CSV or JSON file and trigger import. The application SHALL display the import result (success count or error). Behavior SHALL match the settings-screen and local-import specs.

#### Scenario: Upload file and import
- **WHEN** the user selects or drops a file and triggers import
- **THEN** the application SHALL send the file to the import endpoint and SHALL display the result

### Requirement: Dashboard SHALL allow adding a new card

The dashboard (or cards view) SHALL provide an "Add card" (or equivalent) control that opens a form or modal. The form SHALL include fields for the card (at least name; other fields as needed). On submit, the application SHALL call POST /api/cards and SHALL refresh the list or append the new card on success; on error, the application SHALL display the error (e.g. toast or inline).

#### Scenario: User adds a card
- **WHEN** the user opens the add form, fills required fields, and submits
- **THEN** the application SHALL create the card via the API and SHALL update the card list on success

### Requirement: Dashboard SHALL allow editing an existing card

The dashboard (or cards view) SHALL provide an edit control (e.g. edit button or row action) that opens a form or modal pre-filled with the card data. On submit, the application SHALL call PUT or PATCH /api/cards/{id} and SHALL refresh or update the row on success; on error, the application SHALL display the error.

#### Scenario: User edits a card
- **WHEN** the user opens the edit form for a card, changes fields, and submits
- **THEN** the application SHALL update the card via the API and SHALL reflect changes in the list on success

### Requirement: Dashboard SHALL allow deleting a card

The dashboard (or cards view) SHALL provide a delete control (e.g. delete button) with confirmation. On confirm, the application SHALL call DELETE /api/cards/{id} and SHALL remove the card from the list on success; on error, the application SHALL display the error.

#### Scenario: User deletes a card
- **WHEN** the user confirms deletion of a card
- **THEN** the application SHALL call the delete API and SHALL remove the card from the list on success

### Requirement: Process Cards action SHALL offer scope choice

When the user triggers "Process Cards", the application SHALL offer a choice of scope (e.g. dropdown or modal): "New added cards (with only the name)" (scope=new_only) and "All cards" (scope=all). The request to POST /api/process SHALL include the selected scope in the body. This allows processing only newly added or incomplete cards without reprocessing the entire collection.

#### Scenario: User processes only new cards
- **WHEN** the user selects "New added cards (with only the name)" and confirms
- **THEN** the application SHALL call POST /api/process with body { scope: "new_only" } and SHALL show job progress as for any process job

#### Scenario: User processes all cards
- **WHEN** the user selects "All cards" and confirms
- **THEN** the application SHALL call POST /api/process with body { scope: "all" } (or omit scope) and SHALL show job progress

## MODIFIED Requirements

None. The existing "Dashboard SHALL provide card filtering by all table dimensions" requirement and its scenarios remain unchanged; filtering continues to apply to the card list (now sourced from Postgres).
