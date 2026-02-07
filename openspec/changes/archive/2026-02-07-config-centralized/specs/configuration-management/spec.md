# Configuration Management Specification

## Summary

The configuration management system provides a centralized, multi-source configuration system with profile support, override hierarchy, and validation. It SHALL load configuration from YAML files, environment variables, and CLI flags, merging them in a defined priority order.

## ADDED Requirements

### Requirement: YAML configuration file

The system SHALL support a `config.yaml` file with profile-based configuration structure.

#### Scenario: Load default profile
- **WHEN** system loads config.yaml without profile specification
- **THEN** system uses configuration from the "default" section

#### Scenario: Load development profile
- **WHEN** system loads config.yaml with profile="development"
- **THEN** system merges "default" section with "development" section, with development overriding defaults

#### Scenario: Load production profile
- **WHEN** system loads config.yaml with profile="production"
- **THEN** system merges "default" section with "production" section, with production overriding defaults

#### Scenario: Missing profile
- **WHEN** system loads config.yaml with profile="nonexistent"
- **THEN** system logs warning and uses default profile

#### Scenario: Missing config file
- **WHEN** system attempts to load config.yaml but file does not exist
- **THEN** system logs warning and uses built-in defaults

### Requirement: Nested configuration structure

The system SHALL organize configuration into logical subsystem sections.

#### Scenario: Processing configuration
- **WHEN** config.yaml contains "processing" section
- **THEN** section includes batch_size, max_workers, api_delay, write_buffer_batches

#### Scenario: API configuration
- **WHEN** config.yaml contains "api" section
- **THEN** section includes subsections for scryfall, google_sheets, and openai

#### Scenario: Scryfall API configuration
- **WHEN** config.yaml contains "api.scryfall" section
- **THEN** section includes max_retries, retry_delay, timeout

#### Scenario: Google Sheets API configuration
- **WHEN** config.yaml contains "api.google_sheets" section
- **THEN** section includes batch_size, max_retries, retry_delay, sheet_name, worksheet_name

#### Scenario: OpenAI API configuration
- **WHEN** config.yaml contains "api.openai" section
- **THEN** section includes enabled, model, max_tokens, temperature, max_retries

### Requirement: Environment variable overrides

The system SHALL support environment variable overrides using DECKDEX_ prefix convention.

#### Scenario: Override processing parameter
- **WHEN** environment variable DECKDEX_PROCESSING_BATCH_SIZE=30 is set
- **THEN** processing.batch_size uses value 30, overriding YAML value

#### Scenario: Override API parameter
- **WHEN** environment variable DECKDEX_SCRYFALL_MAX_RETRIES=5 is set
- **THEN** api.scryfall.max_retries uses value 5, overriding YAML value

#### Scenario: Boolean environment variable
- **WHEN** environment variable DECKDEX_OPENAI_ENABLED=true is set
- **THEN** api.openai.enabled uses boolean value true

#### Scenario: Integer environment variable
- **WHEN** environment variable DECKDEX_PROCESSING_MAX_WORKERS=8 is set
- **THEN** processing.max_workers uses integer value 8

#### Scenario: Float environment variable
- **WHEN** environment variable DECKDEX_PROCESSING_API_DELAY=0.2 is set
- **THEN** processing.api_delay uses float value 0.2

#### Scenario: Invalid environment variable format
- **WHEN** environment variable does not match DECKDEX_SECTION_KEY pattern
- **THEN** system ignores variable

### Requirement: CLI flag overrides

The system SHALL support CLI flag overrides with highest priority.

#### Scenario: Override via profile flag
- **WHEN** user runs with --profile production
- **THEN** system loads production profile from config.yaml

#### Scenario: Override via specific flag
- **WHEN** user runs with --batch-size 50
- **THEN** processing.batch_size uses value 50, overriding both YAML and ENV values

#### Scenario: Custom config file
- **WHEN** user runs with --config /path/to/custom.yaml
- **THEN** system loads configuration from specified file instead of default config.yaml

#### Scenario: Ad-hoc override with --set
- **WHEN** user runs with --set processing.api_delay=0.02
- **THEN** processing.api_delay uses value 0.02, overriding all other sources

### Requirement: Configuration priority

The system SHALL apply configuration sources in strict priority order.

#### Scenario: YAML only
- **WHEN** only YAML config exists for a parameter
- **THEN** system uses YAML value

#### Scenario: YAML and ENV
- **WHEN** both YAML and ENV var exist for a parameter
- **THEN** system uses ENV var value (ENV overrides YAML)

#### Scenario: YAML, ENV, and CLI
- **WHEN** YAML, ENV var, and CLI flag exist for a parameter
- **THEN** system uses CLI flag value (CLI overrides all)

#### Scenario: Priority order verification
- **WHEN** config.yaml has batch_size=20, ENV has DECKDEX_PROCESSING_BATCH_SIZE=30, CLI has --batch-size 40
- **THEN** system uses batch_size=40

