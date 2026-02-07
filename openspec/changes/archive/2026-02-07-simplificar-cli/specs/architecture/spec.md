# Architecture Specification Delta

## Summary

This delta modifies the CLI component of the architecture to reflect the simplified, enhanced single entry point design.

## MODIFIED Requirements

### Requirement: CLI / Interactive CLI

The system SHALL provide a single CLI entry point at `main.py` with comprehensive configuration options.

**Modified from original**:
- **OLD**: Entrypoints: `main.py`, `run_cli.py` - Orchestrates tasks, parses flags, and exposes user flows (process cards, update prices, configure credentials).
- **NEW**: Entrypoint: `main.py` only - Orchestrates tasks with comprehensive argument parsing for performance tuning, Google Sheets configuration, and processing control.

#### Scenario: Single entry point
- **WHEN** user wants to run the application
- **THEN** user invokes `python main.py` with appropriate flags (no separate interactive CLI)

#### Scenario: Enhanced configuration
- **WHEN** user runs main.py
- **THEN** CLI accepts 13+ configuration options including batch-size, workers, api-delay, sheet-name, credentials-path, limit, resume-from, dry-run, verbose

#### Scenario: Help documentation
- **WHEN** user runs `python main.py --help`
- **THEN** system displays comprehensive help with all options, defaults, and usage examples

### Requirement: Non-functional Requirements - Observability

The system SHALL provide configurable observability with normal and verbose logging modes.

**Modified from original**:
- **OLD**: Observability: CLI output and optional verbose logging; structured logs for CI runs.
- **NEW**: Observability: Two-tier logging system with normal mode (progress bars + errors) and verbose mode (detailed per-card/batch info); dry-run mode for testing without side effects.

#### Scenario: Normal observability
- **WHEN** user runs without --verbose flag
- **THEN** system displays progress bars, error counts, and completion status

#### Scenario: Verbose observability
- **WHEN** user runs with --verbose flag
- **THEN** system displays detailed per-card fetch times, batch write times, and comprehensive statistics

#### Scenario: Dry-run observability
- **WHEN** user runs with --dry-run flag
- **THEN** system shows what would be executed without making changes, with full operation logging

### Requirement: Non-functional Requirements - Performance

The system SHALL support runtime configuration of performance parameters.

**Modified from original**:
- **OLD**: Performance: Parallel processing with configurable worker count.
- **NEW**: Performance: Runtime-configurable parallel processing (workers), batch sizing, API delays, and retry attempts via CLI arguments.

#### Scenario: Configure workers at runtime
- **WHEN** user runs `python main.py --workers 8`
- **THEN** system uses 8 parallel workers without code modification

#### Scenario: Configure batch size at runtime
- **WHEN** user runs `python main.py --batch-size 50`
- **THEN** system processes cards in batches of 50

#### Scenario: Configure API rate limiting at runtime
- **WHEN** user runs `python main.py --api-delay 0.2`
- **THEN** system waits 0.2s between API requests

## REMOVED Requirements

### Requirement: Interactive CLI entrypoint

**Reason**: The interactive CLI (`run_cli.py`) was never fully implemented and imports non-existent `cli_interactive.py` module. Removing to eliminate broken code and reduce maintenance burden.

**Migration**: All functionality is available through enhanced `main.py` with command-line arguments. Users should use `python main.py` with appropriate flags instead of `python run_cli.py`.

#### Scenario: Previous interactive CLI users
- **WHEN** user previously ran `python run_cli.py`
- **THEN** user should now run `python main.py` with appropriate flags (e.g., `python main.py --use_openai --verbose`)
