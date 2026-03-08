## ADDED Requirements

### Requirement: Startup cleanup for stale sync state

On application startup, any `catalog_sync_state` row with status `syncing_data` or `syncing_images` must be reset to `idle`. This prevents the UI from being permanently stuck in "syncing" after an unclean shutdown.

#### Scenario: Server restarts while catalog sync was running
- **WHEN** the backend starts and `catalog_sync_state.status` is `syncing_data` or `syncing_images`
- **THEN** the status is updated to `idle` and `updated_at` is set to current time

#### Scenario: Server restarts with no active sync
- **WHEN** the backend starts and `catalog_sync_state.status` is `idle` or `failed`
- **THEN** no changes are made to `catalog_sync_state`
