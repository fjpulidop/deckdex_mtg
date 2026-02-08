# CLI Interface

Single entry `main.py`. No args → process all with defaults. --help: full options, defaults, examples.

**Flags:** --use_openai, --update_prices, --dry-run, --verbose/-v. **Performance:** --batch-size, --workers (1–10), --api-delay (≥0), --max-retries (≥1); invalid → exit with clear message. **Sheets:** --credentials-path, --sheet-name, --worksheet-name. **Control:** --limit (≥1), --resume-from (≥1). **Config:** --profile (default|development|production), --config path, --set key=value, --show-config (print resolved, exit). Help documents profile, config file, --show-config. Combine flags; missing/invalid profile → warn and use default; missing config file → built-in defaults.
