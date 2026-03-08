## Why

When Docker is stopped while background jobs are running (catalog sync, price updates, card processing), the persisted state in Postgres becomes stale. Catalog sync status stays as `syncing_*` forever, and orphaned job rows appear as active in the frontend. The frontend's `ActiveJobsContext` restores all jobs from `/api/jobs` without filtering by status, causing ghost jobs that show 0% progress indefinitely.

## What Changes

- Reset `catalog_sync_state.status` to `idle` on backend startup if currently `syncing_*`
- Filter restored jobs in `ActiveJobsContext` to only include `running`/`pending` status
- Add a `mark_orphan_syncs` method to `CatalogRepository` for startup cleanup

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `catalog-system`: Add startup cleanup for stale sync state
- `global-jobs-ui`: Filter restored jobs by status to prevent ghost jobs

## Impact

- `backend/api/main.py`: Additional startup cleanup call
- `deckdex/catalog/repository.py`: New `mark_orphan_syncs()` method
- `frontend/src/contexts/ActiveJobsContext.tsx`: Filter logic in `restoreJobs()`
- No API changes, no breaking changes, no new dependencies
