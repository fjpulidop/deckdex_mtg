## Why

The current CLI implementation has broken references (`run_cli.py` imports non-existent `cli_interactive.py`), misleading documentation about an interactive CLI that doesn't exist, and hardcoded configuration values that limit flexibility. Users cannot adjust critical parameters like batch size, worker count, or API rate limits without modifying source code, and there's no way to test changes safely (dry-run) or debug issues with verbose logging.

## What Changes

- **DELETE** `run_cli.py` - Remove broken CLI entry point that references missing `cli_interactive.py`
- **ENHANCE** `main.py` - Transform into a comprehensive CLI with advanced argument parsing and configuration options
- **NEW** Configuration system - Centralized `ProcessorConfig` dataclass with validation
- **NEW** Dry-run mode - Simulate execution without writing to Google Sheets
- **NEW** Verbose logging - Configurable detailed output for debugging
- **NEW** Advanced CLI options:
  - `--batch-size N` - Configure batch processing size (default: 20)
  - `--workers N` - Configure parallel worker count (default: 4, range: 1-10)
  - `--api-delay SECONDS` - Configure delay between API requests (default: 0.1s for Scryfall 10 req/s limit)
  - `--max-retries N` - Configure retry attempts for failed requests (default: 5)
  - `--sheet-name NAME` - Process different spreadsheets
  - `--worksheet-name NAME` - Target specific worksheets
  - `--credentials-path PATH` - Override default Google API credentials
  - `--limit N` - Process only N cards (useful for testing)
  - `--resume-from ROW` - Resume processing from specific row
  - `--dry-run` - Simulate without writing
  - `-v / --verbose` - Enable detailed logging
- **REFACTOR** `MagicCardProcessor` - Accept configuration via dataclass instead of hardcoded constants
- **REFACTOR** `CardFetcher` and `SpreadsheetClient` - Accept configuration parameters
- **NEW** Factory pattern - Create appropriate client based on dry-run flag
- **UPDATE** README.md - Remove interactive CLI references, add comprehensive CLI option documentation
- **RENAME** `tests/test_cli.py` → `tests/test_main.py` - Better naming convention
- **UPDATE** Default `api_delay` from 0.05s to 0.1s - Align with Scryfall's 10 requests/second limit

## Capabilities

### New Capabilities

- `cli-interface` - Enhanced command-line interface with comprehensive argument parsing, validation, help text, and usage examples
- `processor-configuration` - Centralized configuration system using dataclass with validation and defaults optimized for API rate limits
- `dry-run-mode` - Simulation mode that fetches from APIs but skips Google Sheets writes, showing what would be changed
- `verbose-logging` - Configurable logging system with normal (progress bars + errors) and verbose (detailed per-card/batch info) modes

### Modified Capabilities

- `architecture` - CLI component changes from dual entry points (main.py + run_cli.py) to single enhanced entry point (main.py only)

## Impact

**Files Modified:**
- `main.py` - Complete refactor with enhanced argument parsing and configuration
- `deckdex/magic_card_processor.py` - Accept configuration dataclass, convert constants to instance attributes
- `deckdex/card_fetcher.py` - Accept configuration for retry/delay settings
- `deckdex/spreadsheet_client.py` - Accept configuration for credentials/sheet names
- `README.md` - Remove lines 85-98 (interactive CLI section) and line 122 (interactive CLI mention), add CLI options table
- `tests/test_cli.py` - Rename to `test_main.py`, add tests for new options

**Files Created:**
- `deckdex/config.py` - Configuration dataclass
- `deckdex/dry_run_client.py` - Mock client for dry-run mode
- `deckdex/logger_config.py` - Centralized logging configuration

**Files Deleted:**
- `run_cli.py` - Broken CLI entry point removed

**Breaking Changes:**
- None - All existing command invocations remain compatible (default values match current hardcoded constants)

**Backwards Compatibility:**
- ✅ `python main.py` - Still works (uses defaults)
- ✅ `python main.py --use_openai` - Still works
- ✅ `python main.py --update_prices` - Still works
- ❌ `python run_cli.py` - No longer works (intentionally removed, was broken)

**Dependencies:**
- No new external dependencies required (uses existing argparse, dataclasses from stdlib)

**Performance:**
- Improved default API delay (0.1s) reduces risk of hitting Scryfall rate limits
- No performance degradation - all defaults match current behavior
- Users can now tune performance parameters for their use case
