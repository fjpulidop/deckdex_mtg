# Architecture Specification (Delta)

## Summary

Delta spec for architecture capability. Integrates configuration management system as a central component in the architecture.

## ADDED Requirements

### Requirement: Configuration Management Component

The system SHALL include a Configuration Management component responsible for loading and merging configuration from multiple sources.

#### Scenario: Component responsibilities
- **WHEN** system architecture is documented
- **THEN** Configuration Management component is listed with responsibilities: load YAML files, apply environment overrides, merge CLI flags, validate parameters, create ProcessorConfig instances

#### Scenario: Component location
- **WHEN** Configuration Management component is implemented
- **THEN** component resides in deckdex/config_loader.py module

#### Scenario: Component dependencies
- **WHEN** Configuration Management component is initialized
- **THEN** component depends on pyyaml library and deckdex/config.py module

## MODIFIED Requirements

### Requirement: High-level Components

The system SHALL document Configuration Management as a component between CLI and processing subsystems.

#### Scenario: Updated component list
- **WHEN** architecture documentation lists high-level components
- **THEN** list includes: (1) CLI, (2) Configuration Management [NEW], (3) Scryfall Fetcher, (4) Google Sheets Sync, (5) Enrichment Service, (6) Price Updater, (7) Worker/Executor, (8) Caching & Persistence

#### Scenario: Configuration Management description
- **WHEN** Configuration Management component is described
- **THEN** description includes: "Loads configuration from config.yaml with profile support (default, development, production). Merges environment variables (DECKDEX_* prefix) and CLI flags using strict priority hierarchy. Validates all parameters and provides nested configuration objects (ProcessingConfig, ScryfallConfig, GoogleSheetsConfig, OpenAIConfig) to subsystems."

### Requirement: Data Flow

The system SHALL update data flow to include configuration loading step.

#### Scenario: Updated data flow
- **WHEN** data flow is documented
- **THEN** flow includes new step 0: "Configuration Management loads config.yaml (with selected profile), applies environment variable overrides (DECKDEX_*), merges CLI flag overrides, validates parameters, and creates ProcessorConfig instance"

#### Scenario: Configuration flow to subsystems
- **WHEN** data flow shows processor initialization
- **THEN** flow shows ProcessorConfig passed to MagicCardProcessor, which distributes nested configs to CardFetcher (ScryfallConfig), SpreadsheetClient (GoogleSheetsConfig), and enrichment service (OpenAIConfig)

### Requirement: Integration Points

The system SHALL document configuration files as an integration point.

#### Scenario: Configuration file integration
- **WHEN** integration points are documented
- **THEN** list includes: "Configuration files (config.yaml): define operational parameters, performance tuning, and profile-based settings for different environments"

#### Scenario: Environment variables integration
- **WHEN** integration points are documented
- **THEN** environment variables section includes: "DECKDEX_* variables for configuration overrides in addition to existing GOOGLE_API_CREDENTIALS, OPENAI_API_KEY, OPENAI_MODEL for secrets"

### Requirement: Non-functional Requirements

The system SHALL update performance and observability requirements to reference configuration system.

#### Scenario: Performance configurability
- **WHEN** performance requirements are documented
- **THEN** text updated to: "Runtime-configurable parallel processing (workers), batch sizing, API delays, and retry attempts via config.yaml profiles, environment variables (DECKDEX_* prefix), and CLI arguments with strict priority hierarchy"

#### Scenario: Configuration observability
- **WHEN** observability requirements are documented
- **THEN** text includes: "Configuration debugging via --show-config flag displays resolved values from all sources (YAML, ENV, CLI) to aid troubleshooting"

### Requirement: Security and Secrets

The system SHALL clarify that secrets remain in environment variables, not configuration files.

#### Scenario: Secrets exclusion from config files
- **WHEN** security requirements are documented
- **THEN** text clarifies: "Google credentials JSON path and OPENAI_API_KEY MUST be stored as environment variables (GOOGLE_API_CREDENTIALS, OPENAI_API_KEY). Configuration files (config.yaml) MUST NOT contain secrets or API keys."

#### Scenario: Config file safety
- **WHEN** security requirements are documented
- **THEN** text includes: "config.yaml is safe to commit to version control as it contains only operational parameters (batch sizes, retry counts, delays), not secrets"

### Requirement: Suggested Next Steps

The system SHALL update suggested next steps to reflect configuration system completion.

#### Scenario: Completed configuration item
- **WHEN** suggested next steps are listed
- **THEN** previous item "Define centralized configuration system" is removed (now implemented)

#### Scenario: New configuration-related suggestions
- **WHEN** suggested next steps are listed
- **THEN** list may include: "Add configuration schema validation (jsonschema)", "Support configuration file auto-discovery ($HOME/.deckdex/config.yaml)", "Add configuration hot-reload for long-running processes"
