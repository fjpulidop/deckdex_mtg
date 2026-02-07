# API & Integration Specification

## External APIs Used

1. Scryfall REST API
   - Purpose: primary source for card data and pricing.
   - Rate limits must be respected; implement backoff and retries.
   - Key endpoints: card lookup by exact name, search, set endpoints.

2. Google Sheets API (Sheets v4)
   - Purpose: storage and user-facing data surface.
   - Use batchUpdate and values.batchGet/values.batchUpdate for efficiency.
   - Authenticate with Service Account credentials JSON.

3. OpenAI API (optional)
   - Purpose: classify game strategy and tier for cards.
   - Use short, deterministic prompts and caching to keep costs low.

## Internal API (CLI / Programmatic)

The application exposes a small internal command API via CLI flags and functions:

- `process_cards(names: List[str], use_openai: bool = False, update_prices: bool = True)`
  - Orchestrates fetching, enrichment, and sheet updates.
  - Returns a report object with counts (fetched, enriched, updated, errors).

- `update_prices(force_all: bool = False)`
  - Iterates cards from sheet and updates prices where changed (or all if forced).

- `enrich_cards(card_ids: List[str])`
  - Requests OpenAI for strategy/tier for given cards, returns enriched fields.

## Payload Schemas (simplified)

Card payload (internal):

```json
{
  "id": "scryfall-id",
  "name": "Card Name",
  "prices": { "usd": "1.23", "eur": "1.10" },
  "game_strategy": "Aggro",
  "tier": "High"
}
```

Process report:

```json
{
  "fetched": 120,
  "enriched": 45,
  "updated_rows": 37,
  "errors": [
    {"name":"Unknown Card","reason":"not_found"}
  ]
}
```

## Error Handling & Retries

- Normalize external errors into a small set of internal error codes: not_found, rate_limited, transient_error, permission_denied.
- Retries with exponential backoff for transient failures. Fail fast for permission issues (e.g. Sheets auth).

## Observability

- Emit structured CLI summaries and optional JSON reports for CI consumption.
- Provide verbose logging toggle for troubleshooting.

