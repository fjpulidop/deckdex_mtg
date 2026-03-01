# Conventions

Python 3.9+, type hints, PEP-8. Lint/format: ruff (optional black); type-check: mypy. Tests: pytest/unittest; mock Scryfall, Sheets, OpenAI. Commits: short imperative summary; branches feat/ fix/ chore/ docs/. Doc sheet column changes in [data-model](data-model.md). No secrets in repo; rotate keys; least-privilege Service Account.

**Logging:** CLI uses stdlib logging (--verbose/--quiet). Web backend uses loguru: human-readable stderr in development, structured JSON (`serialize=True`) stderr in production. File logs (`logs/api.log`) are always structured JSON for SIEM ingestion. Rotation: 500 MB, retention: 10 days. PII (user emails, IPs) SHALL NOT appear in structured log messages — use user IDs instead.

**Error handling:** Unhandled exceptions return `{"detail": "Internal server error"}` (HTTP 500); full stack traces logged server-side only. Validation errors return `{"detail": "Validation error", "errors": [...]}` (HTTP 400).
