# Admin Backoffice

Admin access control and admin dashboard for DeckDex MTG. Provides a dedicated, access-controlled section of the web dashboard where the designated admin user can manage system-level operations. The first admin feature is catalog sync management (trigger, monitor, inspect), built on top of the catalog-system capability.

## Requirements

### Requirement: Admin identification via environment variable

The system SHALL identify the admin user by comparing the authenticated user's email to the `DECKDEX_ADMIN_EMAIL` environment variable. Admin status is not stored in the database.

#### Scenario: Admin email matches

- **WHEN** the `DECKDEX_ADMIN_EMAIL` environment variable is set to `admin@example.com`
- **AND** the authenticated user's email is `admin@example.com`
- **THEN** the system SHALL consider the user an admin

#### Scenario: Admin email does not match

- **WHEN** the `DECKDEX_ADMIN_EMAIL` environment variable is set to `admin@example.com`
- **AND** the authenticated user's email is `user@example.com`
- **THEN** the system SHALL NOT consider the user an admin

#### Scenario: Admin email not configured

- **WHEN** the `DECKDEX_ADMIN_EMAIL` environment variable is not set or is empty
- **THEN** the system SHALL NOT consider any user an admin

### Requirement: Backend admin dependency

The system SHALL provide a `require_admin` FastAPI dependency in `backend/api/dependencies.py` that gates admin-only routes.

#### Scenario: Admin user accesses admin endpoint

- **WHEN** an authenticated admin user calls an endpoint protected by `require_admin`
- **THEN** the request SHALL proceed normally
- **AND** the dependency SHALL return the user payload

#### Scenario: Non-admin user accesses admin endpoint

- **WHEN** an authenticated non-admin user calls an endpoint protected by `require_admin`
- **THEN** the system SHALL return HTTP 403 Forbidden
- **AND** the response body SHALL contain `{"detail": "Admin access required"}`

#### Scenario: Unauthenticated request to admin endpoint

- **WHEN** an unauthenticated request is made to an endpoint protected by `require_admin`
- **THEN** the system SHALL return HTTP 401 Unauthorized
- **AND** authentication SHALL be checked before the admin check (via `Depends(get_current_user)`)

### Requirement: Admin status in auth/me response

The system SHALL expose admin status to the frontend via the `/api/auth/me` endpoint response.

#### Scenario: Admin user calls /api/auth/me

- **WHEN** an admin user calls `GET /api/auth/me`
- **THEN** the response SHALL include `is_admin: true` in addition to existing fields (id, email, display_name, picture)

#### Scenario: Non-admin user calls /api/auth/me

- **WHEN** a non-admin user calls `GET /api/auth/me`
- **THEN** the response SHALL include `is_admin: false`

### Requirement: Admin API routes

The system SHALL provide admin API routes under the `/api/admin/` prefix, all gated by the `require_admin` dependency. These routes delegate to the catalog service from catalog-system.

#### Scenario: Trigger catalog sync

- **WHEN** an admin user calls `POST /api/admin/catalog/sync`
- **THEN** the system SHALL start a catalog sync background job via the catalog service
- **AND** return `{"job_id": "<uuid>", "status": "started", "message": "Catalog sync started"}`
- **AND** the job SHALL be tracked in the `jobs` table with type `catalog_sync`

#### Scenario: Trigger sync when already running

- **WHEN** an admin user calls `POST /api/admin/catalog/sync`
- **AND** a catalog sync is already in progress
- **THEN** the system SHALL return HTTP 409 Conflict
- **AND** the response SHALL contain `{"detail": "Catalog sync already in progress"}`

#### Scenario: Get catalog sync status

- **WHEN** an admin user calls `GET /api/admin/catalog/sync/status`
- **THEN** the system SHALL return the current catalog sync state including: last_bulk_sync (ISO timestamp or null), total_cards (integer), total_images_downloaded (integer), status (one of: idle, syncing_data, syncing_images, completed, failed), error_message (string or null)

#### Scenario: Catalog service not available

- **WHEN** an admin user calls any `/api/admin/catalog/*` endpoint
- **AND** the catalog service is not available (e.g., catalog-system not deployed, no DATABASE_URL)
- **THEN** the system SHALL return HTTP 501 Not Implemented
- **AND** the response SHALL contain `{"detail": "Catalog system not available"}`

### Requirement: Admin route registration

The admin router SHALL be registered in `backend/api/main.py` alongside existing routers.

#### Scenario: Admin routes are accessible

- **WHEN** the backend starts
- **THEN** routes under `/api/admin/` SHALL be registered and accessible
- **AND** the admin router SHALL use the `admin` tag for OpenAPI documentation

### Requirement: WebSocket progress for catalog sync

The system SHALL support real-time progress monitoring for catalog sync jobs via the existing WebSocket pattern.

#### Scenario: Admin monitors sync progress

