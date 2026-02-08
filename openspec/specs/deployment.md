# Deployment

See [architecture](architecture/spec.md) for CLI-only vs web vs Docker. **Env:** GOOGLE_API_CREDENTIALS, OPENAI_API_KEY, optional PREFERRED_CURRENCY, WORKER_COUNT. Run price updates via cron/GitHub Actions or ad-hoc `python main.py`. CI: lint, type-check, unit tests; optional integration with mocked services. Secrets in repo secrets or platform secret manager; no credentials in repo.
