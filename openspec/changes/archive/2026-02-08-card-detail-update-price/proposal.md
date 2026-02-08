## Why

When a user opens the card detail modal (by clicking a row), they see the current price but have no way to refresh only that card's price. Today they must go to Settings → Deck Actions and run "Update Prices" for the entire collection. A single-card update from the modal improves UX and reuses the existing app-wide jobs bar so progress and completion stay consistent with the rest of the app.

## What Changes

- Add an **"Update price"** button inside the card detail modal. It is shown only when the card has an `id` (persisted in the collection).
- New backend capability: **single-card price update**. The backend SHALL accept a request to update the price of one card by id and SHALL run it as a job (same job infrastructure: job_id, WebSocket progress, completion summary). The job SHALL appear in the same bottom jobs bar with a distinct label (e.g. "Update price").
- **Refresh on job completion**: When the single-card "Update price" job completes, the app SHALL refresh immediately: (1) total value (and stats), (2) the price shown in the card detail modal if it is still open for that card, and (3) the card table rows so the updated price is visible in the list.
- No change to full "Update Prices" behavior or to the existing POST `/api/prices/update` contract for bulk updates.

## Capabilities

### New Capabilities

None. This change extends existing capabilities.

### Modified Capabilities

- **card-detail-modal**: The modal SHALL offer an "Update price" action when the displayed card has an id. Triggering it SHALL start a single-card price-update job and SHALL register that job with the global jobs state so it appears in the app-wide jobs bar. When that job completes, the system SHALL refresh total value (stats), the price displayed in the modal (if still open for that card), and the card table so all displayed data reflects the new price.
- **web-api-backend**: The system SHALL provide an endpoint (or an optional parameter on the existing price-update endpoint) to trigger a price update for a single card by id. The response SHALL be a job_id and the job SHALL use the same progress/WebSocket and completion semantics as the bulk price update job. Single-card update jobs MAY run concurrently with each other or with the bulk update job (policy left to design).

## Impact

- **Frontend**: CardDetailModal component, API client (new method to trigger single-card update), ActiveJobs context (addJob with optional onFinished callback), Dashboard refetch on job completion (invalidate cards/stats, refetch open card by id). Jobs bar calls onFinished when a job completes so the dashboard can refresh.
- **Backend**: New route POST `/api/prices/update/{card_id}`, ProcessorService to run a one-card price update as an async job with progress callbacks. No change to request/response shape for the english_name behaviour (that is internal to deckdex/repository).
- **Core/processor**: Narrow path to run price update for a given list of card ids (e.g. one id) reusing existing Scryfall fetch and repository update logic; use english_name for Scryfall lookup when available (bulk and single-card).
- **Jobs UI**: No structural change; a new job type label (e.g. "Update price") will appear in the same bar.
