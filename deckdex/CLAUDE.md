# deckdex/

Core package. Card processing, config, Google Sheets client, storage layer. Used by the backend API and CLI. No framework deps — stdlib + root `requirements.txt` only.

## Commands

```bash
pytest tests/          # from repo root
python main.py         # CLI entrypoint
python main.py --help
```

## File map

```
deckdex/
  config.py                 → Config dataclass + validation
  config_loader.py          → Load YAML + env overrides
  card_fetcher.py           → Scryfall API calls
  magic_card_processor.py   → Core processing logic
  spreadsheet_client.py     → Google Sheets (gspread)
  dry_run_client.py         → Simulates writes without side effects
  logger_config.py          → Logging setup
  storage/
    repository.py           → All DB operations (SQLAlchemy)
```

## Conventions

- No FastAPI, no React, no framework imports. Keep dependencies minimal.
- Config: always load through `config_loader.py`. No hardcoded values or paths.
- DB ops: always through `storage/repository.py`. No raw SQL elsewhere.
- Secrets: env vars only — never in code or `config.yaml`.
