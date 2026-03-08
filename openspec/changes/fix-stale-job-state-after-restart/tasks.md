## 1. Backend: Catalog sync state cleanup on startup

- [x] 1.1 Add `mark_orphan_syncs()` method to `CatalogRepository` that updates `catalog_sync_state` rows with status `syncing_data` or `syncing_images` to `idle`
- [x] 1.2 Call `mark_orphan_syncs()` in `backend/api/main.py` `startup_event()` after existing `mark_orphans_as_error()`, using the catalog repo from dependencies

## 2. Frontend: Filter restored jobs by status

- [x] 2.1 Update `ActiveJobsContext.restoreJobs()` to only add jobs with status `running` or `pending` to the active jobs list
- [x] 2.2 Update the `visibilitychange` re-sync handler to also filter by status when adding new jobs from the server

## 3. Tests

- [x] 3.1 Add pytest test for `mark_orphan_syncs()`: verify it resets `syncing_*` to `idle` and leaves `idle`/`failed` unchanged
- [x] 3.2 Add pytest test for `startup_event` calling both orphan cleanup methods
