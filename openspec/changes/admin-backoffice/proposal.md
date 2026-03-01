# Proposal: Admin Backoffice

## Why

DeckDex currently has no admin interface. The catalog-system change introduces a background sync job that downloads Scryfall bulk data and images, but there is no way for an administrator to trigger, monitor, or inspect catalog syncs from the web UI. Without an admin area, the only way to manage catalog operations would be direct API calls or CLI scripts, which is fragile and opaque.

An admin backoffice provides a dedicated, access-controlled section of the web dashboard where the designated admin user can manage system-level operations. The first feature is catalog sync management: triggering syncs, viewing progress in real time via WebSocket, and inspecting the current catalog state (last sync timestamp, total cards, images downloaded). This lays the foundation for future admin capabilities (user management, system health, etc.) without cluttering the regular user experience.

## What Changes

- New **admin middleware** on the backend that checks whether the authenticated user's email matches the `DECKDEX_ADMIN_EMAIL` environment variable. Non-admin users receive 403 on admin endpoints.
- New **admin API routes** under `/api/admin/` that proxy catalog sync operations (trigger sync, get sync status) through the admin access gate. These routes delegate to the catalog service created by the catalog-system change.
- New **`/admin` route** on the frontend with its own layout and navigation, accessible only to admin users.
- **Admin catalog dashboard** page showing: sync status (last sync timestamp, total cards, total images downloaded, current status), a "Start Sync" button, and a real-time progress bar with WebSocket updates showing phase (data/images), current/total, and percentage.
- **Conditional admin link** in the main Navbar: an "Admin" link appears only when the logged-in user's email matches the admin email (exposed via an `is_admin` field added to the `/api/auth/me` response).

## Capabilities

### New Capabilities

- **admin-backoffice**: Admin access control and admin dashboard. Defines the admin user identification mechanism (env var `DECKDEX_ADMIN_EMAIL`), the backend middleware/dependency for admin-only routes, the admin API prefix (`/api/admin/`), the frontend `/admin` route with dedicated navigation, and the catalog sync dashboard as the first admin feature. The admin area is separate from the regular dashboard and only visible/accessible to admin users.

### Modified Capabilities

- **web-dashboard-ui**: Add conditional "Admin" navigation link in the Navbar for admin users. Add `/admin` route and admin layout. The admin link only renders when the current user is identified as admin.
- **web-api-backend**: New admin router under `/api/admin/` with admin middleware dependency. Endpoints for catalog sync management (trigger, status) that delegate to catalog service. Modified `/api/auth/me` response to include `is_admin` boolean field.
- **configuration-management**: New `DECKDEX_ADMIN_EMAIL` environment variable recognized by the backend. Not stored in `config.yaml` (it is a secret/deployment concern).

## Impact

- **Backend**: New `backend/api/routes/admin_routes.py` with admin middleware dependency. New `require_admin` dependency in `backend/api/dependencies.py`. Modified `/api/auth/me` response to include `is_admin` field. Router registered in `backend/api/main.py`.
- **Frontend**: New `frontend/src/pages/Admin.tsx` page with catalog sync UI. New `frontend/src/components/AdminRoute.tsx` guarding `/admin` routes. Modified `frontend/src/components/Navbar.tsx` to conditionally show "Admin" link. New API client methods for admin endpoints in `frontend/src/api/client.ts`. Modified `frontend/src/contexts/AuthContext.tsx` user type to include `is_admin`.
- **Config/Env**: New `DECKDEX_ADMIN_EMAIL` env var in `.env`. No changes to `config.yaml`.
- **Data**: No database schema changes. Admin status is derived from env var comparison at runtime, not stored in the database.
- **Dependencies**: No new dependencies. Reuses existing JWT auth (`get_current_user` in `backend/api/dependencies.py`), WebSocket `ConnectionManager` in `backend/api/websockets/progress.py`, and catalog service from the catalog-system change.
