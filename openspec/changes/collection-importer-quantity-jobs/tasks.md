## 1. DB Migrations

- [ ] 1.1 Create `migrations/007_add_quantity_to_cards.sql`: `ALTER TABLE cards ADD COLUMN IF NOT EXISTS quantity INTEGER NOT NULL DEFAULT 1;` + index on `(user_id, name, set_id)` for grouping queries.
- [ ] 1.2 Create `migrations/008_jobs_table.sql`: `CREATE TABLE jobs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id INTEGER REFERENCES users(id), type VARCHAR(64) NOT NULL, status VARCHAR(32) NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(), completed_at TIMESTAMPTZ, result JSONB);` + index on `(user_id, created_at DESC)`.
- [ ] 1.3 Create `migrations/009_group_cards_by_name_set.sql`: data migration that groups duplicate `(user_id, name, set_id)` rows — keep the row with the lowest `id`, set its `quantity` to the count of duplicates, delete the rest. Run in a transaction.

## 2. Core: Quantity in Repository & Storage

- [ ] 2.1 In `deckdex/storage/repository.py`, update `_card_to_row()` to include `quantity` (default 1 if absent in input dict).
- [ ] 2.2 Update `get_cards()` (Postgres implementation) to `SELECT ... quantity ...` and return it in the card dict.
- [ ] 2.3 Update `replace_all()` to accept and persist `quantity` from each card dict.
- [ ] 2.4 Add `update_quantity(card_id, quantity, user_id)` method to the repository interface and Postgres implementation.
- [ ] 2.5 Update `backend/api/routes/stats.py`: `total_cards = sum(c.get("quantity", 1) for c in collection)` and `total_value = sum(parse_price(c.get("price_eur")) * c.get("quantity", 1) for c in collection)`.
- [ ] 2.6 Update `backend/api/routes/analytics.py`: all counters change from `counter[key] += 1` to `counter[key] += card.get("quantity", 1)` so charts are quantity-weighted.

## 3. Core: Jobs Persistence

- [ ] 3.1 Create `deckdex/storage/job_repository.py` with `JobRepository` class: `create_job(user_id, type) -> str (job_id)`; `update_job_status(job_id, status, result=None)`; `get_job_history(user_id, limit=50) -> List[dict]`.
- [ ] 3.2 Update `backend/api/services/processor_service.py`: on job start call `job_repo.create_job()`; on complete/error/cancel call `job_repo.update_job_status()` with result summary.
- [ ] 3.3 Add `GET /api/jobs/history` endpoint in `backend/api/routes/process.py`: returns paginated list of persisted jobs for the authenticated user (type, status, created_at, completed_at, result summary). Auth-gated.
- [ ] 3.4 Update `JobRepository` to be initialized in `backend/api/dependencies.py` alongside `get_collection_repo()`, with the same Postgres URL.

## 4. Core: Importer Module

- [ ] 4.1 Create `deckdex/importers/__init__.py` and `deckdex/importers/base.py` with `ParsedCard = TypedDict("ParsedCard", { "name": str, "set_name": Optional[str], "quantity": int })` and a `detect_format(filename, content) -> str` function that inspects headers to return `"moxfield"`, `"tappedout"`, `"mtgo"`, or `"generic"`.
- [ ] 4.2 Create `deckdex/importers/moxfield.py`: parse CSV with columns `Count, Name, Edition, [Foil, ...]` → `ParsedCard` list. Map `Count` → quantity, `Name` → name, `Edition` → set_name.
- [ ] 4.3 Create `deckdex/importers/tappedout.py`: parse CSV with columns `Qty, Name, Set, [...]` → `ParsedCard` list.
- [ ] 4.4 Create `deckdex/importers/mtgo.py`: parse plain-text lines `N CardName` (e.g. `4 Lightning Bolt`) → `ParsedCard` list. Skip empty lines and comment lines starting with `//`.
- [ ] 4.5 Create `deckdex/importers/generic_csv.py`: upgrade of existing logic in `import_routes.py` — detect name column, detect quantity column (`qty`, `count`, `quantity`), return `ParsedCard` list.
- [ ] 4.6 Create `backend/api/services/importer_service.py` with `ImporterService`: takes parsed cards list + mode (`merge`/`replace`) + `user_id`; calls `CardFetcher.search_card()` for each name; builds full card dict (with quantity); calls `repo.replace_all()` for replace mode or upsert-with-quantity-add for merge mode; returns result summary dict.
- [ ] 4.7 Implement merge upsert logic in `ImporterService`: for each enriched card, if a card with `(user_id, name, set_id)` already exists → `UPDATE cards SET quantity = quantity + $new_qty`; else → `INSERT`. Use a transaction.

