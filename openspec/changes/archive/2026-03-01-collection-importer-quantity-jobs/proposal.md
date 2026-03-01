## Why

Three related gaps limit the app's usefulness for real collectors:

1. **No quantity field.** Each card is a single row. Users who own 4x Lightning Bolt or 2x Rhystic Study have no way to record that — the collection under-counts cards and misstates total value.

2. **No import path from other apps.** Moxfield, TappedOut, and MTGO are where most players already have their collections. Without a migration path, adoption requires manual re-entry of hundreds of cards.

3. **Jobs vanish on restart.** Active jobs are in-memory only. History is lost. There's no way to audit what ran, when, or what the outcome was.

These three problems connect: fixing quantity is a prerequisite for a correct importer, and the importer needs job persistence to deliver a trustworthy async experience.

## What Changes

- **Quantity field**: `quantity INT DEFAULT 1` added to `cards`. Existing rows with the same `name + set_id` are merged into one row with the summed quantity. First column in the card table. Stats and analytics become quantity-weighted.

- **External importer**: Accepts Moxfield CSV, TappedOut CSV, MTGO `.txt` decklist, and generic CSV. Format is auto-detected from headers. Each card is enriched via Scryfall (async job). Two modes: **Merge** (adds quantities to existing cards, default) and **Replace** (replaces entire collection). Accessible as a dedicated page (`/import`) linked from Settings.

- **Jobs persistence**: New `jobs` table in Postgres. The existing job runner persists state and result summaries. New `GET /api/jobs/history` endpoint.

- **Jobs bottom bar**: The existing ActiveJobs UI is replaced by a permanent bottom bar. Collapsed by default (discrete button, always visible). Expands on demand or automatically when a job starts. Two tabs: **Active** (live progress) and **History** (past jobs with log access). Log detail opens in a modal.

## Capabilities

### New Capabilities
- `collection-importer`: Parser layer (Moxfield, TappedOut, MTGO, generic CSV) + Scryfall enrichment pipeline + async import job + `/import` page.

### Modified Capabilities
- `data-model`: `quantity` field on `Card`. Grouping by `name + set_id`. Stats and analytics are quantity-weighted.
- `web-api-backend`: Jobs persistence (new `jobs` table, `JobRepository`); quantity in all card payloads; import endpoint updated; `GET /api/jobs/history`; import preview endpoint.
- `web-dashboard-ui`: Jobs bottom bar (replaces ActiveJobs pattern); `/import` page; Settings link to importer; quantity column in card table.

## Impact

- **Schema**: 2 migrations — add `quantity` to `cards`; create `jobs` table.
- **Data**: One-time grouping of duplicate `name+set_id` rows (sum quantities).
- **Backend**: New `deckdex/importers/` module; updated `ProcessorService`; new routes.
- **Frontend**: New `JobsBottomBar` component replaces `ActiveJobs`; new `Import` page; quantity column in `CardTable`; Settings gets import link.
- **Dependencies**: No new external dependencies. Scryfall enrichment reuses existing `CardFetcher`.
