# CLI Interface Specification (Delta)

## Summary

Delta spec for cli-interface capability. Adds profile selection, configuration file specification, and configuration debugging flags.

## ADDED Requirements

### Requirement: Profile selection flag

The system SHALL accept a --profile flag to select configuration profile.

#### Scenario: Select development profile
- **WHEN** user runs `python main.py --profile development`
- **THEN** system loads development profile from config.yaml with conservative settings

#### Scenario: Select production profile
- **WHEN** user runs `python main.py --profile production`
- **THEN** system loads production profile from config.yaml with aggressive settings

#### Scenario: Default profile
- **WHEN** user runs `python main.py` without --profile flag
- **THEN** system loads default profile from config.yaml

#### Scenario: Invalid profile name
- **WHEN** user runs `python main.py --profile nonexistent`
- **THEN** system logs warning and falls back to default profile

### Requirement: Custom configuration file flag

The system SHALL accept a --config flag to specify custom configuration file path.

#### Scenario: Custom config file
- **WHEN** user runs `python main.py --config /path/to/custom.yaml`
- **THEN** system loads configuration from specified file instead of default config.yaml

#### Scenario: Custom config with profile
- **WHEN** user runs `python main.py --config /path/to/custom.yaml --profile production`
- **THEN** system loads production profile from specified custom file

#### Scenario: Missing custom config file
- **WHEN** user runs `python main.py --config /nonexistent/path.yaml`
- **THEN** system logs warning and falls back to built-in defaults

### Requirement: Configuration debugging flag

The system SHALL accept a --show-config flag to display resolved configuration.

#### Scenario: Show default config
- **WHEN** user runs `python main.py --show-config`
- **THEN** system displays resolved configuration with all values from all sources and exits without processing

#### Scenario: Show config with profile
- **WHEN** user runs `python main.py --profile production --show-config`
- **THEN** system displays production profile configuration with all merged values

#### Scenario: Show config with all overrides
- **WHEN** user runs `python main.py --profile production --batch-size 100 --workers 10 --show-config`
- **THEN** system displays final resolved configuration including CLI overrides

#### Scenario: Show config format
- **WHEN** user runs with --show-config flag
- **THEN** output includes section headers (Processing, API.Scryfall, API.GoogleSheets, API.OpenAI) and all parameter values

### Requirement: Ad-hoc configuration override flag

The system SHALL accept a --set flag for arbitrary configuration overrides.

#### Scenario: Override nested parameter
- **WHEN** user runs `python main.py --set processing.api_delay=0.02`
- **THEN** system sets processing.api_delay to 0.02, overriding all other sources

#### Scenario: Override API parameter
- **WHEN** user runs `python main.py --set api.scryfall.max_retries=10`
- **THEN** system sets api.scryfall.max_retries to 10

#### Scenario: Multiple --set flags
- **WHEN** user runs `python main.py --set processing.batch_size=100 --set processing.max_workers=10`
- **THEN** system applies both overrides

#### Scenario: Invalid --set format
- **WHEN** user runs `python main.py --set invalidformat`
- **THEN** system exits with error message explaining correct format

### Requirement: Help text updates

The system SHALL update help text to document new configuration flags.

#### Scenario: Help includes profile flag
- **WHEN** user runs `python main.py --help`
- **THEN** help text includes --profile flag with description of available profiles

#### Scenario: Help includes config flag
- **WHEN** user runs `python main.py --help`
- **THEN** help text includes --config flag with description and default path

#### Scenario: Help includes show-config flag
- **WHEN** user runs `python main.py --help`
- **THEN** help text includes --show-config flag with description

#### Scenario: Help includes set flag
- **WHEN** user runs `python main.py --help`
- **THEN** help text includes --set flag with format example

#### Scenario: Help includes configuration examples
- **WHEN** user runs `python main.py --help`
- **THEN** examples section includes profile usage and override examples

## MODIFIED Requirements

### Requirement: Backwards compatibility

The system SHALL maintain compatibility with existing command invocations, now loading defaults from config.yaml.

#### Scenario: Legacy basic command with YAML
- **WHEN** user runs `python main.py` as before this change
- **THEN** system loads default profile from config.yaml (same values as previous hardcoded defaults)

#### Scenario: Legacy OpenAI command
- **WHEN** user runs `python main.py --use_openai` as before this change
- **THEN** system behaves identically to previous version (--use_openai sets openai.enabled=true)

#### Scenario: Legacy performance tuning
- **WHEN** user runs `python main.py --batch-size 50 --workers 8` as before this change
- **THEN** CLI flags still override configuration (now from YAML instead of hardcoded)

### Requirement: Argument combination

The system SHALL allow combining new flags with existing arguments.

#### Scenario: Profile with performance tuning
- **WHEN** user runs `python main.py --profile production --batch-size 100`
- **THEN** system loads production profile and overrides batch_size with CLI value

#### Scenario: Custom config with dry-run
- **WHEN** user runs `python main.py --config custom.yaml --dry-run --verbose`
- **THEN** system loads custom.yaml and applies behavioral flags

#### Scenario: Profile with limit and resume
- **WHEN** user runs `python main.py --profile development --limit 10 --resume-from 50`
- **THEN** system loads development profile and applies processing control flags

#### Scenario: All new flags combined
- **WHEN** user runs `python main.py --config custom.yaml --profile production --set processing.batch_size=200 --show-config`
- **THEN** system loads custom.yaml, applies production profile, overrides batch_size, and displays resolved config
