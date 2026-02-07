# Dry-Run Mode Specification

## Summary

Dry-run mode enables users to simulate card processing without writing to Google Sheets. It SHALL fetch data from external APIs (Scryfall, OpenAI) but skip all write operations, displaying what would be changed.

## ADDED Requirements

### Requirement: Dry-run client implementation

The system SHALL provide a `DryRunClient` class that implements the same interface as `SpreadsheetClient` but does not perform write operations.

#### Scenario: Initialize dry-run client
- **WHEN** DryRunClient is instantiated with configuration
- **THEN** client initializes without connecting to Google Sheets API

#### Scenario: Mock get operations
- **WHEN** dry-run client's get_cards() or get_all_cards_prices() is called
- **THEN** client returns empty list or mock data without API call

#### Scenario: Intercept write operations
- **WHEN** dry-run client's update_column() or update_cells() is called
- **THEN** client logs the operation details but does not write to Google Sheets

### Requirement: Client factory

The system SHALL use a factory pattern to create appropriate client based on dry_run configuration.

#### Scenario: Create normal client
- **WHEN** factory is called with config where dry_run=False
- **THEN** factory returns SpreadsheetClient instance

#### Scenario: Create dry-run client
- **WHEN** factory is called with config where dry_run=True
- **THEN** factory returns DryRunClient instance

### Requirement: Dry-run output

The system SHALL display comprehensive information about what would be executed in dry-run mode.

#### Scenario: Display configuration
- **WHEN** dry-run mode starts
- **THEN** system displays banner "DRY RUN MODE - No changes will be written" and configuration summary

#### Scenario: Show simulated operations
- **WHEN** dry-run mode processes cards
- **THEN** system displays progress bars and statistics as in normal mode

#### Scenario: Display sample output
- **WHEN** dry-run mode completes
- **THEN** system shows first 3-5 sample rows that would be written

#### Scenario: Summary report
- **WHEN** dry-run mode completes
- **THEN** system displays summary with card count, API calls made, errors encountered, estimated write time

### Requirement: API interaction in dry-run

The system SHALL make real API calls to Scryfall and OpenAI during dry-run mode.

#### Scenario: Fetch card data
- **WHEN** dry-run mode processes a card
- **THEN** system makes real API call to Scryfall to fetch card data

#### Scenario: Fetch OpenAI data
- **WHEN** dry-run mode processes card with --use_openai flag
- **THEN** system makes real API call to OpenAI to generate strategy and tier

#### Scenario: Respect rate limits
- **WHEN** dry-run mode makes API calls
- **THEN** system applies configured api_delay between requests

### Requirement: Operation logging

The system SHALL log all operations that would be performed in dry-run mode.

#### Scenario: Log batch updates
- **WHEN** dry-run client receives batch update request
- **THEN** client logs "DRY RUN: Would update range A2:T21 with 20 rows"

#### Scenario: Log column updates
- **WHEN** dry-run client receives column update request
- **THEN** client logs "DRY RUN: Would update column 'Price' for N rows"

#### Scenario: Collect statistics
- **WHEN** dry-run mode executes
- **THEN** client tracks count of operations that would be performed

### Requirement: No side effects

The system SHALL guarantee no writes to Google Sheets in dry-run mode.

#### Scenario: No sheet connection
- **WHEN** dry-run mode is active
- **THEN** system does not authenticate with Google Sheets API

#### Scenario: No write operations
- **WHEN** dry-run client's write methods are called
- **THEN** methods return immediately without network calls

#### Scenario: Verify no changes
- **WHEN** dry-run mode completes
- **THEN** Google Sheet remains unchanged from before execution

### Requirement: Error simulation

The system SHALL show actual API errors encountered during dry-run.

#### Scenario: Card not found
- **WHEN** dry-run mode processes non-existent card
- **THEN** system displays error same as normal mode

#### Scenario: OpenAI rate limit
- **WHEN** dry-run mode hits OpenAI rate limit
- **THEN** system displays rate limit error same as normal mode

#### Scenario: Scryfall error
- **WHEN** dry-run mode encounters Scryfall API error
- **THEN** system displays error same as normal mode
