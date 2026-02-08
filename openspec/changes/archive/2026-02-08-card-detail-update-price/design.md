## Context

- **Card detail modal**: `CardDetailModal` receives a `Card` and displays image (from GET `/api/cards/{id}/image`) and metadata including price. It is read-only; there is no action today to refresh the card's price.
- **Jobs**: The app uses `ActiveJobsContext` (addJob/removeJob) and an `ActiveJobs` bar at the bottom. Jobs are created by calling the API (e.g. POST `/api/prices/update`), then `addJob(jobId, jobType)` so the bar shows progress via WebSocket. Same pattern is used for "Process Cards" and "Update Prices" from Settings → Deck Actions.
- **Backend price update**: POST `/api/prices/update` (no body) starts a full collection price update. It uses `ProcessorService.update_prices_async()`, which runs `MagicCardProcessor.process_card_data()` in update_prices mode: repository `get_cards_for_price_update()` returns all cards as `(id, name, price_eur)`; `update_prices_data_repo(cards)` fetches Scryfall prices and updates the repository. Only one bulk "update_prices" job is allowed at a time (409 if already running).
- **Processor**: `MagicCardProcessor.update_prices_data_repo(cards)` already accepts a list of `(card_id, name, current_price_str)`. Passing a single-element list would update only that card; the processor does not currently expose an entry point that takes a subset of card ids.

## Goals / Non-Goals

**Goals:**

- Add an "Update price" button in the card detail modal when the card has an id.
- Expose a backend way to trigger a price update for one card by id, returning a job_id and using the same job/WebSocket/completion flow as bulk update.
- Reuse the existing jobs bar: the new job appears at the bottom with a clear label (e.g. "Update price") and the same UX (progress, completion, cancel if we keep it consistent).
- When the single-card "Update price" job completes, refresh immediately: total value (stats), the price in the open card detail modal (if still that card), and the card table rows.

**Non-Goals:**

- Changing bulk "Update Prices" behavior or its 409 semantics.
- Adding a separate "single-card jobs" UI; we reuse the global jobs bar.

## Decisions

### 1. API shape: new endpoint vs optional body

- **Chosen:** New endpoint **POST `/api/prices/update/{card_id}`** (path parameter).
- **Alternatives:** POST `/api/prices/update` with body `{ "card_id": 123 }`. Rejected to keep the bulk endpoint body-free and to make the single-card case explicit and easy to document.

### 2. Where to implement "update only these cards"

- **Chosen:** Add a method in **deckdex** (e.g. `MagicCardProcessor.update_prices_for_card_ids(card_ids: List[int])`) that builds the list of `(id, name, price)` via `get_card_by_id` for each id, then calls existing `update_prices_data_repo(cards)`. The backend then calls this path when handling POST `/api/prices/update/{card_id}`.
- **Rationale:** Keeps Scryfall and repository logic in one place; backend stays a thin orchestrator. No new repository method required; `get_card_by_id` is sufficient.

### 3. Backend job type and concurrency

- **Chosen:** Register the job with type **"Update price"** (singular) so the bar shows a distinct label. Allow single-card update jobs to run **independently** of the bulk update job: do not block on "another price update job is already running" for this endpoint. Multiple single-card jobs may run concurrently.
- **Rationale:** Single-card updates are quick and low-impact; blocking them on a long bulk run would hurt UX. The 409 rule remains for the bulk endpoint only.

### 4. Frontend: how to trigger and register the job

- **Chosen:** In `CardDetailModal`, add a button "Update price" visible only when `card.id != null`. On click: call new API method (e.g. `triggerSingleCardPriceUpdate(card.id)`), get `job_id`, then `useActiveJobs().addJob(jobId, 'Update price', onPriceUpdateJobComplete)` where `onPriceUpdateJobComplete` is a callback provided by the Dashboard. Disable the button or show loading state while the start request is in flight.
- **Rationale:** Matches existing pattern (Settings buttons that start jobs and call addJob). The optional third argument to addJob is an onFinished callback; when the job completes, the jobs bar invokes it so the Dashboard can refetch stats, cards, and the open card (by id) and update the modal and table.

### 5. Refresh on job completion

- **Chosen:** Extend `ActiveJobsContext.addJob(jobId, jobType, onFinished?)`. When a job completes (in the jobs bar, when WebSocket reports complete), call the stored onFinished for that jobId before removing the job from the bar. Dashboard provides a callback that: invalidates cards and stats queries (so total value and table refetch), then fetches the current open card by id via GET `/api/cards/{id}` and updates `detailCard` only if it still refers to that card (so the modal price updates without reopening if the user had closed it).
- **Rationale:** User sees updated total value, modal price, and table rows immediately when the job finishes, without closing the modal or refreshing the page.

### 6. Scryfall lookup name for price update

- **Chosen:** Use **english_name** when available (else **name**) for Scryfall API lookup in both bulk and single-card price update. Repository `get_cards_for_price_update()` returns (card_id, name_for_scryfall, price) with name_for_scryfall = COALESCE(english_name, name); processor `update_prices_for_card_ids` builds the same from get_card_by_id.
- **Rationale:** Scryfall expects canonical English names; cards with a localised display name (e.g. Spanish) often failed to resolve; filling english_name (e.g. from Scryfall on process) fixes price lookup.
- **Scope:** This is a deckdex/repository and processor change only; the web API backend (POST `/api/prices/update`, POST `/api/prices/update/{card_id}`) is unchanged and does not expose or require english_name.

## Risks / Trade-offs

- **Card without id:** Cards that are not yet persisted (e.g. no id) will not show the button; this is by design and documented in the proposal.
- **Scryfall/credentials:** Same failure modes as bulk update (e.g. missing Scryfall credentials, rate limits, card not found). The job will report completion or error via the same WebSocket/summary; no special handling required in the UI beyond what the jobs bar already shows.
- **Concurrency:** Allowing single-card and bulk runs together could increase load on Scryfall. Mitigation: single-card runs are infrequent and one-off; if needed, a future change can add a global "one price-update job at a time" (any type) policy.

## Migration Plan

- No data migration. Deploy backend with new route and (if added) deckdex method; deploy frontend with updated modal and API client. Rollback: revert frontend and backend; no schema or data changes.

## Open Questions

None.
