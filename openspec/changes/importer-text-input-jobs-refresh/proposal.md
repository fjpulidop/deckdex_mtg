## Why

Two usability gaps in the Import workflow and job tracking:

1. **No text paste input.** The importer only accepts file uploads. Users who want to quickly paste a decklist (e.g., copied from a forum post, Moxfield deck view, or MTGO client) have to first save it as a `.txt` file before importing. This adds unnecessary friction for the most common quick-import case.

2. **Import jobs disappear on page refresh.** When a user starts an import and then refreshes the browser, the job is gone from the Jobs bottom bar — even if the backend is still processing cards. This happens because `GET /api/jobs` only reads in-memory dicts (`_active_jobs`, `_job_results` in `process.py`), while import jobs are persisted to Postgres via `JobRepository` but never surfaced through that endpoint.

## What Changes

- **Text paste input**: A two-tab toggle is added to Step 1 of the Import wizard: **Subir archivo** (existing flow) and **Pegar texto** (new). The text tab shows a `<textarea>` where the user types or pastes a card list in MTGO format (`4 Lightning Bolt`, one card per line). Clicking "Continuar →" calls the existing preview/import flow through the same pipeline.

- **Backend text support**: `POST /api/import/preview` and `POST /api/import/external` now accept an optional `text` Form field alongside the optional `file` upload. If `text` is provided, the MTGO parser is used directly. If `file` is provided, existing format detection and parsing apply. Both fields are optional; at least one must be present.

- **Jobs refresh fix**: `GET /api/jobs` now also queries `JobRepository.get_job_history()` for jobs with status `running` or `pending` that are not already tracked in the in-memory dicts. This ensures import jobs survive a page refresh while they are still being processed.

## Capabilities

### Modified Capabilities
- `collection-importer`: Added text paste input path (textarea + MTGO parser). Backend preview/external endpoints now dual-mode (file or text).
- `web-api-backend`: `GET /api/jobs` now merges in-memory state with DB-persisted running jobs.
- `web-dashboard-ui`: Import wizard Step 1 has a tab switcher (Subir archivo / Pegar texto).

## Impact

- **Backend**: Two endpoints updated (`/api/import/preview`, `/api/import/external`); `GET /api/jobs` updated. No schema changes.
- **Frontend**: `Import.tsx` updated (tab state, textarea, text handlers); `client.ts` gets `importPreviewText()` and `importExternalText()`.
- **Dependencies**: None.
