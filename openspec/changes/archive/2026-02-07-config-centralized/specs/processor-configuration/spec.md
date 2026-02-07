# Processor Configuration Specification (Delta)

## Summary

Delta spec for processor-configuration capability. Evolves from simple flat dataclass to hierarchical system with nested configurations for each subsystem (processing, scryfall, google_sheets, openai).

## ADDED Requirements

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

### Requirement: Validation in nested configs

The system SHALL validate parameters in each nested config's __post_init__ method.

#### Scenario: ProcessingConfig validation
- **WHEN** ProcessingConfig is created with invalid values
- **THEN** system raises ValueError with appropriate message

#### Scenario: ScryfallConfig validation
- **WHEN** ScryfallConfig is created with max_retries < 1
- **THEN** system raises ValueError with message "max_retries must be >= 1"

#### Scenario: GoogleSheetsConfig validation
- **WHEN** GoogleSheetsConfig is created with batch_size <= 0
- **THEN** system raises ValueError with message "batch_size must be > 0"

#### Scenario: OpenAIConfig validation
- **WHEN** OpenAIConfig is created with temperature < 0.0 or temperature > 1.0
- **THEN** system raises ValueError with message "temperature must be between 0.0 and 1.0"

### Requirement: Backwards compatibility properties

The system SHALL provide deprecated properties on ProcessorConfig that delegate to nested configs.

#### Scenario: Legacy batch_size property
- **WHEN** code accesses config.batch_size
- **THEN** property returns config.processing.batch_size value

#### Scenario: Legacy max_workers property
- **WHEN** code accesses config.max_workers
- **THEN** property returns config.processing.max_workers value

#### Scenario: Legacy api_delay property
- **WHEN** code accesses config.api_delay
- **THEN** property returns config.processing.api_delay value

#### Scenario: Legacy use_openai property
- **WHEN** code accesses config.use_openai
- **THEN** property returns config.openai.enabled value

#### Scenario: Legacy sheet_name property
- **WHEN** code accesses config.sheet_name
- **THEN** property returns config.google_sheets.sheet_name value

#### Scenario: Legacy worksheet_name property
- **WHEN** code accesses config.worksheet_name
- **THEN** property returns config.google_sheets.worksheet_name value

## MODIFIED Requirements

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
- **THEN** config includes credentials_path, limit, resume_from fields (unchanged)

### Requirement: MagicCardProcessor integration

The system SHALL modify MagicCardProcessor to use nested configuration objects.

#### Scenario: Initialize with nested config
- **WHEN** MagicCardProcessor is instantiated with ProcessorConfig
- **THEN** processor uses config.processing.batch_size, config.processing.max_workers, etc.

#### Scenario: Pass nested configs to subsystems
- **WHEN** MagicCardProcessor initializes CardFetcher
- **THEN** processor passes config.scryfall to CardFetcher constructor

#### Scenario: Pass GoogleSheetsConfig
- **WHEN** MagicCardProcessor initializes SpreadsheetClient via ClientFactory
- **THEN** factory passes config.google_sheets to SpreadsheetClient constructor

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
