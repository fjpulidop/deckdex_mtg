# CLI Interface Specification

## Summary

The CLI interface provides the primary user-facing command-line entry point for DeckDex MTG. It SHALL accept arguments for configuration, behavioral flags, and execution control, providing comprehensive help text and validation.

## ADDED Requirements

### Requirement: CLI entry point

The system SHALL provide a single CLI entry point at `main.py` that accepts command-line arguments and orchestrates card processing.

#### Scenario: Basic invocation
- **WHEN** user runs `python main.py` with no arguments
- **THEN** system processes all cards with default configuration

#### Scenario: Help text
- **WHEN** user runs `python main.py --help` or `python main.py -h`
- **THEN** system displays comprehensive help text including all options, defaults, and usage examples

### Requirement: Behavioral flags

The system SHALL accept boolean flags that control processing behavior.

#### Scenario: Enable OpenAI enrichment
- **WHEN** user runs `python main.py --use_openai`
- **THEN** system fetches game strategy and tier data from OpenAI for each card

#### Scenario: Update prices mode
- **WHEN** user runs `python main.py --update_prices`
- **THEN** system updates only the price column for all cards in the sheet

#### Scenario: Dry-run mode
- **WHEN** user runs `python main.py --dry-run`
- **THEN** system simulates execution without writing to Google Sheets

#### Scenario: Verbose logging
- **WHEN** user runs `python main.py --verbose` or `python main.py -v`
- **THEN** system outputs detailed logging including per-card and per-batch information

### Requirement: Performance configuration

The system SHALL accept integer arguments to configure performance parameters with validation.

#### Scenario: Configure batch size
- **WHEN** user runs `python main.py --batch-size 50`
- **THEN** system processes cards in batches of 50

#### Scenario: Invalid batch size
- **WHEN** user runs `python main.py --batch-size 0` or `python main.py --batch-size -5`
- **THEN** system exits with error message "batch_size must be > 0"

#### Scenario: Configure worker count
- **WHEN** user runs `python main.py --workers 8`
- **THEN** system uses ThreadPoolExecutor with max_workers=8

#### Scenario: Invalid worker count
- **WHEN** user runs `python main.py --workers 0` or `python main.py --workers 15`
- **THEN** system exits with error message "max_workers must be between 1 and 10"

#### Scenario: Configure API delay
- **WHEN** user runs `python main.py --api-delay 0.2`
- **THEN** system waits 0.2 seconds between API requests

#### Scenario: Invalid API delay
- **WHEN** user runs `python main.py --api-delay -0.1`
- **THEN** system exits with error message "api_delay must be >= 0"

#### Scenario: Configure max retries
- **WHEN** user runs `python main.py --max-retries 10`
- **THEN** system retries failed requests up to 10 times

#### Scenario: Invalid max retries
- **WHEN** user runs `python main.py --max-retries 0`
- **THEN** system exits with error message "max_retries must be >= 1"

### Requirement: Google Sheets configuration

The system SHALL accept string arguments to configure Google Sheets connection.

#### Scenario: Custom credentials path
- **WHEN** user runs `python main.py --credentials-path /path/to/creds.json`
- **THEN** system uses specified credentials file instead of GOOGLE_API_CREDENTIALS env var

#### Scenario: Custom spreadsheet name
- **WHEN** user runs `python main.py --sheet-name "my_collection"`
- **THEN** system opens spreadsheet named "my_collection" instead of default "magic"

#### Scenario: Custom worksheet name
- **WHEN** user runs `python main.py --worksheet-name "standard_cards"`
- **THEN** system opens worksheet named "standard_cards" instead of default "cards"

### Requirement: Processing control

The system SHALL accept arguments to control which cards are processed.

#### Scenario: Limit processing
- **WHEN** user runs `python main.py --limit 10`
- **THEN** system processes only the first 10 cards

#### Scenario: Invalid limit
- **WHEN** user runs `python main.py --limit 0` or `python main.py --limit -5`
- **THEN** system exits with error message "limit must be > 0"

#### Scenario: Resume from row
- **WHEN** user runs `python main.py --resume-from 50`
- **THEN** system skips rows 1-49 and starts processing from row 50

#### Scenario: Invalid resume row
- **WHEN** user runs `python main.py --resume-from 0` or `python main.py --resume-from -5`
- **THEN** system exits with error message "resume_from must be >= 1"

### Requirement: Backwards compatibility

The system SHALL maintain compatibility with existing command invocations.

#### Scenario: Legacy basic command
- **WHEN** user runs `python main.py` as before this change
- **THEN** system behaves identically to previous version (same defaults)

#### Scenario: Legacy OpenAI command
- **WHEN** user runs `python main.py --use_openai` as before this change
- **THEN** system behaves identically to previous version

#### Scenario: Legacy price update command
- **WHEN** user runs `python main.py --update_prices` as before this change
- **THEN** system behaves identically to previous version

### Requirement: Argument combination

The system SHALL allow combining multiple arguments in a single invocation.

#### Scenario: Combined performance tuning
- **WHEN** user runs `python main.py --batch-size 30 --workers 6 --api-delay 0.15`
- **THEN** system applies all specified configuration values

#### Scenario: Testing workflow
- **WHEN** user runs `python main.py --limit 5 --dry-run --verbose`
- **THEN** system processes 5 cards in dry-run mode with verbose output

#### Scenario: Custom sheet workflow
- **WHEN** user runs `python main.py --sheet-name "legacy" --worksheet-name "old_cards" --use_openai`
- **THEN** system processes specified sheet with OpenAI enrichment
