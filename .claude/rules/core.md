---
paths:
  - "deckdex/**"
---

# Core Package Conventions (deckdex/)

- Zero framework imports. No FastAPI, no React, no web framework dependencies. Stdlib + root `requirements.txt` only.
- Config always via `config_loader.py`. Never hardcode paths, URLs, or secrets.
- All DB operations through `storage/repository.py`. No raw SQL elsewhere in the codebase.
- Secrets via environment variables only — never in code or `config.yaml`.
- Scryfall API calls go through `card_fetcher.py`. No direct HTTP calls to Scryfall elsewhere.
- Google Sheets access via `spreadsheet_client.py`. Use `dry_run_client.py` for simulated writes.
- Processing logic lives in `magic_card_processor.py`. This is the core orchestrator.
- Logging via `logger_config.py`. Use stdlib `logging`, support `--verbose`/`--quiet` flags.
