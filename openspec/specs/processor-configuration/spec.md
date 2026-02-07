# Processor Configuration Specification

## Summary

The processor configuration system provides centralized, validated configuration for all components via a hierarchical dataclass system. It SHALL replace hardcoded constants with configurable parameters organized by subsystem (processing, scryfall, google_sheets, openai) while maintaining sensible defaults and backwards compatibility.

## ADDED Requirements

### Requirement: Configuration dataclass

The system SHALL define a `ProcessorConfig` dataclass in `deckdex/config.py` containing all configuration parameters, organized into nested configurations for each subsystem.

#### Scenario: Create config with defaults
- **WHEN** code instantiates `ProcessorConfig()` with no arguments
- **THEN** config contains nested configs with default values: processing (batch_size=20, max_workers=4, api_delay=0.1), scryfall (max_retries=3, retry_delay=0.5, timeout=10.0), google_sheets (batch_size=500, max_retries=5), openai (enabled=False)

#### Scenario: Create config with custom nested configs
- **WHEN** code instantiates `ProcessorConfig(processing=ProcessingConfig(batch_size=50, max_workers=8))`
- **THEN** config contains custom processing config and defaults for other nested configs

#### Scenario: Config with all parameters
- **WHEN** code instantiates ProcessorConfig with all nested configs specified
- **THEN** config contains all specified nested configuration objects

### Requirement: Nested configuration dataclasses

The system SHALL define separate dataclasses for each subsystem configuration.

#### Scenario: ProcessingConfig dataclass
- **WHEN** code defines ProcessingConfig
- **THEN** dataclass contains batch_size, max_workers, api_delay, write_buffer_batches fields

#### Scenario: ScryfallConfig dataclass
- **WHEN** code defines ScryfallConfig
- **THEN** dataclass contains max_retries, retry_delay, timeout fields

#### Scenario: GoogleSheetsConfig dataclass
- **WHEN** code defines GoogleSheetsConfig
- **THEN** dataclass contains batch_size, max_retries, retry_delay, sheet_name, worksheet_name fields

#### Scenario: OpenAIConfig dataclass
- **WHEN** code defines OpenAIConfig
- **THEN** dataclass contains enabled, model, max_tokens, temperature, max_retries fields

### Requirement: Configuration validation

The system SHALL validate configuration parameters in each dataclass's `__post_init__` method.

#### Scenario: Valid configuration
- **WHEN** ProcessorConfig or nested config is created with valid values
- **THEN** validation passes and object is created successfully

#### Scenario: Invalid batch size (ProcessingConfig)
- **WHEN** ProcessingConfig is created with batch_size <= 0
- **THEN** system raises ValueError with message "batch_size must be > 0"

#### Scenario: Invalid worker count low (ProcessingConfig)
- **WHEN** ProcessingConfig is created with max_workers < 1
- **THEN** system raises ValueError with message "max_workers must be between 1 and 10"

#### Scenario: Invalid worker count high (ProcessingConfig)
- **WHEN** ProcessingConfig is created with max_workers > 10
- **THEN** system raises ValueError with message "max_workers must be between 1 and 10"

#### Scenario: Invalid API delay (ProcessingConfig)
- **WHEN** ProcessingConfig is created with api_delay < 0
- **THEN** system raises ValueError with message "api_delay must be >= 0"

#### Scenario: ScryfallConfig validation
- **WHEN** ScryfallConfig is created with max_retries < 1
- **THEN** system raises ValueError with message "max_retries must be >= 1"

#### Scenario: GoogleSheetsConfig validation
- **WHEN** GoogleSheetsConfig is created with batch_size <= 0
- **THEN** system raises ValueError with message "batch_size must be > 0"

#### Scenario: OpenAIConfig validation
- **WHEN** OpenAIConfig is created with temperature < 0.0 or temperature > 1.0
- **THEN** system raises ValueError with message "temperature must be between 0.0 and 1.0"

#### Scenario: Invalid limit (ProcessorConfig)
- **WHEN** ProcessorConfig is created with limit <= 0
- **THEN** system raises ValueError with message "limit must be > 0"

#### Scenario: Invalid resume_from (ProcessorConfig)
- **WHEN** ProcessorConfig is created with resume_from < 1
- **THEN** system raises ValueError with message "resume_from must be >= 1"

