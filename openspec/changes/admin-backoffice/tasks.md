# Tasks: Admin Backoffice

## 1. Backend admin middleware

- [ ] 1.1 Add `require_admin` async dependency to `backend/api/dependencies.py`. It depends on `get_current_user` (via `Depends`), reads `DECKDEX_ADMIN_EMAIL` from `os.getenv()`, compares to `user["email"]` (case-insensitive), and raises `HTTPException(status_code=403, detail="Admin access required")` if they don't match. Returns the user payload on success.
- [ ] 1.2 Add `is_admin` helper function to `backend/api/dependencies.py`: `def is_admin_user(email: str) -> bool` that reads `DECKDEX_ADMIN_EMAIL` env var and returns `True` if the email matches (case-insensitive). Used by both `require_admin` and the `/api/auth/me` endpoint.

## 2. Backend auth/me modification

- [ ] 2.1 Add `is_admin: bool = False` field to the `UserPayload` Pydantic model in `backend/api/routes/auth.py`.
- [ ] 2.2 Update the `get_current_user` endpoint (`GET /api/auth/me`) in `backend/api/routes/auth.py` to compute `is_admin` by calling `is_admin_user(row["email"])` (imported from `backend/api/dependencies.py`) and include it in the `UserPayload` response.

## 3. Backend admin routes

- [ ] 3.1 Create `backend/api/routes/admin_routes.py` with an `APIRouter(prefix="/api/admin", tags=["admin"])`. All endpoints use `Depends(require_admin)`.
- [ ] 3.2 Add `POST /api/admin/catalog/sync` endpoint: check if catalog service is available (return 501 if not), delegate to catalog service `start_sync()`, return `{"job_id": ..., "status": "started", "message": "Catalog sync started"}`. Return 409 if sync already running.
- [ ] 3.3 Add `GET /api/admin/catalog/sync/status` endpoint: check if catalog service is available (return 501 if not), delegate to catalog service `get_sync_status()`, return sync state object with `last_bulk_sync`, `total_cards`, `total_images_downloaded`, `status`, `error_message`.
- [ ] 3.4 Register the admin router in `backend/api/main.py` by importing `admin_routes` and calling `app.include_router(admin_routes.router)` alongside existing routers.

## 4. Frontend AuthContext admin support

- [ ] 4.1 Add `is_admin?: boolean` to the `User` interface in `frontend/src/contexts/AuthContext.tsx`.
- [ ] 4.2 Update the `fetchMe()` function in `frontend/src/contexts/AuthContext.tsx` to map `data.is_admin` from the `/api/auth/me` response to `is_admin` in the user object, defaulting to `false` if not present.

## 5. Frontend API client admin methods

- [ ] 5.1 Add `CatalogSyncStatus` interface to `frontend/src/api/client.ts`: `{ last_bulk_sync: string | null, total_cards: number, total_images_downloaded: number, status: string, error_message: string | null }`.
- [ ] 5.2 Add `adminTriggerCatalogSync` method to the `api` object in `frontend/src/api/client.ts`: sends `POST` to `/api/admin/catalog/sync`, returns `{ job_id: string, status: string, message: string }`.
- [ ] 5.3 Add `adminGetCatalogSyncStatus` method to the `api` object in `frontend/src/api/client.ts`: sends `GET` to `/api/admin/catalog/sync/status`, returns `CatalogSyncStatus`.

## 6. Frontend AdminRoute guard

- [ ] 6.1 Create `frontend/src/components/AdminRoute.tsx`. Functional component that wraps children. Uses `useAuth()` to get `user`, `isAuthenticated`, and `isLoading`. Shows loading spinner while loading (same pattern as `frontend/src/components/ProtectedRoute.tsx`). Redirects to `/login` if not authenticated. Redirects to `/dashboard` if authenticated but `user.is_admin` is not true. Renders children if admin.

## 7. Frontend admin page

- [ ] 7.1 Create `frontend/src/pages/Admin.tsx`. Main admin page with catalog sync dashboard. Uses Tailwind for styling (matching existing dark/light theme support). Sections: page header ("Admin Dashboard"), catalog sync status card, sync controls.
- [ ] 7.2 Implement sync status display in `Admin.tsx`: on mount, call `api.adminGetCatalogSyncStatus()` via TanStack Query (or `useApi` hook pattern). Display: last sync timestamp (formatted with `toLocaleString()`, or "Never" if null), total cards count, total images downloaded count, current status with color-coded badge (idle=gray, syncing_data=blue, syncing_images=blue, completed=green, failed=red).
- [ ] 7.3 Implement "Start Sync" button in `Admin.tsx`: button calls `api.adminTriggerCatalogSync()`. Disabled when status is `syncing_data` or `syncing_images`. On success, store `job_id` and connect to WebSocket at `ws://host/ws/progress/{job_id}`. Handle 409 response gracefully (show "Sync already in progress" message).
- [ ] 7.4 Implement progress bar in `Admin.tsx`: when WebSocket events arrive with `type: 'progress'`, display phase label ("Downloading card data..." when `phase === 'data'`, "Downloading images..." when `phase === 'images'`), progress bar (Tailwind `bg-indigo-600` bar inside `bg-gray-200` track), current/total text. On `type: 'complete'` event, refresh sync status and show success message.
- [ ] 7.5 Implement error display in `Admin.tsx`: when sync status is `failed`, display the `error_message` in a red alert box. When WebSocket sends an error event, display it inline.

## 8. Frontend Navbar admin link

- [ ] 8.1 Update `frontend/src/components/Navbar.tsx`: conditionally add an "Admin" entry to the `navLinks` array (or render it separately) when `user?.is_admin` is true. The link points to `/admin`. Use the existing `LinkItem` component for consistent styling.

## 9. Frontend route registration

- [ ] 9.1 Update `frontend/src/App.tsx`: import `AdminRoute` from `./components/AdminRoute` and `Admin` page from `./pages/Admin`. Add a new `<Route path="/admin" element={<AdminRoute><Admin /></AdminRoute>} />` inside the `<Routes>` block, following the existing `ProtectedRoute` wrapping pattern.

## 10. Environment and configuration

- [ ] 10.1 Add `DECKDEX_ADMIN_EMAIL=` (empty placeholder) to `.env.example` if it exists, or document in the change notes that `DECKDEX_ADMIN_EMAIL` must be set in `.env` for admin features to work.

## 11. Tests

- [ ] 11.1 Backend unit test for `require_admin` dependency: test that admin email match returns user, non-match raises 403, missing env var raises 403, case-insensitive comparison works. Place in `tests/test_admin.py` or `tests/api/test_admin_routes.py`.
- [ ] 11.2 Backend unit test for `is_admin_user` helper: test match, no match, empty env var, case insensitivity.
- [ ] 11.3 Backend integration test for admin routes: test `POST /api/admin/catalog/sync` returns 403 for non-admin, 200 for admin (with mocked catalog service), 409 when sync already running, 501 when catalog service unavailable.
- [ ] 11.4 Backend integration test for `/api/auth/me` admin field: test that `is_admin` is `true` when email matches env var, `false` otherwise.
- [ ] 11.5 Frontend test for `AdminRoute` component: test renders children for admin user, redirects to `/dashboard` for non-admin, redirects to `/login` for unauthenticated.
- [ ] 11.6 Frontend test for Navbar admin link: test "Admin" link appears for admin user, does not appear for non-admin user.
