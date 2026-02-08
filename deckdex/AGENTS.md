# AGENTS.md — deckdex

## Overview

Core DeckDex package: card processing, config loading, spreadsheet client, storage layer, and CLI/processor entrypoints. Used by the backend API and by standalone CLI. Python 3.x; no framework—plain modules.

## Commands

| Task | Command | Notes |
|------|---------|-------|
| Run tests | `pytest tests/` (from repo root) | Tests for deckdex and backend live under tests/ |
| Run processor | From repo root: `python main.py` or as per README | CLI entrypoint |

See root `AGENTS.md` for project-wide skills and workflow.

## File map

```
deckdex/
  config.py         → Config dataclass / validation
  config_loader.py  → Load YAML and env
  card_fetcher.py   → Card data fetching
  magic_card_processor.py → Core processing logic
  spreadsheet_client.py   → Google Sheets client (gspread)
  dry_run_client.py → Dry-run behavior
  logger_config.py  → Logging setup
  storage/          → Persistence layer
  storage/repository.py → DB access (e.g. SQLAlchemy)
```

## Conventions

- No FastAPI or React here; keep imports limited to stdlib and dependencies in root `requirements.txt`.
- Config: use `config_loader` and `config.py`; avoid hardcoded paths or secrets.
- Storage: go through `storage/repository` for DB operations.
- Check root AGENTS.md for project-wide conventions and OpenSpec workflow.