- **WHEN** an admin triggers a catalog sync and receives a `job_id`
- **AND** the admin connects to `/ws/progress/{job_id}`
- **THEN** the system SHALL send progress events with: phase (`data` or `images`), current (integer), total (integer), percentage (float)

#### Scenario: Sync completion event

- **WHEN** a catalog sync job completes
- **THEN** the system SHALL send a `complete` event via WebSocket with: total_cards, total_images_downloaded, duration_seconds

### Requirement: Frontend admin route guard

The frontend SHALL provide an `AdminRoute` component that restricts access to admin pages.

#### Scenario: Admin user navigates to /admin

- **WHEN** an authenticated admin user navigates to `/admin`
- **THEN** the admin page SHALL render

#### Scenario: Non-admin user navigates to /admin

- **WHEN** an authenticated non-admin user navigates to `/admin`
- **THEN** the system SHALL redirect to `/dashboard`

#### Scenario: Unauthenticated user navigates to /admin

- **WHEN** an unauthenticated user navigates to `/admin`
- **THEN** the system SHALL redirect to `/login` (via `ProtectedRoute` behavior)

### Requirement: Conditional admin navigation link

The main Navbar SHALL conditionally show an "Admin" link for admin users only.

#### Scenario: Admin user sees admin link

- **WHEN** the Navbar renders for an admin user (user.is_admin is true)
- **THEN** an "Admin" link SHALL appear in the navigation
- **AND** the link SHALL point to `/admin`

#### Scenario: Non-admin user does not see admin link

- **WHEN** the Navbar renders for a non-admin user (user.is_admin is false or undefined)
- **THEN** no "Admin" link SHALL appear in the navigation

#### Scenario: Admin link active state

- **WHEN** the admin user is on the `/admin` route
- **THEN** the "Admin" link SHALL show an active/selected visual state (matching existing nav link styling)

### Requirement: Admin catalog sync dashboard

The admin page SHALL display a catalog sync dashboard as its first feature.

#### Scenario: Dashboard shows sync status on load

- **WHEN** an admin navigates to `/admin`
- **THEN** the page SHALL call `GET /api/admin/catalog/sync/status`
- **AND** display: last sync timestamp (formatted, or "Never" if null), total cards in catalog, total images downloaded, current sync status (idle, syncing_data, syncing_images, completed, failed)

#### Scenario: Start sync button

- **WHEN** the sync status is `idle`, `completed`, or `failed`
- **THEN** the "Start Sync" button SHALL be enabled
- **WHEN** the admin clicks "Start Sync"
- **THEN** the system SHALL call `POST /api/admin/catalog/sync`
- **AND** disable the button
- **AND** connect to WebSocket for progress updates

#### Scenario: Start sync button disabled during sync

- **WHEN** the sync status is `syncing_data` or `syncing_images`
- **THEN** the "Start Sync" button SHALL be disabled
- **AND** show a label indicating sync is in progress

#### Scenario: Progress bar with phase indicator

- **WHEN** a catalog sync is running and WebSocket events are received
- **THEN** the page SHALL display a progress bar with: current phase label ("Downloading card data..." or "Downloading images..."), progress bar showing percentage, text showing current/total count

#### Scenario: Sync completion updates status

- **WHEN** a WebSocket `complete` event is received
- **THEN** the page SHALL update the sync status display with the new values
- **AND** re-enable the "Start Sync" button
- **AND** show a success message

#### Scenario: Sync failure display

- **WHEN** the sync status is `failed`
- **THEN** the page SHALL display the error message from the sync state
- **AND** the "Start Sync" button SHALL remain enabled (to allow retry)

### Requirement: Frontend AuthContext admin support

The `AuthContext` SHALL expose the user's admin status to all components.

#### Scenario: User type includes is_admin

- **WHEN** `/api/auth/me` returns `is_admin: true`
- **THEN** the `AuthContext` user object SHALL have `is_admin: true`
- **AND** components using `useAuth()` SHALL be able to read `user.is_admin`

#### Scenario: User type defaults is_admin to false

- **WHEN** `/api/auth/me` does not return an `is_admin` field (backward compatibility)
- **THEN** the `AuthContext` user object SHALL default `is_admin` to `false`

### Requirement: Frontend API client admin methods

The API client in `frontend/src/api/client.ts` SHALL provide methods for admin endpoints.

#### Scenario: Trigger catalog sync

- **WHEN** `api.adminTriggerCatalogSync()` is called
- **THEN** it SHALL send `POST /api/admin/catalog/sync` with auth headers
- **AND** return `{ job_id: string, status: string, message: string }`

#### Scenario: Get catalog sync status

- **WHEN** `api.adminGetCatalogSyncStatus()` is called
- **THEN** it SHALL send `GET /api/admin/catalog/sync/status` with auth headers
- **AND** return `{ last_bulk_sync: string | null, total_cards: number, total_images_downloaded: number, status: string, error_message: string | null }`
