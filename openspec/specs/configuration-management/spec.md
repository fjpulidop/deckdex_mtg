# Configuration

Centralized config: YAML profiles, ENV (DECKDEX_*), CLI overrides; priority YAML < ENV < CLI. Nested dataclasses with validation.

## Sources and priority

- **YAML:** `config.yaml` with profiles (default, development, production). Deep-merge selected profile over default. Missing file → built-in defaults.
- **ENV:** DECKDEX_SECTION_KEY (e.g. DECKDEX_PROCESSING_BATCH_SIZE=30). Type conversion: int, float, bool ("true"/"1"/"yes" → True). Invalid pattern ignored.
- **CLI:** --profile, --config /path, --batch-size, --workers, etc. Highest priority. --set key=value for ad-hoc.
- **Secrets:** GOOGLE_API_CREDENTIALS, OPENAI_API_KEY (env only; never in YAML). Legacy OPENAI_MODEL supported.

## Structure (YAML)

- `processing`: batch_size, max_workers, api_delay, write_buffer_batches
- `api.scryfall`: max_retries, retry_delay, timeout
- `api.google_sheets`: batch_size, max_retries, retry_delay, sheet_name, worksheet_name
- `api.openai`: enabled, model, max_tokens, temperature, max_retries

## ProcessorConfig (deckdex/config.py)

- **ProcessorConfig** holds nested: ProcessingConfig, ScryfallConfig, GoogleSheetsConfig, OpenAIConfig; plus credentials_path, limit, resume_from, update_prices, dry_run, verbose.
- **ProcessingConfig:** batch_size (default 20), max_workers (1–10), api_delay (≥0), write_buffer_batches (default 3).
- **ScryfallConfig:** max_retries (≥1), retry_delay, timeout.
- **GoogleSheetsConfig:** batch_size, max_retries, retry_delay, sheet_name, worksheet_name.
- **OpenAIConfig:** enabled (default false), model (gpt-3.5-turbo), max_tokens, temperature (0–1), max_retries.
- Validation in `__post_init__`: e.g. batch_size > 0, max_workers 1–10, api_delay ≥ 0; ValueError with clear message.
- Deprecated flat properties (batch_size, max_workers, api_delay, use_openai, sheet_name, worksheet_name) delegate to nested config and emit DeprecationWarning.

## Loader (config_loader.py)

- `load_config(profile=..., cli_overrides=...)` → ProcessorConfig (merged, validated).
- `load_yaml_config(path, profile)`, `apply_env_overrides(config_dict)`, `build_processor_config(yaml_config, cli_overrides)` available.
- **--show-config:** print resolved config and exit (no processing). Example file: config.example.yaml with all sections and comments.
