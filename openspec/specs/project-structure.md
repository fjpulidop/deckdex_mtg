# Project Structure

See [architecture](architecture/spec.md) for directory layout (backend/, frontend/, deckdex/, main.py, config.yaml). Core package: deckdex/ (config_loader, card_fetcher, spreadsheet_client, magic_card_processor, etc.). Tests in tests/. Entry points: main.py (CLI), backend/api/main.py (web). Type hints and single-responsibility modules; small public API per module.
