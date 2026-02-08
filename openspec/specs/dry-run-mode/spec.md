# Dry-Run Mode

Simulate processing: real Scryfall/OpenAI calls; no sheet writes. **DryRunClient** implements SpreadsheetClient interface: get_cards/get_all_cards_prices return empty or mock; update_column/update_cells log only, no API. Factory: dry_run=False → SpreadsheetClient, dry_run=True → DryRunClient.

**Output:** Banner "DRY RUN MODE - No changes will be written", config summary; progress/stats as normal; sample rows that would be written; summary (count, API calls, errors, estimated write time). **APIs:** Real Scryfall and OpenAI when --use_openai; respect api_delay. Log "DRY RUN: Would update range…" / "Would update column…". No auth to Sheets; write methods no-op; sheet unchanged after run. Real API errors shown as in normal mode.
