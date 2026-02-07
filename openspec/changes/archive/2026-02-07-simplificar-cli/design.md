## Context

The current DeckDex MTG CLI has evolved organically with hardcoded configuration values spread throughout the codebase. A broken `run_cli.py` entry point imports a non-existent `cli_interactive.py` module, and the README documents features that don't exist. Users have no way to adjust critical parameters like batch size, worker count, or API rate limits without modifying source code, and there's no mechanism to test changes safely before applying them to production Google Sheets.

The system currently uses:
- Hardcoded constants in `MagicCardProcessor` (`BATCH_SIZE=20`, `MAX_RETRIES=5`, etc.)
- Fixed worker count in `ThreadPoolExecutor` calls
- Basic `argparse` in `main.py` with only 2 flags (`--use_openai`, `--update_prices`)
- No validation of configuration values
- No dry-run or verbose logging capabilities

This change consolidates the CLI to a single enhanced entry point, introduces a centralized configuration system with validation, and adds essential debugging/testing capabilities.

## Goals / Non-Goals

**Goals:**
- Single, well-documented CLI entry point with comprehensive options
- Centralized configuration with type safety and validation
- Dry-run mode for safe testing
- Verbose logging for debugging
- Runtime configurability of all performance parameters
- Factory pattern for creating appropriate clients based on configuration
- Backwards compatibility with existing command invocations
- Optimized defaults aligned with API rate limits (Scryfall: 10 req/s)

**Non-Goals:**
- Graphical user interface (project remains terminal-only)
- Interactive/menu-driven CLI (complexity not justified for use case)
- Configuration file support (CLI args sufficient for current needs)
- Persistent configuration/profiles (can be added later if needed)
- Changing core processing logic (only configuration mechanism changes)
- Performance improvements beyond making parameters configurable

## Decisions

### Decision 1: Single Entry Point (main.py only)

**Decision**: Delete `run_cli.py` and consolidate all CLI functionality in `main.py`.

**Rationale**:
- `run_cli.py` imports non-existent `cli_interactive.py` (broken code)
- Interactive CLI mentioned in README was never implemented
- Single entry point reduces maintenance burden and user confusion
- All functionality can be achieved with command-line arguments

**Alternatives considered**:
- Fix `run_cli.py` by implementing `cli_interactive.py`: Adds complexity and maintenance burden for limited benefit. Interactive menus are less automatable than CLI args.
- Keep both entry points: Maintains broken code and split functionality without clear benefit.

**Impact**: Users currently running `python run_cli.py` (if any) must switch to `python main.py` with appropriate flags.

### Decision 2: Dataclass-based Configuration

**Decision**: Create `ProcessorConfig` dataclass with `__post_init__` validation instead of passing individual parameters.

**Rationale**:
- Type safety with Python type hints
- Centralized validation logic in one place
- Easy to extend with new configuration parameters
- Clear contract between CLI and processor
- Testable configuration independent of CLI parsing

**Alternatives considered**:
- Pass individual parameters to constructors: Leads to long parameter lists, no centralized validation, harder to extend.
- Use dict-based configuration: No type safety, runtime errors instead of early validation, harder to document.
- Use external config library (pydantic, attrs): Adds dependency for stdlib-solvable problem.

**Impact**: `MagicCardProcessor.__init__` signature changes from `(use_openai, update_prices)` to accepting `ProcessorConfig`. Class constants become instance attributes.

### Decision 3: Factory Pattern for Client Creation

**Decision**: Implement `ClientFactory.create_spreadsheet_client(config)` that returns `SpreadsheetClient` or `DryRunClient` based on `config.dry_run`.

**Rationale**:
- Encapsulates client creation logic
- Makes dry-run mode transparent to processor
- Easy to test with mock factory
- Follows Open/Closed Principle (can add new client types without modifying processor)

**Alternatives considered**:
- Conditional logic in processor: Spreads dry-run handling throughout codebase, harder to test.
- Subclass MagicCardProcessor for dry-run: Code duplication, harder to maintain.
- Pass dry_run flag to every write method: Pollutes method signatures, error-prone.

**Impact**: New `ClientFactory` class in `deckdex/config.py`. Processor uses factory instead of directly instantiating `SpreadsheetClient`.

### Decision 4: DryRunClient Interface Compatibility

**Decision**: `DryRunClient` implements same interface as `SpreadsheetClient` but logs operations instead of executing them.

**Rationale**:
- Transparent to processor (no conditional logic needed)
- Can be tested independently
- Makes real API calls to Scryfall/OpenAI (validates those integrations)
- Skips only Google Sheets writes (the side-effectful operations)

**Alternatives considered**:
- Mock all API calls in dry-run: Doesn't validate API integrations, less useful for testing.
- Add dry_run parameter to every method: Spreads complexity, harder to ensure all paths are covered.
- Use dependency injection framework: Overkill for this use case.

**Impact**: New `deckdex/dry_run_client.py` module. Collects statistics about operations that would be performed.

### Decision 5: Two-Tier Logging System

**Decision**: Normal mode (INFO level, progress bars) vs Verbose mode (DEBUG level, per-card details).

