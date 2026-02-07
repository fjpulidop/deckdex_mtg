# Architecture Specification

## Summary

This document describes the overall architecture of DeckDex MTG. It is focused on high-level components, data flow, integration points, and non-functional requirements to guide maintainers and future contributors.

## Goals

- Provide a robust CLI-first tool that syncs Magic: The Gathering card data from Scryfall into Google Sheets.
- Optionally enrich card records using the OpenAI API.
- Keep price data current while minimizing API calls and cost.
- Be testable, maintainable, and easy to run in local or CI environments.

## High-level Components

1. CLI / Interactive CLI
   - Entrypoints: `main.py`, `run_cli.py`
   - Orchestrates tasks, parses flags, and exposes user flows (process cards, update prices, configure credentials).

2. Scryfall Fetcher
   - Responsible for querying Scryfall API, normalizing responses, and caching results.
   - Uses persistent HTTP sessions and rate-limit/backoff handling.

3. Google Sheets Sync
   - Translates internal card models to sheet rows and performs batched updates to minimize API calls.
   - Manages authentication via Google Service Account credentials JSON.

4. Enrichment Service (Optional)
   - Calls OpenAI to generate game strategy and tier metadata.
   - Runs optionally per-card or in batches; results are cached to avoid duplicate calls.

5. Price Updater
   - Compares current prices with new Scryfall prices and only writes changed values.
   - Persists minimal price history for auditing and selective updates.

6. Worker / Executor
   - Uses ThreadPoolExecutor for parallel processing of cards.
   - Ensures thread-safe Google Sheets batching and rate-limit compliance.

7. Caching & Persistence
   - In-memory LRU caches for short-term API responses.
   - Optional local persistence (JSON or lightweight DB) for price history and deduplication.

## Data Flow

1. User provides a list of card names in the Google Sheet (column `Name`).
2. CLI reads sheet rows, queues card names for processing.
3. For each card:
   - Check cache and local persistence.
   - Fetch card data from Scryfall.
   - Optionally call OpenAI to enrich metadata.
   - Compute price delta and prepare sheet update.
4. Batch updates are sent back to Google Sheets.

## Integration Points

- Scryfall API: primary source of card metadata and pricing.
- Google Sheets API: primary storage and user-facing surface.
- OpenAI API: optional enrichment provider.

## Non-functional Requirements

- Performance: Parallel processing with configurable worker count.
- Cost-efficiency: Batch updates and selective price writes to minimize API usage.
- Reliability: Retries with exponential backoff and robust error handling.
- Observability: CLI output and optional verbose logging; structured logs for CI runs.

## Security and Secrets

- Google credentials JSON and OPENAI_API_KEY must be stored outside the repo and provided via environment variables or a `.env` file.
- Least-privilege Google service account recommended (only Sheets scopes needed).

## Suggested Next Steps

- Add simple architecture diagram (SVG or ASCII) to docs.
- Define a small schema for persisted price history to enable rollbacks and audits.

