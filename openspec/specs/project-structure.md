# Project Structure Specification

## Purpose

Describe repository layout, core modules, and responsibilities to make onboarding and modifications straightforward.

## Top-level Layout

- `main.py` - primary CLI entrypoint (non-interactive)
- `run_cli.py` - interactive CLI (menu-driven)
- `deckdex/` - main package
  - `__init__.py`
  - `cli.py` - CLI argument parsing and orchestration helpers
  - `scryfall.py` - Scryfall API client and normalizers
  - `sheets.py` - Google Sheets integration and batch syncing
  - `enrich.py` - OpenAI enrichment helpers
  - `prices.py` - price comparison and history hooks
  - `cache.py` - caching utilities (LRU wrappers)
  - `workers.py` - thread/worker management
  - `models.py` - core data models and type definitions
  - `utils.py` - small utilities and helpers
- `tests/` - unit and integration tests
- `requirements.txt` - pinned Python dependencies
- `.env.template` - environment variables template
- `openspec/` - specs and change artifacts (this folder)

## Module Guidelines

- Keep each module focused: single responsibility per file.
- Use type hints across public functions to improve readability and enable static checking.
- Expose a small, well-documented public API from each module for testability.

## Packaging and Entry Points

- The app can be packaged as a CLI with setuptools/poetry if needed. For now, `main.py` and `run_cli.py` should remain primary entry points.

## Tests

- Tests live in `tests/` mirroring the `deckdex/` package structure.
- Provide unit tests for:
  - Scryfall client (mock HTTP responses)
  - Sheets sync (mock Google API)
  - Price updater logic (delta detection)
  - OpenAI enrichment (mocked responses)

## CI / Automation

- Provide GitHub Actions workflow:
  - lint (flake8/ruff), type-check (mypy), tests
  - optionally run integration tests with mocked services

