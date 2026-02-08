# Settings Screen

Settings page (route `/settings`) with "Import from file" (upload CSV or JSON to replace collection). Clear import result feedback.

## Requirements

### Requirement: Application SHALL provide a Settings route

The application SHALL expose a Settings page at `/settings`. The layout SHALL include a navigation entry to reach Settings from the main dashboard.

#### Scenario: User navigates to Settings
- **WHEN** the user selects "Settings" in the navigation
- **THEN** the application SHALL navigate to `/settings` and SHALL display the Settings page content

### Requirement: Settings SHALL support "Import from file" flow

The Settings page SHALL include a section for importing from a local file. The section SHALL allow the user to upload a CSV or JSON file. The section SHALL show import result (success with count or error).

#### Scenario: User uploads file for import
- **WHEN** the user selects a CSV or JSON file
- **THEN** the system SHALL send the file to the backend import endpoint and SHALL display the result (number imported or error)

#### Scenario: Import result feedback
- **WHEN** the file import completes (success or failure)
- **THEN** the system SHALL display the result so the user understands the outcome

### Requirement: Settings SHALL support Scryfall API credentials

The Settings page SHALL include a section for Scryfall API credentials. The user SHALL be able to paste or upload the Scryfall credentials JSON. The backend SHALL store the JSON content internally (e.g. in app settings or data file) and SHALL remember it for the next run; no file path is required on the server. The backend SHALL use these stored credentials when running price updates or other Scryfall-dependent operations. When no credentials are configured, the backend SHALL return a clear message (e.g. "Scryfall credentials not configured") instead of a system error such as file-not-found.

#### Scenario: User configures Scryfall credentials
- **WHEN** the user pastes the credentials JSON or uploads a .json file in Settings and saves
- **THEN** the backend SHALL persist the JSON content internally and SHALL use it for subsequent Scryfall API usage

#### Scenario: No Scryfall credentials configured
- **WHEN** an operation that requires Scryfall credentials is run and none are stored
- **THEN** the system SHALL respond with a clear message that credentials are not configured (not a raw file or path error)
