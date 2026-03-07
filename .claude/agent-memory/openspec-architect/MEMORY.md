# OpenSpec Architect Memory

## OpenSpec CLI Usage

- `openspec new change "<name>"` — creates change dir at `openspec/changes/<name>/`
- `openspec status --change <name> --json` — check artifact completion (requires `--change` flag)
- `openspec instructions --change <name> <artifact> --json` — get instructions for an artifact
- Schema `spec-driven` has 4 artifacts in order: `proposal` → `design` + `specs` (parallel) → `tasks`
- `isComplete: true` when all artifacts are `done`
- Warning: "Rules for 'tasks' must be an array of strings" is benign, not a real error

## Artifact Writing Sequence

1. Write `proposal.md` first — unlocks `design` and `specs`
2. Write `design.md` and `specs/**/*.md` — both unlock `tasks`
3. Write `tasks.md` — completes the change
4. Always call `openspec instructions --change <name> <artifact> --json` before writing each artifact to get the template and rules

## Proposal Rules

- Keep under 500 words
- Always include "Non-goals" section
- "Capabilities / Modified Capabilities" only lists specs with actual requirement changes (not just implementation fixes)
- Use kebab-case for capability names that match folder names under `openspec/specs/`

## Specs Artifact Rules

- Delta spec path must match existing spec folder: `specs/<existing-name>/spec.md`
- Use `## MODIFIED Requirements` with FULL requirement block copied + edited
- Use `## ADDED Requirements` for truly new requirements
- Scenarios MUST use `####` (4 hashtags), never 3 or bullets
- Every requirement needs at least one scenario

## Job System Architecture (confirmed from codebase)

- Three module-level dicts in `backend/api/routes/process.py`: `_active_jobs`, `_job_results`, `_job_types`
- `JobRepository` in `deckdex/storage/job_repository.py` — public methods: `create_job`, `update_job_status`, `get_job_history`
- Canonical status values: `'running'`, `'complete'`, `'error'`, `'cancelled'`
- `catalog_service` was using `job_repo._engine()` (private) — fix: use public repo methods
- `catalog_service` wrote `'completed'`/`'failed'` — non-canonical, must be normalized
- `ProcessorService` has `_persist_job_start` / `_persist_job_end` helpers; `update_single_card_price_async` was missing calls to both
- WebSocket handler in `progress.py` validates job against in-memory only — needs DB fallback via `get_job()`
- Route ordering bug: `GET /api/jobs/history` defined AFTER `GET /api/jobs/{job_id}` — FastAPI matches "history" as path param

## Key File Locations

- `backend/api/routes/process.py` — all job REST endpoints + in-memory dicts
- `backend/api/services/processor_service.py` — ProcessorService with persist helpers
- `backend/api/services/catalog_service.py` — catalog sync, raw SQL (bug), status mismatch
- `backend/api/services/importer_service.py` — import jobs, correct persistence pattern
- `backend/api/websockets/progress.py` — ConnectionManager, WS validation
- `deckdex/storage/job_repository.py` — JobRepository (core layer, no framework deps)
- `migrations/008_jobs_table.sql` — jobs table schema (UUID PK, VARCHAR status, JSONB result)
- `backend/api/main.py` — startup hooks go here
- `frontend/src/contexts/ActiveJobsContext.tsx` — frontend job state, restores from GET /api/jobs on mount

## Architecture Constraints (confirmed)

- `deckdex/` has zero framework imports — no FastAPI, no SQLAlchemy direct in service files
- All DB ops through `storage/repository.py` or `storage/job_repository.py` — no raw SQL in services
- `catalog_service` violates this convention (uses `job_repo._engine()`) — architectural debt being fixed
- Google Sheets mode: `get_job_repo()` returns `None` — all repo calls must be guarded with `if job_repo:`
- Job state is intentionally in-memory (lost on restart) — Postgres is persistence layer, not primary state
