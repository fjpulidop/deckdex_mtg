## Context

The app stores each card as one row, no quantity field exists. Jobs are held in an in-memory dict (`_active_jobs` in `process.py`) and are lost on restart. The existing import endpoint (`POST /api/import/file`) does a dumb column map with no Scryfall enrichment and a destructive `replace_all`. The `ActiveJobs` component is mounted inside specific pages, not at layout level.

## Goals / Non-Goals

**Goals:**
- Add `quantity` to the card schema; group duplicate `name+set_id` rows; make all counts/values quantity-weighted.
- Parse Moxfield, TappedOut, MTGO, and generic CSV exports; enrich cards via Scryfall; run as an async job.
- Persist job state to Postgres; expose history API; never lose completed job records on restart.
- Permanent jobs bottom bar: discrete when idle, auto-expands on new job, Active + History tabs.
- Import page accessible from Settings; Merge (default) and Replace modes.

**Non-Goals:**
- Foil / condition tracking — deferred.
- TCGPlayer, Deckbox, Archidekt parsers — can be added later; the parser interface makes it trivial.
- Import from URL (API integrations with external platforms) — file upload only for now.
- Bulk job cancellation from history.

## Decisions

### 1. Quantity grouping by name + set_id

**Choice:** Cards with the same `(name, set_id)` are one logical card; `quantity` tracks how many copies.

**Alternative considered:** Group by `scryfall_id` (exact printing). Rejected — Scryfall IDs are often absent at import time from external files.

**Alternative considered:** Group by name only. Rejected — a collector distinguishes an Alpha Lightning Bolt from an M11 reprint.

**Rationale:** `name + set_id` is reliable (both fields are present after Scryfall enrichment), matches how players think ("I have 3x Lightning Bolt from M11"), and avoids the complexity of merging across printings.

### 2. Merge adds quantities; Replace nukes and rebuilds

**Choice:** Merge mode sums quantities (2 existing + 3 imported = 5). Replace mode calls `replace_all`.

**Rationale:** Merge is the safe default — a user importing from a secondary account doesn't want to lose existing data. Replace is an explicit opt-in for "start fresh from this file."

### 3. Import runs as an async job via the existing job pattern

**Choice:** `POST /api/import/external` launches a background task, returns `job_id`, progress via WebSocket. Mirrors how `POST /api/process` and `POST /api/prices/update` work.

**Alternative considered:** Synchronous upload → response. Rejected — Scryfall enrichment for 300 cards takes ~2–3 minutes. A synchronous endpoint would timeout and give no feedback.

**Rationale:** Reuses `ProcessorService`-style pattern (thread pool + WebSocket push). Progress reporting: `current / total cards resolved`, plus a "not found" list at completion.

### 4. Format detection by CSV header signature

**Choice:** Auto-detect format by inspecting the first-row headers of the uploaded file.

```
Moxfield:   "Count" + "Name" + "Edition"
TappedOut:  "Qty" + "Name" + "Set"
MTGO txt:   no header, lines like "4 Lightning Bolt"
Generic:    fallback — any CSV with a name-ish column
```

**Alternative considered:** User selects format from a dropdown. Rejected — adds a friction step for no real benefit; header signatures are unambiguous.

**Rationale:** In the rare case of ambiguity, fall back to generic parser. Surface the detected format in the preview step so the user can confirm.

### 5. Preview endpoint before committing

**Choice:** `POST /api/import/preview` parses the file and returns `{ detected_format, card_count, sample: [...first 5 names] }` without saving. The UI calls this after upload, before the user picks Merge/Replace and confirms.

**Rationale:** Gives the user a chance to see "Moxfield · 247 cards detected" and abort if something looks wrong. No extra cost — parsing is cheap; Scryfall enrichment only happens after confirmation.

### 6. Jobs persisted in Postgres; in-memory jobs remain for active state

**Choice:** On job start, write a row to `jobs` table (`id UUID, user_id, type, status, created_at`). On job end (complete/error/cancel), write `completed_at` and `result` (JSON: summary counts, error message, not-found list). In-memory dict remains for live progress updates.

**Alternative considered:** Replace in-memory dict entirely with DB polling. Rejected — WebSocket progress already works via in-memory callbacks; rewriting that is out of scope.

**Rationale:** Hybrid: in-memory for live performance, DB for durability. History is available after restart. The `JobRepository` in `deckdex/storage/` handles all DB writes.

### 7. Import parsers as a dedicated module

**Choice:** New `deckdex/importers/` package with one file per format:
- `moxfield.py` → parses `Count, Name, Edition, Foil, ...`
- `tappedout.py` → parses `Qty, Name, Set, ...`
- `mtgo.py` → parses plain `N CardName` text lines
- `generic_csv.py` → best-effort column detection (reuses existing logic from `import_routes.py`)

Each parser returns `List[{ name: str, set_name: str | None, quantity: int }]`.

The `ImporterService` in `backend/api/services/` receives the parsed list and runs Scryfall enrichment via the existing `CardFetcher`.

**Rationale:** Isolated parser modules are easy to test and to extend. A new format = one new file + one entry in the format-detection mapping.

### 8. Jobs bottom bar: always rendered, auto-expands

**Choice:** `JobsBottomBar` is rendered unconditionally in `App.tsx` (replaces `ActiveJobs`). Collapsed state shows a small pill button in the bottom-right corner. Bar auto-expands when a new job starts. User can manually collapse it. When no jobs have ever run in this session and history is empty, the pill is still visible but labeled "Jobs ▲".

**Alternative considered:** Only render when jobs exist. Rejected — user wants to be able to open it anytime to check history.

**Rationale:** The pill is 32px tall and positioned fixed bottom-right — completely non-invasive. The rest of the UI is unaffected (no reserved space when collapsed).

### 9. Import page at /import, linked from Settings

**Choice:** New page at `/import` route. Settings modal/page gets an "Import Collection" button that navigates to `/import`. The import page is a protected route (auth required).

**Rationale:** The import flow has 5 steps (upload → preview → mode → progress → result) — too complex for a modal. A dedicated page gives room to breathe and is bookmarkable.

### 10. Quantity in the card table: first column, editable inline

**Choice:** `Quantity` is the first column in `CardTable`. Clicking the quantity cell opens an inline number input (not the full card modal). Saving updates via `PATCH /api/cards/{id}` with `{ quantity }`.

**Rationale:** Users will frequently adjust quantities as they acquire or trade cards. Inline editing is faster than opening a modal for a single number.

## Data Shapes

### `jobs` table
```sql
CREATE TABLE jobs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     INTEGER REFERENCES users(id),
  type        VARCHAR(64) NOT NULL,   -- 'process', 'update_prices', 'import'
  status      VARCHAR(32) NOT NULL,   -- 'running', 'complete', 'error', 'cancelled'
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  result      JSONB                   -- { imported, not_found, errors, ... }
);
```

### Import job result shape
```json
{
  "imported": 243,
  "skipped": 4,
  "not_found": ["Timewalk", "Ancestral Recall"],
  "mode": "merge",
  "format": "moxfield"
}
```

### Parser output (each format normalizes to this)
```json
[
  { "name": "Lightning Bolt", "set_name": "M11", "quantity": 4 },
  { "name": "Rhystic Study", "set_name": "C21", "quantity": 2 }
]
```
