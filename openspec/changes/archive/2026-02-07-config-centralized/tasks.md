## 1. Add Configuration Infrastructure

- [x] 1.1 Add pyyaml dependency to requirements.txt
- [x] 1.2 Create config.yaml with default profile matching current hardcoded values
- [x] 1.3 Create config.example.yaml as documented template with comments
- [x] 1.4 Create deckdex/config_loader.py module skeleton
- [x] 1.5 Implement load_yaml_config() function in config_loader
- [x] 1.6 Implement _deep_merge() helper function for profile merging
- [x] 1.7 Implement apply_env_overrides() function for DECKDEX_* variables
- [x] 1.8 Implement build_processor_config() function
- [x] 1.9 Implement load_config() main entry point function

## 2. Enhance ProcessorConfig with Nested Dataclasses

- [x] 2.1 Create ProcessingConfig dataclass in deckdex/config.py
- [x] 2.2 Add __post_init__ validation to ProcessingConfig
- [x] 2.3 Create ScryfallConfig dataclass in deckdex/config.py
- [x] 2.4 Add __post_init__ validation to ScryfallConfig
- [x] 2.5 Create GoogleSheetsConfig dataclass in deckdex/config.py
- [x] 2.6 Add __post_init__ validation to GoogleSheetsConfig
- [x] 2.7 Create OpenAIConfig dataclass in deckdex/config.py
- [x] 2.8 Add __post_init__ validation to OpenAIConfig
- [x] 2.9 Update ProcessorConfig to use nested config objects
- [x] 2.10 Add backwards compatibility properties to ProcessorConfig (batch_size, max_workers, api_delay, use_openai, sheet_name, worksheet_name)
- [x] 2.11 Remove redundant validation from ProcessorConfig.__post_init__ (now in nested configs)

## 3. Add CLI Flags for Configuration Management

- [x] 3.1 Add --profile argument to argparse in main.py
- [x] 3.2 Add --config argument to argparse for custom config file path
- [x] 3.3 Add --show-config flag to argparse
- [x] 3.4 Add --set argument for ad-hoc overrides (deferred as optional - not critical for MVP)
- [x] 3.5 Update help text with configuration examples
- [x] 3.6 Update epilog section with profile usage examples

## 4. Integrate config_loader into main.py

- [x] 4.1 Import load_config from deckdex.config_loader in main.py
- [x] 4.2 Replace manual ProcessorConfig instantiation with load_config() call
- [x] 4.3 Pass profile and config_path from CLI args to load_config()
- [x] 4.4 Pass cli_overrides dict from parsed args to load_config()
- [x] 4.5 Implement --show-config handler to display resolved configuration
- [x] 4.6 Add configuration display formatting function
- [x] 4.7 Test that existing CLI commands work with new config system

## 5. Refactor CardFetcher to Accept ScryfallConfig

- [x] 5.1 Update CardFetcher.__init__ signature to accept ScryfallConfig
- [x] 5.2 Replace hardcoded CardFetcher defaults with config values (max_retries, retry_delay)
- [x] 5.3 Add timeout parameter to CardFetcher from ScryfallConfig
- [x] 5.4 Update CardFetcher._make_request to use config.timeout
- [x] 5.5 Update openai_model from environment to config.openai.model
- [x] 5.6 Update MagicCardProcessor._initialize_clients to pass config.scryfall to CardFetcher

## 6. Refactor SpreadsheetClient to Accept GoogleSheetsConfig

- [x] 6.1 Update SpreadsheetClient.__init__ signature to accept GoogleSheetsConfig
- [x] 6.2 Replace hardcoded SpreadsheetClient constants with config values (BATCH_SIZE, max_retries, base_delay)
- [x] 6.3 Update _ensure_connection to use config.max_retries and config.retry_delay
- [x] 6.4 Update _batch_update_with_retry to use config values
- [x] 6.5 Update _update_range_with_retry to use config values
- [x] 6.6 Update ClientFactory.create_spreadsheet_client to pass config.google_sheets to SpreadsheetClient

## 7. Update MagicCardProcessor to Use Nested Configs

- [x] 7.1 Update _initialize_clients to use config.scryfall and config.google_sheets
- [x] 7.2 Replace self.batch_size with config.processing.batch_size throughout
- [x] 7.3 Replace self.max_workers with config.processing.max_workers throughout
- [x] 7.4 Replace self.api_delay with config.processing.api_delay throughout
- [x] 7.5 Replace self.max_retries with appropriate nested config (scryfall or google_sheets)
- [x] 7.6 Update self.use_openai to use config.openai.enabled
- [x] 7.7 Verify all legacy properties still work via backwards compatibility

## 8. Add Development and Production Profiles

- [x] 8.1 Add development profile to config.yaml with conservative settings (batch_size=10, max_workers=2, api_delay=0.2)
- [x] 8.2 Add production profile to config.yaml with aggressive settings (batch_size=50, max_workers=8, api_delay=0.05)
- [x] 8.3 Document profile differences in config.example.yaml
- [x] 8.4 Test --profile development loads correct values
- [x] 8.5 Test --profile production loads correct values
- [x] 8.6 Test profile merging (development overrides only specified values)

## 9. Testing and Validation

- [x] 9.1 Add unit tests for load_yaml_config with different profiles
- [x] 9.2 Add unit tests for _deep_merge function
- [x] 9.3 Add unit tests for apply_env_overrides with various DECKDEX_* variables
- [x] 9.4 Add unit tests for type conversion (int, float, bool, string)
- [x] 9.5 Add unit tests for nested config dataclass validation
- [x] 9.6 Add integration test for full config loading pipeline
- [x] 9.7 Add integration test for priority order (YAML < ENV < CLI)
- [x] 9.8 Test that existing commands work without changes
- [x] 9.9 Test error cases (invalid values, missing files, invalid profiles)
- [x] 9.10 Verify --show-config displays correct resolved values

## 10. Documentation

- [x] 10.1 Add Configuration section to README.md
- [x] 10.2 Document profile usage (default, development, production)
- [x] 10.3 Document environment variable mapping (DECKDEX_* convention)
- [x] 10.4 Document override priority (YAML → ENV → CLI)
- [x] 10.5 Add examples for common configuration scenarios
- [x] 10.6 Document --show-config flag usage
- [x] 10.7 Update openspec/specs/architecture.md with Configuration Management component
- [x] 10.8 Update openspec/specs/processor-configuration/spec.md if needed (merge delta spec)
- [x] 10.9 Update openspec/specs/cli-interface/spec.md if needed (merge delta spec)
- [x] 10.10 Add migration guide for users with custom scripts

## 11. Cleanup and Polish

- [x] 11.1 Remove deprecated class constants from MagicCardProcessor (BATCH_SIZE, MAX_RETRIES, etc.)
- [x] 11.2 Add deprecation warnings to legacy properties in ProcessorConfig
- [x] 11.3 Verify no hardcoded values remain in codebase
- [x] 11.4 Run linter and fix any issues
- [x] 11.5 Verify type hints are correct on all new code
- [x] 11.6 Add docstrings to all new functions and classes
- [x] 11.7 Ensure config.yaml and config.example.yaml are in .gitignore (if needed)
- [x] 11.8 Verify config.example.yaml is comprehensive and well-documented
