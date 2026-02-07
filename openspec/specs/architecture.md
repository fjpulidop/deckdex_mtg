# Architecture Specification

## Summary

This document describes the overall architecture of DeckDex MTG. It is focused on high-level components, data flow, integration points, and non-functional requirements to guide maintainers and future contributors.

## Goals

- Provide a robust CLI-first tool that syncs Magic: The Gathering card data from Scryfall into Google Sheets.
- Optionally enrich card records using the OpenAI API.
- Keep price data current while minimizing API calls and cost.
- Be testable, maintainable, and easy to run in local or CI environments.

## High-level Components

1. CLI / Interactive CLI
   - Entrypoint: `main.py`
   - Orchestrates tasks with comprehensive argument parsing for performance tuning, Google Sheets configuration, and processing control.
   - Provides 16+ configuration options including profile, config, show-config, batch-size, workers, api-delay, sheet-name, credentials-path, limit, resume-from, dry-run, verbose.

2. Configuration Management
   - Module: `deckdex/config_loader.py`
   - Loads configuration from config.yaml with profile support (default, development, production).
   - Merges environment variables (DECKDEX_* prefix) and CLI flags using strict priority hierarchy.
   - Validates all parameters and provides nested configuration objects (ProcessingConfig, ScryfallConfig, GoogleSheetsConfig, OpenAIConfig) to subsystems.
   - Supports --show-config flag for debugging resolved configuration.

3. Scryfall Fetcher
   - Module: `deckdex/card_fetcher.py`
   - Responsible for querying Scryfall API, normalizing responses, and caching results.
   - Uses persistent HTTP sessions and rate-limit/backoff handling.
   - Configured via ScryfallConfig (max_retries, retry_delay, timeout).

4. Google Sheets Sync
   - Module: `deckdex/spreadsheet_client.py`
   - Translates internal card models to sheet rows and performs batched updates to minimize API calls.
   - Manages authentication via Google Service Account credentials JSON.
   - Supports incremental price writes for better progress visibility and resilience.
   - Configured via GoogleSheetsConfig (batch_size, max_retries, retry_delay, sheet_name, worksheet_name).

5. Enrichment Service (Optional)
   - Module: `deckdex/card_fetcher.py` (integrated)
   - Calls OpenAI to generate game strategy and tier metadata.
   - Runs optionally per-card or in batches; results are cached to avoid duplicate calls.
   - Configured via OpenAIConfig (enabled, model, max_tokens, temperature, max_retries).

6. Price Updater
   - Compares current prices with new Scryfall prices and only writes changed values.
   - Uses incremental buffered writes (configurable via write_buffer_batches) to Google Sheets.
   - Writes prices as numeric values for spreadsheet calculations.
   - Generates CSV error reports for failed card lookups.

7. Worker / Executor
   - Uses ThreadPoolExecutor for parallel processing of cards.
   - Ensures thread-safe Google Sheets batching and rate-limit compliance.
   - Parallelism level configured via ProcessingConfig.max_workers.

8. Caching & Persistence
   - In-memory LRU caches for short-term API responses.
   - Optional local persistence (JSON or lightweight DB) for price history and deduplication.

## Data Flow

1. Configuration Management loads config.yaml (with selected profile), applies environment variable overrides (DECKDEX_*), merges CLI flag overrides, validates parameters, and creates ProcessorConfig instance.
2. User provides a list of card names in the Google Sheet (column `English name` or `Name`).
3. CLI reads sheet rows, queues card names for processing.
4. For each card:
   - Check cache and local persistence.
   - Fetch card data from Scryfall (using ScryfallConfig parameters).
   - Optionally call OpenAI to enrich metadata (if OpenAIConfig.enabled).
   - Compute price delta and prepare sheet update.
5. Batch updates are sent back to Google Sheets incrementally (configurable via ProcessingConfig.write_buffer_batches).

## Integration Points

- Configuration files (config.yaml): define operational parameters, performance tuning, and profile-based settings for different environments (default, development, production).
- Environment variables (DECKDEX_* prefix): override configuration parameters; GOOGLE_API_CREDENTIALS and OPENAI_API_KEY for secrets.
- Scryfall API: primary source of card metadata and pricing.
- Google Sheets API: primary storage and user-facing surface.
- OpenAI API: optional enrichment provider.

## Non-functional Requirements

- Performance: Runtime-configurable parallel processing (workers), batch sizing, API delays, and retry attempts via config.yaml profiles, environment variables (DECKDEX_* prefix), and CLI arguments with strict priority hierarchy (YAML < ENV < CLI).
- Cost-efficiency: Batch updates and selective price writes to minimize API usage; incremental writes reduce data loss window.
- Reliability: Retries with exponential backoff and robust error handling; CSV error reports for failed lookups.
- Observability: Two-tier logging system with normal mode (progress bars + errors) and verbose mode (detailed per-card/batch info); dry-run mode for testing without side effects; --show-config flag for configuration debugging.

## Security and Secrets

- Google credentials JSON path and OPENAI_API_KEY MUST be stored as environment variables (GOOGLE_API_CREDENTIALS, OPENAI_API_KEY).
- Configuration files (config.yaml) MUST NOT contain secrets or API keys - only operational parameters (batch sizes, retry counts, delays).
- config.yaml is safe to commit to version control as it contains only operational parameters, not secrets.
- Least-privilege Google service account recommended (only Sheets scopes needed).

## Suggested Next Steps

- Add simple architecture diagram (SVG or ASCII) to docs showing configuration flow.
- Define a small schema for persisted price history to enable rollbacks and audits.
- Add configuration schema validation (jsonschema) for stricter YAML validation.
- Support configuration file auto-discovery ($HOME/.deckdex/config.yaml).
- Add configuration hot-reload for long-running processes.

