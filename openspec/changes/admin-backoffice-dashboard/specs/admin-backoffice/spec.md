# Admin Backoffice — Delta Spec

This delta spec adds the missing test coverage requirements to the existing
`openspec/specs/admin-backoffice/spec.md`. All other requirements in the base spec are
already implemented and verified. No other sections change.

---

## Requirement: Admin endpoint access control tests

The test suite SHALL include HTTP-level integration tests for admin endpoint access
control using the FastAPI `TestClient` against the real application stack.

### Scenario: Unauthenticated request to admin catalog sync trigger returns 401

- **GIVEN** no valid JWT cookie is present in the request
- **WHEN** `POST /api/admin/catalog/sync` is called
- **THEN** the response SHALL be HTTP 401 Unauthorized

### Scenario: Unauthenticated request to admin catalog sync status returns 401

- **GIVEN** no valid JWT cookie is present in the request
- **WHEN** `GET /api/admin/catalog/sync/status` is called
- **THEN** the response SHALL be HTTP 401 Unauthorized

### Scenario: Non-admin authenticated request to admin catalog sync trigger returns 403

- **GIVEN** a valid JWT for a non-admin user is present
- **WHEN** `POST /api/admin/catalog/sync` is called
- **THEN** the response SHALL be HTTP 403 Forbidden
- **AND** the response body SHALL contain `{"detail": "Admin access required"}`

### Scenario: Non-admin authenticated request to admin catalog sync status returns 403

- **GIVEN** a valid JWT for a non-admin user is present
- **WHEN** `GET /api/admin/catalog/sync/status` is called
- **THEN** the response SHALL be HTTP 403 Forbidden
- **AND** the response body SHALL contain `{"detail": "Admin access required"}`

## Requirement: Admin sync trigger integration test

The test suite SHALL include an integration test verifying the admin sync trigger
endpoint's happy path and error conditions.

### Scenario: Admin user triggers catalog sync successfully

- **GIVEN** a valid JWT for an admin user is present
- **AND** no sync is currently running
- **AND** the catalog repository is available
- **WHEN** `POST /api/admin/catalog/sync` is called
- **THEN** the response SHALL be HTTP 200 OK
- **AND** the response body SHALL contain `job_id` (a non-empty string), `status`
  (value `"started"`), and `message` (value `"Catalog sync started"`)

### Scenario: Admin user triggers sync when one is already running

- **GIVEN** a valid JWT for an admin user is present
- **AND** a catalog sync is already in progress
- **WHEN** `POST /api/admin/catalog/sync` is called
- **THEN** the response SHALL be HTTP 409 Conflict
- **AND** the response body SHALL contain `{"detail": "Catalog sync already in progress"}`

### Scenario: Admin user triggers sync when catalog is unavailable

- **GIVEN** a valid JWT for an admin user is present
- **AND** the catalog repository is not available (PostgreSQL not configured)
- **WHEN** `POST /api/admin/catalog/sync` is called
- **THEN** the response SHALL be HTTP 501 Not Implemented
- **AND** the response body SHALL contain `{"detail": "Catalog system not available"}`

## Requirement: Admin sync status integration test

### Scenario: Admin user retrieves catalog sync status

- **GIVEN** a valid JWT for an admin user is present
- **AND** the catalog repository is available
- **WHEN** `GET /api/admin/catalog/sync/status` is called
- **THEN** the response SHALL be HTTP 200 OK
- **AND** the response body SHALL contain keys: `last_bulk_sync`, `total_cards`,
  `total_images_downloaded`, `status`, `error_message`

## Implementation notes

- All pytest fixtures SHALL use `scope="function"` (not `scope="module"`)
- `catalog_service.start_sync` SHALL be mocked in any test calling the sync trigger
  endpoint to prevent real background threads from spawning
- `is_admin_user` SHALL be patched via `unittest.mock.patch.object` (it is a plain
  function, not a FastAPI dependency, and cannot be overridden via
  `app.dependency_overrides`)
- `promote_bootstrap_admin` SHALL be patched to a no-op in admin user test fixtures
- The test file SHALL be located at `tests/test_admin_routes.py`
