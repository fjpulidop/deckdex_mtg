# Verbose Logging Specification

## Summary

Verbose logging provides detailed execution information for debugging and monitoring. The system SHALL support two logging levels: normal (progress bars and errors) and verbose (detailed per-card and per-batch information).

## ADDED Requirements

### Requirement: Logging configuration

The system SHALL provide a centralized logging configuration module at `deckdex/logger_config.py`.

#### Scenario: Initialize normal logging
- **WHEN** configure_logging(verbose=False) is called
- **THEN** logger outputs only INFO level messages, errors, warnings, and progress bars

#### Scenario: Initialize verbose logging
- **WHEN** configure_logging(verbose=True) is called
- **THEN** logger outputs DEBUG level messages including per-card and per-batch details

#### Scenario: Log format
- **WHEN** logging is configured
- **THEN** log messages include timestamp, level, and message

### Requirement: Normal mode output

The system SHALL provide concise output in normal mode.

#### Scenario: Connection message
- **WHEN** system connects to Google Sheets in normal mode
- **THEN** system logs "Connected to spreadsheet 'name', worksheet 'name'"

#### Scenario: Progress bar
- **WHEN** system processes cards in normal mode
- **THEN** system displays tqdm progress bar with cards/second rate

#### Scenario: Error summary
- **WHEN** system encounters errors in normal mode
- **THEN** system displays error count and sample error messages

#### Scenario: Completion message
- **WHEN** system completes processing in normal mode
- **THEN** system logs "Card processing completed successfully"

### Requirement: Verbose mode output

The system SHALL provide detailed output in verbose mode.

#### Scenario: Batch start
- **WHEN** system starts a batch in verbose mode
- **THEN** system logs "Starting batch N/M (cards X-Y)"

#### Scenario: Card fetch
- **WHEN** system fetches a card in verbose mode
- **THEN** system logs "Fetching: Card Name... ✓ (123ms)" or "Fetching: Card Name... ✗ (error)"

#### Scenario: API timing
- **WHEN** system makes API calls in verbose mode
- **THEN** system logs timing for each call

#### Scenario: Batch write
- **WHEN** system writes batch in verbose mode
- **THEN** system logs "Writing batch to A2:T21... ✓ (245ms)"

#### Scenario: Statistics
- **WHEN** system completes in verbose mode
- **THEN** system displays detailed statistics: total cards, successful, errors, total time, average time per card

### Requirement: Error counter

The system SHALL display a running counter of cards not found during processing.

#### Scenario: Initial counter
- **WHEN** processing starts
- **THEN** system displays "Cards not found counter: 0"

#### Scenario: Increment counter
- **WHEN** card is not found
- **THEN** system updates counter display with current count and last 3 not-found card names

#### Scenario: Final error report
- **WHEN** processing completes with errors
- **THEN** system displays total cards not found and up to 10 card names

### Requirement: Progress visualization

The system SHALL use tqdm for progress bars with appropriate configuration.

#### Scenario: Progress bar elements
- **WHEN** processing runs
- **THEN** progress bar shows: description, percentage, current/total, cards/s, elapsed time, ETA

#### Scenario: Price update progress
- **WHEN** updating prices
- **THEN** system displays "Verifying prices" progress bar followed by "Updating prices" progress bar

#### Scenario: Card processing progress
- **WHEN** processing cards
- **THEN** system displays "Processing cards" progress bar

### Requirement: Color-coded output

The system SHALL use ANSI color codes for terminal output highlighting.

#### Scenario: Error highlighting
- **WHEN** system displays error count
- **THEN** error count is displayed in red bold text

#### Scenario: Warning highlighting
- **WHEN** system displays cards not found
- **THEN** card names are displayed in yellow text

#### Scenario: Success highlighting
- **WHEN** system displays completion message
- **THEN** checkmark and success message are displayed in green

### Requirement: Log level control

The system SHALL configure loguru logger based on verbose flag.

#### Scenario: Remove default handler
- **WHEN** logger is configured
- **THEN** system removes default loguru handler

#### Scenario: Add normal handler
- **WHEN** verbose=False
- **THEN** system adds handler with level="INFO"

#### Scenario: Add verbose handler
- **WHEN** verbose=True
- **THEN** system adds handler with level="DEBUG"

### Requirement: Stdout flushing

The system SHALL flush stdout after critical messages to ensure immediate display.

#### Scenario: Error counter update
- **WHEN** error counter is displayed
- **THEN** system calls sys.stdout.flush() to force immediate output

#### Scenario: Progress bar compatibility
- **WHEN** error messages are displayed during progress bar operation
- **THEN** messages appear below progress bar without interfering

### Requirement: Logging in dry-run mode

The system SHALL provide appropriate logging in dry-run mode.

#### Scenario: Dry-run banner
- **WHEN** dry-run mode starts with verbose logging
- **THEN** system displays "DRY RUN MODE" banner and configuration details

#### Scenario: Operation logging
- **WHEN** dry-run mode simulates operations with verbose logging
- **THEN** system logs each simulated operation with "DRY RUN:" prefix

#### Scenario: Summary in dry-run
- **WHEN** dry-run mode completes with verbose logging
- **THEN** system displays detailed summary of simulated operations
