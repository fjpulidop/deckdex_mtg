# Buffered Price Updates Specification

## ADDED Requirements

### Requirement: System SHALL write price updates incrementally during verification

The system SHALL write verified price changes to Google Sheets in configurable batches during the verification phase, rather than accumulating all changes and writing at the end.

#### Scenario: Incremental writes during verification
- **WHEN** the system verifies prices for multiple batches of cards
- **THEN** the system SHALL write accumulated price changes to Google Sheets after every N verification batches (where N is configurable)

#### Scenario: Buffer size configuration
- **WHEN** the processor is initialized with a write_buffer_batches configuration value
- **THEN** the system SHALL use that value to determine when to trigger incremental writes

#### Scenario: Writing remaining changes after verification completes
- **WHEN** price verification completes but there are pending changes not yet written (partial buffer)
- **THEN** the system SHALL write all remaining pending changes to Google Sheets

### Requirement: System SHALL provide progress visibility for incremental writes

The system SHALL display progress information to the user showing when incremental writes occur and their impact.

#### Scenario: Write operation notification
- **WHEN** the system completes an incremental write to Google Sheets
- **THEN** the system SHALL display a notification showing the write number, number of cards processed, and number of actual price updates

#### Scenario: Progress bar integration
- **WHEN** price verification is in progress with incremental writes
- **THEN** the system SHALL maintain the existing progress bar for verification AND display write notifications without disrupting progress display

#### Scenario: Final summary with resume hint
- **WHEN** price update process completes successfully
- **THEN** the system SHALL display a summary showing total cards verified, total prices updated, and a hint for resume-from value

### Requirement: System SHALL maintain data consistency during incremental writes

The system SHALL ensure that incremental writes do not create partial or inconsistent data states in Google Sheets.

#### Scenario: Failed write with retry
- **WHEN** an incremental write to Google Sheets fails due to API quota or transient error
- **THEN** the system SHALL retry the write with exponential backoff (existing retry logic)

#### Scenario: Failed write after retries
- **WHEN** an incremental write fails after all retry attempts
- **THEN** the system SHALL log the error, continue processing, and include the failure in the final summary

#### Scenario: No duplicate writes
- **WHEN** the same price change exists in multiple buffers (edge case)
- **THEN** the system SHALL only write each cell once (most recent value wins)

### Requirement: Write buffer SHALL use sensible default size

The system SHALL use a default buffer size that balances progress visibility, API efficiency, and recovery window.

#### Scenario: Default buffer size
- **WHEN** no explicit write_buffer_batches configuration is provided
- **THEN** the system SHALL use a default value of 3 batches

#### Scenario: Buffer size calculation
- **WHEN** verification batch size is 20 cards and write_buffer_batches is 3
- **THEN** the system SHALL write to Google Sheets every 60 verified cards

### Requirement: System SHALL maintain backward compatibility with existing features

The incremental write feature SHALL not break or change existing price update behaviors.

#### Scenario: Resume-from compatibility
- **WHEN** user restarts price update with --resume-from flag
- **THEN** the system SHALL skip already-processed rows and apply incremental writes to remaining rows

#### Scenario: Dry-run mode compatibility
- **WHEN** user runs price update in dry-run mode
- **THEN** the system SHALL simulate incremental writes without actually writing to Google Sheets

#### Scenario: Existing CLI arguments unchanged
- **WHEN** user runs price update with existing CLI arguments (--update_prices, --batch-size, --workers, etc.)
- **THEN** the system SHALL honor all existing arguments and apply incremental writes transparently

### Requirement: System SHALL minimize data loss window

The incremental write approach SHALL significantly reduce the maximum amount of work that can be lost if the process crashes or is interrupted.

#### Scenario: Maximum data loss with default buffer
- **WHEN** the process crashes mid-buffer with default configuration (3 batches)
- **THEN** the maximum data loss SHALL be 60 verified cards (3 batches × 20 cards)

#### Scenario: Comparison to previous behavior
- **WHEN** comparing data loss window before and after this change
- **THEN** the data loss window SHALL be reduced from "all verified cards" to "one buffer's worth of cards"
