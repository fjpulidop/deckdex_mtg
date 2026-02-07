# Price Updates Specification

## ADDED Requirements

### Requirement: Configuration SHALL include write buffer parameter

The ProcessorConfig dataclass SHALL include a new configuration parameter for controlling incremental write behavior.

#### Scenario: Write buffer batches parameter exists
- **WHEN** ProcessorConfig is instantiated
- **THEN** it SHALL have a write_buffer_batches attribute with type int

#### Scenario: Write buffer batches default value
- **WHEN** ProcessorConfig is instantiated without explicit write_buffer_batches value
- **THEN** write_buffer_batches SHALL default to 3

#### Scenario: Write buffer batches validation
- **WHEN** ProcessorConfig is instantiated with write_buffer_batches less than 1
- **THEN** it SHALL raise ValueError with message indicating minimum value

### Requirement: Price update execution SHALL use incremental writes

The update_prices_data method SHALL be refactored to write price changes incrementally rather than accumulating all changes.

#### Scenario: Buffered write tracking
- **WHEN** update_prices_data begins execution
- **THEN** it SHALL initialize a pending_changes buffer and batches_processed counter

#### Scenario: Buffer write trigger
- **WHEN** batches_processed reaches write_buffer_batches threshold
- **THEN** the system SHALL write pending_changes to Google Sheets, reset the buffer, and reset the counter

#### Scenario: Progress notification after write
- **WHEN** an incremental write completes successfully
- **THEN** the system SHALL print a progress notification with write number and update counts

#### Scenario: Write delay between buffers
- **WHEN** an incremental write completes
- **THEN** the system SHALL sleep for 1.5 seconds before continuing verification (rate limiting)

### Requirement: Helper method SHALL handle buffered writes

A new private method _write_buffered_prices SHALL be added to encapsulate the logic for writing a buffer of price changes.

#### Scenario: Write buffered prices signature
- **WHEN** _write_buffered_prices is called
- **THEN** it SHALL accept a list of (row_index, card_name, new_price) tuples

#### Scenario: Write buffered prices return value
- **WHEN** _write_buffered_prices completes successfully
- **THEN** it SHALL return the number of prices actually written

#### Scenario: Batch update construction
- **WHEN** _write_buffered_prices processes changes
- **THEN** it SHALL construct batch update operations using gspread.utils.rowcol_to_a1 and the price column index

#### Scenario: Reuse existing write logic
- **WHEN** _write_buffered_prices writes to Google Sheets
- **THEN** it SHALL use the existing _batch_update_prices method with retry logic

### Requirement: Price column index SHALL be cached

The system SHALL cache the price column index to avoid redundant API calls when writing multiple buffers.

#### Scenario: Price column index caching
- **WHEN** _get_price_column_index is called for the first time
- **THEN** it SHALL cache the result in _headers_cache

#### Scenario: Price column index reuse
- **WHEN** _get_price_column_index is called multiple times in the same execution
- **THEN** it SHALL return the cached value without making additional API calls

### Requirement: Final summary SHALL include resume hint

After price update completes, the system SHALL provide actionable information for resuming from the last processed position.

#### Scenario: Successful completion summary
- **WHEN** update_prices_data completes successfully
- **THEN** it SHALL print a summary with total cards verified and total prices updated

#### Scenario: Resume-from hint display
- **WHEN** update_prices_data completes successfully with N cards processed
- **THEN** it SHALL display a hint message with format "💡 To resume from here: --resume-from N"
