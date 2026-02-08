## 1. Core (deckdex)

- [x] 1.1 Add `MagicCardProcessor.update_prices_for_card_ids(card_ids: List[int])` that builds list of `(id, name, price)` via `get_card_by_id` for each id and calls existing `update_prices_data_repo(cards)`; handle missing cards (skip or error per design).

## 2. Backend API

- [x] 2.1 Add route POST `/api/prices/update/{card_id}`; resolve card_id to integer; return 404 if card does not exist.
- [x] 2.2 In ProcessorService add path to run single-card price update (e.g. method that calls processor `update_prices_for_card_ids([card_id])` in a thread with same progress callback/WebSocket pattern as bulk update).
- [x] 2.3 Register single-card job with distinct job type (e.g. "Update price"); do not apply 409 conflict for this endpoint when bulk price update is running.

## 3. Frontend API client

- [x] 3.1 Add `triggerSingleCardPriceUpdate(cardId: number)` in `api/client.ts` that POSTs to `/api/prices/update/{card_id}` and returns `Promise<{ job_id: string }>` (or existing JobResponse shape).

## 4. Card detail modal

- [x] 4.1 In CardDetailModal render an "Update price" button only when `card.id != null`.
- [x] 4.2 On button click call `triggerSingleCardPriceUpdate(card.id)`, then `useActiveJobs().addJob(jobId, 'Update price')` so the job appears in the app-wide jobs bar.
- [x] 4.3 Disable button or show loading state while the start request is in flight (optional but recommended).

## 5. Refresh on job completion

- [x] 5.1 Extend ActiveJobsContext.addJob to accept optional onFinished callback; store per jobId and invoke when that job completes (before removing from bar).
- [x] 5.2 In ActiveJobs/JobEntry, when job completes call onJobFinished(jobId) so context can run the registered callback.
- [x] 5.3 Dashboard: implement refetch callback (invalidate cards + stats; fetch open card by id and setDetailCard only if still same card); pass to CardDetailModal as onPriceUpdateJobComplete.
- [x] 5.4 CardDetailModal: accept onPriceUpdateJobComplete and pass it as third argument to addJob when starting Update price job.

## 6. Verification

- [ ] 6.1 Manually verify: open modal for a card with id, click "Update price", confirm job appears in bottom bar and completes; confirm total value, modal price and table row update automatically when job completes.
- [ ] 6.2 Verify modal does not show "Update price" when card has no id (if such case exists in the app).
- [ ] 6.3 Verify POST `/api/prices/update/{card_id}` returns 404 for non-existent card id.
