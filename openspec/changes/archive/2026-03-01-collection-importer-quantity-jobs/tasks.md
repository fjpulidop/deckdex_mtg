## 1. DB Migrations

- [x] 1.1 Create `migrations/007_add_quantity_to_cards.sql`: `ALTER TABLE cards ADD COLUMN IF NOT EXISTS quantity INTEGER NOT NULL DEFAULT 1;` + index on `(user_id, name, set_id)` for grouping queries.
- [x] 1.2 Create `migrations/008_jobs_table.sql`: `CREATE TABLE jobs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id INTEGER REFERENCES users(id), type VARCHAR(64) NOT NULL, status VARCHAR(32) NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(), completed_at TIMESTAMPTZ, result JSONB);` + index on `(user_id, created_at DESC)`.
- [x] 1.3 Create `migrations/009_group_cards_by_name_set.sql`: data migration that groups duplicate `(user_id, name, set_id)` rows — keep the row with the lowest `id`, set its `quantity` to the count of duplicates, delete the rest. Run in a transaction.

## 2. Core: Quantity in Repository & Storage

- [x] 2.1 In `deckdex/storage/repository.py`, update `_card_to_row()` to include `quantity` (default 1 if absent in input dict).
- [x] 2.2 Update `get_cards()` (Postgres implementation) to `SELECT ... quantity ...` and return it in the card dict.
- [x] 2.3 Update `replace_all()` to accept and persist `quantity` from each card dict.
- [x] 2.4 Add `update_quantity(card_id, quantity, user_id)` method to the repository interface and Postgres implementation.
- [x] 2.5 Update `backend/api/routes/stats.py`: quantity-weighted total_cards and total_value.
- [x] 2.6 Update `backend/api/routes/analytics.py`: all counters quantity-weighted.

## 3. Core: Jobs Persistence

- [x] 3.1 Create `deckdex/storage/job_repository.py` with `JobRepository` class.
- [x] 3.2 Update `backend/api/services/processor_service.py`: persist job start/end.
- [x] 3.3 Add `GET /api/jobs/history` endpoint in `backend/api/routes/process.py`.
- [x] 3.4 Add `get_job_repo()` to `backend/api/dependencies.py`.

## 4. Core: Importer Module

- [x] 4.1 Create `deckdex/importers/__init__.py` and `deckdex/importers/base.py`.
- [x] 4.2 Create `deckdex/importers/moxfield.py`.
- [x] 4.3 Create `deckdex/importers/tappedout.py`.
- [x] 4.4 Create `deckdex/importers/mtgo.py`.
- [x] 4.5 Create `deckdex/importers/generic_csv.py`.
- [x] 4.6 Create `backend/api/services/importer_service.py` with `ImporterService`.
- [x] 4.7 Implement merge upsert logic in `ImporterService`.

## 5. Backend: Import Routes

- [x] 5.1 Add `POST /api/import/preview` in `backend/api/routes/import_routes.py`.
- [x] 5.2 Add `POST /api/import/external` in `backend/api/routes/import_routes.py`.
- [x] 5.3 Add `PATCH /api/cards/{card_id}/quantity` endpoint.
- [x] 5.4 Register updated/new routes in `backend/api/main.py` if not already there.

## 6. Frontend: Quantity in Card Table

- [x] 6.1 Add `quantity` to the `Card` interface in `frontend/src/api/client.ts`.
- [x] 6.2 Add `quantity` as the first column in `CardTable.tsx`: header "Qty", numeric sort.
- [x] 6.3 Implement inline quantity editing via `QuantityCell` component (click → input → save).
- [x] 6.4 Add `updateCardQuantity`, `getJobHistory`, `importPreview`, `importExternal` to `frontend/src/api/client.ts`.
- [x] 6.5 `QuantityCell` calls `api.updateCardQuantity` directly; no separate mutation hook needed.

## 7. Frontend: Jobs Bottom Bar

- [x] 7.1 Create `frontend/src/components/JobsBottomBar.tsx`: fixed bottom-right, always rendered in `App.tsx`.
- [x] 7.2 Implement **Active tab** with `ActiveJobEntry` (WebSocket progress, cancel, elapsed time).
- [x] 7.3 Implement **History tab** via `GET /api/jobs/history`, with status icons and "Ver log".
- [x] 7.4 Auto-expand when `jobs.length` increases.
- [x] 7.5 "Ver log" opens existing `JobLogModal`.
- [x] 7.6 `<JobsBottomBar />` added to `App.tsx`; `ActiveJobs` removed from `ActiveJobsContext.tsx`.
- [x] 7.7 Fixed positioning, no layout shift.

## 8. Frontend: Import Page

- [x] 8.1 Create `frontend/src/pages/Import.tsx` as protected route at `/import` in `App.tsx`.
- [x] 8.2 **Step 1 — Upload**: Drag-and-drop + file picker, calls `POST /api/import/preview`.
- [x] 8.3 **Step 2 — Preview**: Format badge, card count, 5-card sample.
- [x] 8.4 **Step 3 — Mode**: Merge (default) / Replace option cards.
- [x] 8.5 **Step 4 — Progress**: Launches job, shows spinner + "check Jobs bar" hint.
- [x] 8.6 **Step 5 — Result**: Summary + not-found collapsible list + navigation buttons.
- [x] 8.7 "Importar colección" button in `SettingsModal.tsx` navigates to `/import`.
