## Context

The Import wizard (`/import`) uses a 5-step flow: Upload → Preview → Mode → Progress → Result. Step 1 previously had only a drag-and-drop / file picker UI. Import jobs are tracked in two places: an in-memory dict in `process.py` (for process/price jobs) and Postgres via `JobRepository` (for import jobs). `GET /api/jobs` only read the in-memory dict, leaving import jobs invisible after a page refresh.

## Goals / Non-Goals

**Goals:**
- Let users paste a card list directly in the import wizard, without creating a file first.
- Ensure import jobs remain visible in the Jobs bottom bar after a page refresh if they are still running.

**Non-Goals:**
- Supporting CSV or Moxfield format via text paste — MTGO plain text is the natural paste format and covers the common use case.
- Unifying the in-memory and Postgres job stores — the hybrid approach remains; only the list endpoint is extended.
- Persisting job state across backend restarts — in-memory jobs are still lost on restart (existing limitation, unchanged).

## Decisions

### 1. MTGO format for text paste, not auto-detect

**Choice:** Text paste always uses the MTGO parser (`N CardName` per line).

**Alternative considered:** Auto-detect format from pasted text (could be CSV). Rejected — users who have CSV data will use the file upload. The text box's placeholder and label make the expected format explicit. Auto-detecting from paste content adds complexity for a marginal benefit.

**Rationale:** MTGO plain text is the universal clipboard format for MTG card lists (forums, Reddit, Moxfield deck view, MTGO client, Archidekt exports). It's the only format that makes sense to type by hand.

### 2. Tab toggle, not a separate step

**Choice:** "Subir archivo" and "Pegar texto" are rendered as a tab switcher within Step 1. The step count and numbering remain unchanged.

**Alternative considered:** Add a Step 0 to choose input method. Rejected — adds a step to the file upload path (the common case) for no benefit.

**Rationale:** The toggle is an implementation detail within Step 1. From Step 2 onward the flow is identical regardless of how cards were ingested.

### 3. Text sent as a Form field alongside the optional file

**Choice:** Both `file` (UploadFile) and `text` (str) are optional Form fields on `/api/import/preview` and `/api/import/external`. Backend checks `text` first; if present and non-empty, uses MTGO parser. Otherwise expects `file`.

**Alternative considered:** Separate endpoint (e.g., `POST /api/import/preview-text`). Rejected — same response shape, same downstream flow. A single endpoint with two input modes is cleaner.

**Rationale:** FastAPI `Form()` fields and `File()` fields coexist in a multipart request. The frontend sends either `file` or `text` in a `FormData` object — the same pattern as before, just with a different key.

### 4. `GET /api/jobs` merges in-memory + DB running jobs

**Choice:** After building the in-memory job list, the endpoint queries `job_repo.get_job_history(user_id, limit=20)` and appends any jobs with `status in ('running', 'pending')` whose IDs are not already in the response.

**Alternative considered:** Track import jobs in the in-memory dict at creation time. Rejected — `import_routes.py` doesn't use `ProcessorService` and has no `get_metadata()` equivalent, so faking an entry would require a stub object or a separate parallel tracking dict. The DB query is cleaner.

**Alternative considered:** Have `ActiveJobsContext` call both `GET /api/jobs` and `GET /api/jobs/history` on mount. Rejected — the context has no way to distinguish "running in DB" from "completed" without fetching status for each job; the backend merge is more reliable.

**Rationale:** The DB query is cheap (indexed on `user_id, created_at DESC`, limit 20, filters to running/pending only). Adding `user_id` as a dependency to `GET /api/jobs` is consistent with how `/api/jobs/history` is already secured.

## Data Shapes

### Request: POST /api/import/preview (text mode)
```
Content-Type: multipart/form-data
text=4 Lightning Bolt\n2 Rhystic Study\n1 Sol Ring
```

### Response: POST /api/import/preview (same as file mode)
```json
{
  "detected_format": "mtgo",
  "card_count": 3,
  "sample": ["Lightning Bolt", "Rhystic Study", "Sol Ring"]
}
```

### Request: POST /api/import/external (text mode)
```
Content-Type: multipart/form-data
text=4 Lightning Bolt\n2 Rhystic Study
mode=merge
```

### GET /api/jobs response item (DB-sourced running import)
```json
{
  "job_id": "uuid...",
  "status": "running",
  "job_type": "import",
  "progress": {},
  "start_time": "2026-03-01T10:00:00+00:00"
}
```