### Requirement: Configuration fields

The system SHALL include all necessary configuration fields in ProcessorConfig, now organized into nested structures.

#### Scenario: Behavioral flags
- **WHEN** ProcessorConfig is created
- **THEN** config includes update_prices, dry_run, verbose as boolean fields (use_openai moved to openai.enabled)

#### Scenario: Nested configurations
- **WHEN** ProcessorConfig is created
- **THEN** config includes processing, scryfall, google_sheets, openai as nested config objects

#### Scenario: Credentials and control
- **WHEN** ProcessorConfig is created
- **THEN** config includes credentials_path, limit, resume_from fields

### Requirement: Backwards compatibility properties

The system SHALL provide deprecated properties on ProcessorConfig that delegate to nested configs for gradual migration.

#### Scenario: Legacy batch_size property
- **WHEN** code accesses config.batch_size
- **THEN** property returns config.processing.batch_size value and emits DeprecationWarning

#### Scenario: Legacy max_workers property
- **WHEN** code accesses config.max_workers
- **THEN** property returns config.processing.max_workers value and emits DeprecationWarning

#### Scenario: Legacy api_delay property
- **WHEN** code accesses config.api_delay
- **THEN** property returns config.processing.api_delay value and emits DeprecationWarning

#### Scenario: Legacy use_openai property
- **WHEN** code accesses config.use_openai
- **THEN** property returns config.openai.enabled value and emits DeprecationWarning

#### Scenario: Legacy sheet_name property
- **WHEN** code accesses config.sheet_name
- **THEN** property returns config.google_sheets.sheet_name value and emits DeprecationWarning

#### Scenario: Legacy worksheet_name property
- **WHEN** code accesses config.worksheet_name
- **THEN** property returns config.google_sheets.worksheet_name value and emits DeprecationWarning

### Requirement: MagicCardProcessor integration

The system SHALL modify MagicCardProcessor to use nested configuration objects.

#### Scenario: Initialize with nested config
- **WHEN** MagicCardProcessor is instantiated with ProcessorConfig
- **THEN** processor uses config.processing.batch_size, config.processing.max_workers, config.processing.api_delay

#### Scenario: Pass nested configs to subsystems
- **WHEN** MagicCardProcessor initializes CardFetcher
- **THEN** processor passes config.scryfall and config.openai to CardFetcher constructor

#### Scenario: Pass GoogleSheetsConfig
- **WHEN** MagicCardProcessor initializes SpreadsheetClient via ClientFactory
- **THEN** factory passes config.google_sheets to SpreadsheetClient constructor

#### Scenario: Replace class constants
- **WHEN** MagicCardProcessor is instantiated
- **THEN** processor uses config.processing attributes instead of deprecated class constants

#### Scenario: Access configuration
- **WHEN** processor methods need configuration values
- **THEN** methods access config.processing.batch_size, config.scryfall.max_retries, etc. instead of flat config attributes

### Requirement: Optimized defaults

The system SHALL provide defaults optimized for Scryfall API rate limits and Google Sheets quotas, now organized by subsystem.

#### Scenario: Processing defaults
- **WHEN** ProcessingConfig uses defaults
- **THEN** batch_size=20, max_workers=4, api_delay=0.1, write_buffer_batches=3

#### Scenario: Scryfall defaults
- **WHEN** ScryfallConfig uses defaults
- **THEN** max_retries=3, retry_delay=0.5, timeout=10.0

#### Scenario: Google Sheets defaults
- **WHEN** GoogleSheetsConfig uses defaults
- **THEN** batch_size=500, max_retries=5, retry_delay=2.0, sheet_name="magic", worksheet_name="cards"

#### Scenario: OpenAI defaults
- **WHEN** OpenAIConfig uses defaults
- **THEN** enabled=false, model="gpt-3.5-turbo", max_tokens=150, temperature=0.7, max_retries=3

#### Scenario: Scryfall rate limit compliance
- **WHEN** ProcessingConfig uses default api_delay
- **THEN** api_delay is 0.1 seconds (100ms) to stay under 10 requests/second limit

#### Scenario: Write buffer default
- **WHEN** ProcessingConfig uses default write_buffer_batches
- **THEN** write_buffer_batches is 3 for balanced progress visibility and API efficiency (writes every 60 cards with batch_size=20)

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
