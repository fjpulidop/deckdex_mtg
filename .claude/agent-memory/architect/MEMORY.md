# Architect Agent Memory

## OpenSpec Workflow

- `openspec new change "<name>"` creates the change directory under `openspec/changes/<name>/`.
- Artifact order: `proposal` -> `design` + `specs` (parallel) -> `tasks`. Each unlocks the next.
- Status check: `openspec status --change <name> --json`. Instructions: `openspec instructions --change <name> <artifact> --json`.
- `isComplete: true` when all artifacts are in `done` status. Ready for `opsx:apply`.
- Delta specs go in `openspec/changes/<name>/specs/<capability>/spec.md` — the glob `specs/**/*.md` picks them up.
- `openspec instructions --change <name> <artifact> --json` outputs leading non-JSON text before the JSON blob — pipe carefully or ignore and just write artifacts directly.
- The `Write` tool creates parent directories automatically — no `mkdir` needed.

## Project Architecture Patterns

- Repository pattern: `CollectionRepository` (ABC in `deckdex/storage/repository.py`) with `PostgresCollectionRepository` implementing all methods.
- SQLAlchemy text() queries use named bind params (`:name`). INTERVAL values must be f-string interpolated (not bound params).
- Route ordering in FastAPI: specific sub-paths (e.g., `/jobs/history`) MUST be registered BEFORE parameterized catch-alls (`/jobs/{job_id}`).
- All backend calls in frontend flow through `api/client.ts` (apiFetch wrapper with auth + retry) + hooks in `useApi.ts` (TanStack Query).
- `recharts ^3.7.0` is already installed in frontend/package.json — no install needed for charting.

## Frontend Key Facts

- Locale files: `frontend/src/locales/en.json` and `es.json` (NOT `i18n/`).
- All backend calls via `api/client.ts` → `apiFetch` wrapper. No raw `fetch` elsewhere.
- `useApi.ts` wraps TanStack Query. All hooks live in `frontend/src/hooks/`.
- `CardTable` props are currently a local interface (not exported). Extracting to shared type is a recurring refactor need.
- Image serving: `GET /api/cards/{id}/image` → `card_image_service.py` → filesystem `ImageStore` keyed by `scryfall_id`. Server-side cache exists; client-side was missing.
- `useCardImage` hook revokes blob URLs on unmount — this defeats caching. Fix: module-level Map cache (`useImageCache`).
- Dashboard page size: 50 for table. Gallery should use 24.
- Dashboard filter state lives in URL params (`useSearchParams`). Pagination/sort live in local state.
- i18n keys for CardTable: `cardTable.*`. Dashboard: `dashboard.*`. Reuse `cardTable.showing` and `cardTable.page` for gallery pagination.

## Job System Architecture (confirmed from codebase)

- Three module-level dicts in `backend/api/routes/process.py`: `_active_jobs`, `_job_results`, `_job_types`
- `JobRepository` at `deckdex/storage/job_repository.py` — public methods: `create_job`, `update_job_status`, `get_job_history`
- Canonical job status values: `'running'` | `'complete'` | `'error'` | `'cancelled'`
- `get_job_repo()` returns `None` in Google Sheets mode — all job_repo calls must be guarded with `if job_repo:`
- Job state is in-memory and lost on restart — never store critical state only in `_active_jobs`/`_job_results` dicts.

## Key File Locations

- Migrations: `migrations/NNN_name.sql` (last known: 008 for jobs table). New migrations are additive-only.
- Core price update logic: `deckdex/magic_card_processor.py`, method `update_prices_data_repo` (~line 300).
- Card detail UI: `frontend/src/components/CardDetailModal.tsx`
- Image service: `backend/api/services/card_image_service.py`
- Job routes: `backend/api/routes/process.py`
- Job repository: `deckdex/storage/job_repository.py`
- WebSocket: `backend/api/websockets/progress.py`
- DI: `backend/api/dependencies.py`
- Frontend job state: `frontend/src/contexts/ActiveJobsContext.tsx`

## Data Model Notes

- `cards.price_eur` is `TEXT` (not numeric) — legacy design.
- No `user_id` on `price_history`: history belongs to cards, cards carry `user_id`.
- `jobs` table: UUID PK, `user_id` nullable FK, `type VARCHAR(64)`, `status VARCHAR(32)`, `result JSONB`, timestamps.
- History is Postgres-only. Google Sheets mode gracefully no-ops via abstract base class defaults.

## Common Pitfalls

- Non-numeric price values (`"N/A"`, `""`) come from Scryfall — always wrap price float conversion in try/except.
- FastAPI route ordering is a recurring issue — always define static routes before parameterized ones.
- `on_event("startup")` may be deprecated in newer FastAPI — check if project uses `lifespan` instead.