### Requirement: Deep merge for profiles

The system SHALL perform deep merge when combining default profile with selected profile.

#### Scenario: Partial override in profile
- **WHEN** development profile only specifies processing.batch_size=10
- **THEN** system uses batch_size=10 from development and other processing.* values from default

#### Scenario: Nested section override
- **WHEN** production profile specifies api.scryfall.max_retries=5
- **THEN** system uses max_retries=5 from production and other api.scryfall.* values from default

#### Scenario: Complete section override
- **WHEN** profile specifies entire "processing" section
- **THEN** system replaces all processing.* values with profile values

### Requirement: Configuration loader module

The system SHALL provide a config_loader.py module with configuration loading functions.

#### Scenario: Load config function
- **WHEN** code calls load_config(profile="development")
- **THEN** function returns fully configured ProcessorConfig instance with merged values

#### Scenario: Load YAML function
- **WHEN** code calls load_yaml_config(config_path, profile)
- **THEN** function returns dictionary with merged YAML configuration

#### Scenario: Apply env overrides function
- **WHEN** code calls apply_env_overrides(config_dict)
- **THEN** function returns dictionary with environment variable overrides applied

#### Scenario: Build processor config function
- **WHEN** code calls build_processor_config(yaml_config, cli_overrides)
- **THEN** function returns ProcessorConfig instance with nested config objects

### Requirement: Configuration validation

The system SHALL validate configuration values at load time using dataclass validation.

#### Scenario: Valid configuration
- **WHEN** all configuration values are within valid ranges
- **THEN** config loads successfully without errors

#### Scenario: Invalid batch size from YAML
- **WHEN** config.yaml contains batch_size: 0
- **THEN** system raises ValueError during config load with message "batch_size must be > 0"

#### Scenario: Invalid worker count from ENV
- **WHEN** environment variable DECKDEX_PROCESSING_MAX_WORKERS=15 is set
- **THEN** system raises ValueError during config load with message "max_workers must be between 1 and 10"

#### Scenario: Invalid API delay from CLI
- **WHEN** user runs with --api-delay -0.5
- **THEN** system exits with error message "api_delay must be >= 0"

### Requirement: Configuration debugging

The system SHALL provide mechanisms to inspect resolved configuration.

#### Scenario: Show resolved config
- **WHEN** user runs with --show-config flag
- **THEN** system displays resolved configuration with all values and exits without processing

#### Scenario: Show config with profile
- **WHEN** user runs with --profile production --show-config
- **THEN** system displays production profile configuration and exits

#### Scenario: Show config with overrides
- **WHEN** user runs with --profile production --batch-size 100 --show-config
- **THEN** system displays configuration with CLI overrides applied

### Requirement: Configuration example template

The system SHALL provide a config.example.yaml file documenting all available options.

#### Scenario: Example file exists
- **WHEN** repository is cloned
- **THEN** config.example.yaml file exists in root directory

#### Scenario: Example contains all sections
- **WHEN** user reads config.example.yaml
- **THEN** file contains documented examples for default, development, and production profiles

#### Scenario: Example contains comments
- **WHEN** user reads config.example.yaml
- **THEN** each configuration parameter includes explanatory comment

### Requirement: Backwards compatibility with secrets

The system SHALL preserve existing environment variable conventions for secrets.

#### Scenario: Google credentials environment variable
- **WHEN** GOOGLE_API_CREDENTIALS environment variable is set
- **THEN** system uses this path for Google API credentials (not in YAML)

#### Scenario: OpenAI API key environment variable
- **WHEN** OPENAI_API_KEY environment variable is set
- **THEN** system uses this key for OpenAI authentication (not in YAML)

#### Scenario: Legacy environment variables
- **WHEN** user has existing environment variables set (GOOGLE_API_CREDENTIALS, OPENAI_API_KEY, OPENAI_MODEL)
- **THEN** system continues to work without requiring migration

### Requirement: Type conversion for environment variables

The system SHALL automatically convert environment variable string values to appropriate types.

#### Scenario: Integer conversion
- **WHEN** environment variable DECKDEX_PROCESSING_BATCH_SIZE="30" is set
- **THEN** system converts to integer 30

#### Scenario: Float conversion
- **WHEN** environment variable DECKDEX_PROCESSING_API_DELAY="0.15" is set
- **THEN** system converts to float 0.15

#### Scenario: Boolean true conversion
- **WHEN** environment variable DECKDEX_OPENAI_ENABLED="true" or "1" or "yes" is set
- **THEN** system converts to boolean True

#### Scenario: Boolean false conversion
- **WHEN** environment variable DECKDEX_OPENAI_ENABLED="false" or "0" or "no" is set
- **THEN** system converts to boolean False

#### Scenario: String preservation
- **WHEN** environment variable cannot be parsed as int, float, or bool
- **THEN** system keeps value as string
