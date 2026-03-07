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
- `FileResponse` (zero-copy serving) is the established pattern in `auth.py` for avatar images (lines 560, 588, 622). Use it for any filesystem-backed image endpoint.
- `ANY(:ids)` Postgres array binding is used in `DeckRepository.find_card_ids_by_names` — reuse this pattern for bulk ID validation in other repository methods.

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
- Shared `formatCurrency(value: number): string` is exported from `frontend/src/components/analytics/constants.ts` — use it instead of private duplicates.
- There is NO user-configurable price_currency setting in the app — currency is hardcoded EUR throughout (settings API only exposes `scryfall_enabled`).

## Deck System Key Facts

- `DeckRepository` lives in `deckdex/storage/deck_repository.py` — not under the CollectionRepository ABC (its own standalone class).
- `require_deck_repo()` in `backend/api/routes/decks.py` returns 501 when no Postgres — all deck endpoints use this dependency.
- Tests in `tests/test_decks.py` use `deck_client` fixture (module-scoped): mocks `require_deck_repo` + `get_current_user_id`. All 19 tests use the same mock_repo.
- Tests in `tests/test_deck_repository.py` test `DeckRepository.find_card_ids_by_names` with `MagicMock` engine injection.
- `POST /api/decks/{id}/import` had zero test coverage prior to the batch-card-add-deck change.
- `DeckCardPickerModal.tsx` had N+1 sequential request pattern (one POST per selected card) — fixed in batch-card-add-deck change.
- `DeckDetailModal.tsx` `formatDeckCurrency` was a duplicate of `analytics/constants.ts` `formatCurrency` — consolidated in batch-card-add-deck change.

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
- Deck routes: `backend/api/routes/decks.py`
- Deck repository: `deckdex/storage/deck_repository.py`
- Deck builder page: `frontend/src/pages/DeckBuilder.tsx`
- Deck detail modal: `frontend/src/components/DeckDetailModal.tsx`
- Deck card picker modal: `frontend/src/components/DeckCardPickerModal.tsx`
- Shared currency formatter: `frontend/src/components/analytics/constants.ts` → `formatCurrency`

## Data Model Notes

- `cards.price_eur` is `TEXT` (not numeric) — legacy design.
- No `user_id` on `price_history`: history belongs to cards, cards carry `user_id`.
- `jobs` table: UUID PK, `user_id` nullable FK, `type VARCHAR(64)`, `status VARCHAR(32)`, `result JSONB`, timestamps.
- History is Postgres-only. Google Sheets mode gracefully no-ops via abstract base class defaults.
- `deck_cards` table: PK `(deck_id, card_id)`, `quantity INT`, `is_commander BOOL`. ON CONFLICT DO UPDATE is the standard upsert pattern.

## ImageStore Pattern

- `FilesystemImageStore` in `deckdex/storage/image_store.py`: images at `{base_dir}/{key}{ext}`, meta sidecars at `{base_dir}/{key}.meta`.
- Keys are `scryfall_id` values (Scryfall UUIDs). Never contain `/` — validated by `_validate_key`.
- `_validate_key` must reject `/` anywhere in key (not just at start) to prevent path traversal via subdirectory creation.
- 10 unit tests in `tests/test_image_store.py`. All must pass on any change to this module.

## Common Pitfalls

- Non-numeric price values (`"N/A"`, `""`) come from Scryfall — always wrap price float conversion in try/except.
- FastAPI route ordering is a recurring issue — always define static routes before parameterized ones.
- `on_event("startup")` may be deprecated in newer FastAPI — check if project uses `lifespan` instead.
- `Response(content=data)` for images loads full bytes into Python heap — prefer `FileResponse` for filesystem-backed stores.
- Do not assume `api.getSettings()` or a `price_currency` user setting exists — the settings API only covers `scryfall_enabled` and Scryfall credentials.
