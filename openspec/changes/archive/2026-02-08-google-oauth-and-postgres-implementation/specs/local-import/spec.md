# Local Import

Import cards from a local file (CSV or JSON) into Postgres via the Settings screen. Column/field mapping consistent with the card model.

## ADDED Requirements

### Requirement: User SHALL be able to import cards from an uploaded file

The system SHALL accept an uploaded file (CSV or JSON) from the Settings screen and SHALL parse it to extract card records. The system SHALL map columns (CSV) or fields (JSON) to the Card model. The system SHALL replace the current collection in Postgres with the imported cards. The system SHALL return a summary (e.g. number of cards imported) or a structured error (e.g. invalid format, missing required columns).

#### Scenario: Successful CSV import
- **WHEN** the user uploads a valid CSV file with headers matching the expected card columns (e.g. Name, English name, Type, Price, …)
- **THEN** the system SHALL parse the file, map rows to cards, replace the collection in Postgres, and SHALL return the number of cards imported

#### Scenario: Successful JSON import
- **WHEN** the user uploads a valid JSON file containing an array of card-like objects with fields aligned to the Card model
- **THEN** the system SHALL parse the file, map objects to cards, replace the collection in Postgres, and SHALL return the number of cards imported

#### Scenario: Import replaces existing collection
- **WHEN** the user imports from a local file and the collection already has cards
- **THEN** the system SHALL replace the entire collection with the imported data (same policy as Google Sheets import)

#### Scenario: Invalid file format
- **WHEN** the uploaded file is not valid CSV or JSON, or lacks required columns/fields
- **THEN** the system SHALL respond with an error that describes the problem (e.g. "Invalid format" or "Missing column: Name") and SHALL NOT modify the existing collection