## 5. Backend: Import Routes

- [ ] 5.1 Add `POST /api/import/preview` in `backend/api/routes/import_routes.py`: accepts file upload, runs parser only (no Scryfall), returns `{ detected_format, card_count, sample: [...first 5 names] }`. No auth side-effects, just parsing.
- [ ] 5.2 Add `POST /api/import/external` in `backend/api/routes/import_routes.py`: accepts file + mode (`merge`/`replace`, default `merge`); launches background `ImporterService` job; persists job via `JobRepository`; returns `{ job_id }`. Auth-gated. WebSocket progress via existing `ws_manager`.
- [ ] 5.3 Add `PATCH /api/cards/{card_id}` endpoint (or extend existing card update) to support `{ quantity: int }` partial update; calls `repo.update_quantity()`; auth-gated and user-scoped.
- [ ] 5.4 Register updated/new routes in `backend/api/main.py` if not already there.

## 6. Frontend: Quantity in Card Table

- [ ] 6.1 Add `quantity` to the card TypeScript type in `frontend/src/types.ts` (or wherever `Card` is defined).
- [ ] 6.2 Add `quantity` as the first column in `CardTable.tsx`: header "Qty", right-aligned, numeric sort.
- [ ] 6.3 Implement inline quantity editing: clicking the Qty cell renders a small `<input type="number" min="1">` in place; on blur or Enter, call `PATCH /api/cards/{id}` with new quantity and invalidate the cards query cache.
- [ ] 6.4 Add `updateCardQuantity(cardId, quantity)` to `frontend/src/api/client.ts`.
- [ ] 6.5 Update `useApi.ts` (or equivalent) with a `useMutation` hook for quantity updates.

## 7. Frontend: Jobs Bottom Bar

- [ ] 7.1 Create `frontend/src/components/JobsBottomBar.tsx`: fixed bottom-right component, always rendered in `App.tsx`. Collapsed state: pill button `[⚡ Jobs ▲]` (or `[⚡ N active ▲]` when jobs running). Expanded state: panel with two tabs.
- [ ] 7.2 Implement **Active tab**: shows in-progress jobs with name, progress bar, elapsed time, and Cancel button. Fetches from existing `GET /api/jobs` and WebSocket updates. Mirrors current `ActiveJobs` behavior.
- [ ] 7.3 Implement **History tab**: fetches `GET /api/jobs/history`, shows list of past jobs with type, status icon (✅ ❌ 🚫), date, and result summary. "Ver log" button per job.
- [ ] 7.4 Auto-expand the bar when a new job starts (e.g., listen to a global jobs context or watch `GET /api/jobs` polling).
- [ ] 7.5 Job log detail: clicking "Ver log" opens the existing `JobLogModal` (or a simplified version) with the persisted result JSON rendered as human-readable text.
- [ ] 7.6 Remove `ActiveJobs` from `Dashboard.tsx` and any other page-level mounting. Add `<JobsBottomBar />` once in `App.tsx` (inside the router, outside page content).
- [ ] 7.7 Ensure bottom bar does NOT add padding/margin to page content when collapsed (fixed positioning, no layout shift).

## 8. Frontend: Import Page

- [ ] 8.1 Create `frontend/src/pages/Import.tsx` as a protected route at `/import`. Add route to `App.tsx` router config.
- [ ] 8.2 **Step 1 — Upload**: Drag-and-drop zone + "Browse" button. Accepts `.csv` and `.txt`. On file select, call `POST /api/import/preview` and advance to Step 2.
- [ ] 8.3 **Step 2 — Preview**: Show detected format badge, card count, and 5-card sample list. "Wrong format?" hint text. Buttons: [Back] [Continuar →].
- [ ] 8.4 **Step 3 — Mode**: Two large option cards: **Merge** (default, highlighted, description: "Adds imported cards to your existing collection. Quantities are combined.") and **Replace** (description: "Replaces your entire collection with this file. This cannot be undone."). [Back] [Importar →].
- [ ] 8.5 **Step 4 — Progress**: Calls `POST /api/import/external` with file + mode, receives `job_id`. Shows live progress via WebSocket (reuse existing progress hook). The Jobs bottom bar also shows this job. [Ver en Jobs ↓] link that opens/focuses the bottom bar.
- [ ] 8.6 **Step 5 — Result**: Shows summary: cards imported, cards skipped, not-found list (collapsible). Buttons: [Ir a colección] [Importar otro archivo].
- [ ] 8.7 Add "Importar colección" link/button in `Settings.tsx` (or the settings modal) that navigates to `/import`. Place it in a logical section (e.g., near "Process Cards").
