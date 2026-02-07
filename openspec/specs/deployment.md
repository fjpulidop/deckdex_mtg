# Deployment & Operations Specification

## Environments

- Local (developer machine)
- CI (GitHub Actions)
- Optional: small cloud runner for scheduled jobs (e.g., GitHub Actions scheduled workflow or a small VM/container)

## Environment Variables / Secrets

- `GOOGLE_API_CREDENTIALS` -> path to service account JSON
- `OPENAI_API_KEY` -> OpenAI key (optional)
- `PREFERRED_CURRENCY` -> e.g., "EUR"
- `WORKER_COUNT` -> configurable number of parallel workers

## Scheduling & Running

- Recommended: run price updates as a scheduled job (daily/weekly) using GitHub Actions or cron in a small cloud runner.
- For ad-hoc usage, users run `python main.py` locally with proper env vars.

## CI / CD

- CI pipeline tasks:
  1. Install dependencies
  2. Run linters and static type checks
  3. Run unit tests
  4. Produce an artifacts folder with a JSON report when running a smoke integration test (mocked services)

## Backups & Auditing

- Persist price history and occasionally dump to a backup file in a secure storage location if running scheduled jobs.
- Keep simple logging of updates with timestamps to enable manual audits.

## Secrets Management

- Avoid committing credential files. Use repository secrets for CI (GitHub Actions secrets).
- For cloud runners, use platform-native secret managers (e.g., AWS Secrets Manager, GitHub Secrets).

## Scaling Notes

- The app is lightweight; scale by increasing `WORKER_COUNT` while observing Scryfall and Sheets rate limits.
- If higher throughput is needed, consider moving to a small queue-based architecture (Redis or Cloud Tasks) and horizontal workers.

