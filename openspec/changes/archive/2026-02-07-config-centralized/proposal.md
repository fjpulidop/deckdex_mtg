## Why

Configuration is currently fragmented with hardcoded values scattered across multiple files (main.py, config.py, card_fetcher.py, spreadsheet_client.py). To optimize processing of thousands of cards, we need to easily adjust performance parameters (batch sizes, workers, delays) without modifying code. Additionally, we want to support different profiles (development, production) with environment-optimized configurations.

## What Changes

- Create `config.yaml` file with three profiles: default, development, production
- Create `config_loader.py` module to load and merge configuration from multiple sources
- Externalize all hardcoded values to configuration
- Support three-level override hierarchy: YAML → Environment Variables → CLI flags
- Restructure `ProcessorConfig` with nested sub-configurations for each subsystem
- Refactor `CardFetcher` and `SpreadsheetClient` to receive explicit configuration
- Add `--profile` flag to CLI for environment selection
- Add `--show-config` flag for configuration debugging
- Maintain backwards compatibility with deprecated properties in `ProcessorConfig`

## Capabilities

### New Capabilities
- `configuration-management`: Centralized configuration system with multi-profile support, override hierarchy (YAML/ENV/CLI), and parameter validation

### Modified Capabilities
- `processor-configuration`: Evolves from simple dataclass to hierarchical system with sub-configs for processing, scryfall, google_sheets, and openai
- `cli-interface`: Adds --profile, --show-config, and --set flags for configuration management
- `architecture`: Integrates config_loader as central component between CLI and subsystems

## Impact

**Affected code:**
- `deckdex/config.py` - Restructure with nested dataclasses
- `deckdex/card_fetcher.py` - Receive ScryfallConfig instead of individual parameters
- `deckdex/spreadsheet_client.py` - Receive GoogleSheetsConfig
- `deckdex/magic_card_processor.py` - Use nested configs from ProcessorConfig
- `main.py` - Integrate config_loader for configuration loading

**New files:**
- `config.yaml` - Main configuration with 3 profiles
- `config.example.yaml` - Documented template for users
- `deckdex/config_loader.py` - Configuration loading and merging logic

**Dependencies:**
- Add `pyyaml` to requirements.txt

**Non-breaking for users:**
- Existing CLI continues working with current default values
- Existing environment variables continue working