**Rationale**:
- Normal mode is clean for production use
- Verbose mode provides debugging without code changes
- Progressive disclosure (don't overwhelm users by default)
- Uses existing loguru infrastructure

**Alternatives considered**:
- Single verbosity level: Either too noisy or not detailed enough.
- Multiple verbosity levels (v, vv, vvv): Added complexity without clear benefit for this application.
- Always verbose: Overwhelming for normal use, harder to spot issues in noise.

**Impact**: New `deckdex/logger_config.py` module. `main.py` calls `configure_logging(verbose)` at startup.

### Decision 6: API Delay Default 0.05s → 0.1s

**Decision**: Change default API delay from 50ms to 100ms (0.1s).

**Rationale**:
- Scryfall API limit is 10 requests/second (100ms minimum)
- Current 50ms default risks hitting rate limit with parallel workers
- Being conservative avoids 429 errors and potential IP blocking
- Users can override with `--api-delay` if they want to be more aggressive

**Alternatives considered**:
- Keep 50ms default: Risks rate limiting, especially with multiple workers.
- Use adaptive rate limiting: Added complexity, harder to reason about, not needed for current scale.
- Use 150ms or 200ms: Overly conservative, unnecessarily slow.

**Impact**: Better rate limit compliance by default, slightly slower processing (50ms/card difference negligible for typical workloads).

### Decision 7: Argument Naming Convention

**Decision**: Use kebab-case for multi-word arguments (`--batch-size`, `--api-delay`) and preserve underscores for existing args (`--use_openai`, `--update_prices`).

**Rationale**:
- Kebab-case is standard for CLI tools (git, docker, kubectl, etc.)
- Preserving existing underscore args maintains backwards compatibility
- argparse automatically converts hyphens to underscores in dest

**Alternatives considered**:
- All underscores: Less conventional for CLI tools.
- Rename existing args to kebab-case: Breaking change, not justified.
- All kebab-case with deprecated underscore aliases: Added complexity for minor benefit.

**Impact**: Mixed naming convention is slightly inconsistent but maintains compatibility.

### Decision 8: Validation Location

**Decision**: Validate configuration values in `ProcessorConfig.__post_init__` rather than in argparse or processor methods.

**Rationale**:
- Single source of truth for validation rules
- Configuration is validated regardless of how it's created (CLI, tests, future APIs)
- Clear error messages with specific field names
- Testable independently of CLI

**Alternatives considered**:
- Validate in argparse: Duplicates validation if config is created programmatically.
- Validate in processor methods: Fails late, spreads validation logic.
- No validation: Runtime errors, poor user experience.

**Impact**: Validation errors raised at config creation time with clear messages.

## Risks / Trade-offs

### Risk: Mixed naming convention (kebab-case + underscores)
**Mitigation**: Document clearly in help text and README. Acceptable trade-off for backwards compatibility.

### Risk: DryRunClient interface drift
**Mitigation**: Use protocol/ABC to enforce interface compatibility. Add integration tests that verify both clients work with processor.

### Risk: Changed default API delay affects existing users
**Mitigation**: New default (0.1s) matches API limits and prevents rate limit errors. Actual impact is 50ms per card (negligible). Users can override with `--api-delay 0.05` if they want old behavior.

### Risk: Breaking change if users modify BATCH_SIZE constants
**Mitigation**: Class constants still exist but are unused. Add deprecation warnings. Provide migration guide in README.

### Risk: Verbose logging performance impact
**Mitigation**: Verbose mode is opt-in. Per-card logging has minimal overhead compared to API calls (network I/O dominates).

### Risk: Dry-run mode makes real API calls (costs money)
**Mitigation**: Documented clearly in help text and output banner. This is intentional design to validate API integrations. Users wanting to avoid API costs should test with `--limit 1`.

### Risk: Factory pattern adds indirection
**Mitigation**: Simple factory with clear purpose. Improved testability and maintainability outweigh slight indirection cost.

## Migration Plan

### Phase 1: Implementation (this change)
1. Create new modules: `config.py`, `dry_run_client.py`, `logger_config.py`
2. Refactor `MagicCardProcessor` to accept `ProcessorConfig`
3. Enhance `main.py` with new argument parsing
4. Delete `run_cli.py`
5. Update README to remove interactive CLI references and document new options
6. Rename `tests/test_cli.py` → `tests/test_main.py` and add new test cases

### Phase 2: Validation
- Run existing test suite (backwards compatibility check)
- Test with `--dry-run --verbose --limit 5` on production data
- Verify `python main.py` still works with no args
- Verify `python main.py --use_openai` still works

### Phase 3: Documentation
- Update README with CLI options table
- Add usage examples for common workflows
- Document migration for any users of `run_cli.py`

### Rollback Strategy
- Git revert is straightforward (no database migrations, no API changes)
- Backwards compatible: old commands still work
- If issues found, revert commit and investigate

### Deployment Notes
- No infrastructure changes required
- No dependency updates required (uses stdlib only)
- Safe to deploy: defaults match existing behavior

## Open Questions

None - design is complete and ready for implementation.
