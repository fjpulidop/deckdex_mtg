# Processor Configuration Specification

## Summary

The processor configuration system provides centralized, validated configuration for all components via a dataclass. It SHALL replace hardcoded constants with configurable parameters while maintaining sensible defaults.

## ADDED Requirements

### Requirement: Configuration dataclass

The system SHALL define a `ProcessorConfig` dataclass in `deckdex/config.py` containing all configuration parameters.

#### Scenario: Create config with defaults
- **WHEN** code instantiates `ProcessorConfig()` with no arguments
- **THEN** config contains default values: batch_size=20, max_workers=4, api_delay=0.1, max_retries=5

#### Scenario: Create config with custom values
- **WHEN** code instantiates `ProcessorConfig(batch_size=50, max_workers=8)`
- **THEN** config contains batch_size=50, max_workers=8, and defaults for other fields

#### Scenario: Config with all parameters
- **WHEN** code instantiates ProcessorConfig with all parameters specified
- **THEN** config contains all specified values

### Requirement: Configuration validation

The system SHALL validate configuration parameters in `__post_init__` method.

#### Scenario: Valid configuration
- **WHEN** ProcessorConfig is created with valid values
- **THEN** validation passes and object is created successfully

#### Scenario: Invalid batch size
- **WHEN** ProcessorConfig is created with batch_size <= 0
- **THEN** system raises ValueError with message "batch_size must be > 0"

#### Scenario: Invalid worker count low
- **WHEN** ProcessorConfig is created with max_workers < 1
- **THEN** system raises ValueError with message "max_workers must be between 1 and 10"

#### Scenario: Invalid worker count high
- **WHEN** ProcessorConfig is created with max_workers > 10
- **THEN** system raises ValueError with message "max_workers must be between 1 and 10"

#### Scenario: Invalid API delay
- **WHEN** ProcessorConfig is created with api_delay < 0
- **THEN** system raises ValueError with message "api_delay must be >= 0"

#### Scenario: Invalid max retries
- **WHEN** ProcessorConfig is created with max_retries < 1
- **THEN** system raises ValueError with message "max_retries must be >= 1"

#### Scenario: Invalid limit
- **WHEN** ProcessorConfig is created with limit <= 0
- **THEN** system raises ValueError with message "limit must be > 0"

#### Scenario: Invalid resume_from
- **WHEN** ProcessorConfig is created with resume_from < 1
- **THEN** system raises ValueError with message "resume_from must be >= 1"

### Requirement: Configuration fields

The system SHALL include all necessary configuration fields in ProcessorConfig.

#### Scenario: Behavioral flags
- **WHEN** ProcessorConfig is created
- **THEN** config includes use_openai, update_prices, dry_run, verbose as boolean fields

#### Scenario: Performance settings
- **WHEN** ProcessorConfig is created
- **THEN** config includes batch_size, max_workers, api_delay, max_retries, write_buffer_batches as numeric fields

#### Scenario: Google Sheets settings
- **WHEN** ProcessorConfig is created
- **THEN** config includes credentials_path, sheet_name, worksheet_name as string fields

#### Scenario: Processing control
- **WHEN** ProcessorConfig is created
- **THEN** config includes limit and resume_from as optional numeric fields

### Requirement: MagicCardProcessor integration

The system SHALL modify MagicCardProcessor to accept ProcessorConfig instead of individual parameters.

#### Scenario: Initialize with config
- **WHEN** MagicCardProcessor is instantiated with a ProcessorConfig object
- **THEN** processor uses config values for batch_size, max_workers, api_delay, max_retries

#### Scenario: Replace class constants
- **WHEN** MagicCardProcessor is instantiated
- **THEN** processor uses instance attributes (self.batch_size, self.max_workers) instead of class constants (BATCH_SIZE, MAX_WORKERS)

#### Scenario: Access configuration
- **WHEN** processor methods need configuration values
- **THEN** methods access self.batch_size, self.max_workers, etc. instead of class constants

### Requirement: Optimized defaults

The system SHALL provide defaults optimized for Scryfall API rate limits and Google Sheets quotas.

#### Scenario: Scryfall rate limit compliance
- **WHEN** ProcessorConfig uses default api_delay
- **THEN** api_delay is 0.1 seconds (100ms) to stay under 10 requests/second limit

#### Scenario: Batch size default
- **WHEN** ProcessorConfig uses default batch_size
- **THEN** batch_size is 20 for balanced memory usage and API efficiency

#### Scenario: Worker count default
- **WHEN** ProcessorConfig uses default max_workers
- **THEN** max_workers is 4 for parallel processing without overwhelming APIs

#### Scenario: Retry default
- **WHEN** ProcessorConfig uses default max_retries
- **THEN** max_retries is 5 for resilience without excessive delays

#### Scenario: Write buffer default
- **WHEN** ProcessorConfig uses default write_buffer_batches
- **THEN** write_buffer_batches is 3 for balanced progress visibility and API efficiency (writes every 60 cards)

### Requirement: Type hints

The system SHALL use Python type hints for all configuration fields.

#### Scenario: Boolean fields
- **WHEN** ProcessorConfig is defined
- **THEN** use_openai, update_prices, dry_run, verbose are typed as bool

#### Scenario: Integer fields
- **WHEN** ProcessorConfig is defined
- **THEN** batch_size, max_workers, max_retries, write_buffer_batches are typed as int

#### Scenario: Float fields
- **WHEN** ProcessorConfig is defined
- **THEN** api_delay is typed as float

#### Scenario: Optional fields
- **WHEN** ProcessorConfig is defined
- **THEN** credentials_path, limit, resume_from are typed as Optional[type]

#### Scenario: String fields
- **WHEN** ProcessorConfig is defined
- **THEN** sheet_name, worksheet_name are typed as str
