# Coding & Project Conventions

## Language & Style

- Python 3.9+ (use type hints liberally)
- Follow PEP-8 for formatting and naming.
- Prefer small, testable functions; keep modules focused.

## Formatting, Linting, and Type Checking

- Recommended tools:
  - ruff for linting/formatting
  - black for formatting (if desired)
  - mypy for static type checking

## Testing

- Use `unittest` or `pytest`. Keep tests fast and deterministic.
- Mock external services (Scryfall, Google Sheets, OpenAI) for unit tests.

## Logging

- Use the standard `logging` module with structured messages where possible.
- Provide `--verbose` / `--quiet` flags to control output.

## Commit Messages & Branches

- Commit message format: short imperative summary (50 chars), optional body.
- Branch naming: `feat/...`, `fix/...`, `chore/...`, `docs/...`

## Documentation

- Keep specs in `openspec/specs/` and update them when making breaking changes.
- Document any additions to the Google Sheets column layout in `openspec/specs/data-model.md`.

## Security

- Do not store secrets in the repository.
- Rotate API keys periodically and use least-privilege principals for Google Service Accounts.

