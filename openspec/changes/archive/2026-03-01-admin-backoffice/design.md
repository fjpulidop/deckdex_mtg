# Design: Admin Backoffice

## Context

- DeckDex has JWT-based authentication via Google OAuth. The `get_current_user` dependency in `backend/api/dependencies.py` extracts user payload (id, email, display_name, picture) from the JWT token. The `get_current_user_id` dependency extracts just the user ID.
- The frontend stores the JWT in `sessionStorage` and sends it via `Authorization: Bearer` header. The `AuthContext` provides `user` (with `id`, `email`, `display_name`, `avatar_url`), `isAuthenticated`, and `isLoading` to all components.
- The catalog-system change (dependency) creates: `catalog_cards` table, `catalog_sync_state` table, `CatalogSyncJob` background job, `CatalogRepository`, catalog API routes (`POST /api/catalog/sync`, `GET /api/catalog/sync/status`), and `ImageStore`. These endpoints are authenticated but not admin-gated.
- The existing Navbar in `frontend/src/components/Navbar.tsx` renders navigation links from a `navLinks` array: Dashboard, Decks (alpha), Analytics (beta). User dropdown has Profile, Settings, Logout.
- Routes are defined in `frontend/src/App.tsx` using React Router. Protected routes wrap children in `ProtectedRoute` which checks `isAuthenticated`.
- Backend routers are registered in `backend/api/main.py` via `app.include_router()`.
- WebSocket progress follows the `ConnectionManager` pattern in `backend/api/websockets/progress.py`: clients connect to `/ws/progress/{job_id}` and receive `progress`, `error`, and `complete` events.
- The `/api/auth/me` endpoint returns `UserPayload(id, email, display_name, picture)` from `backend/api/routes/auth.py`.

## Goals / Non-Goals

**Goals:**

- Gate admin API endpoints behind a `require_admin` dependency that compares the authenticated user's email to `DECKDEX_ADMIN_EMAIL` env var.
- Expose admin status to the frontend via the `/api/auth/me` response.
- Add an `/admin` route in the frontend accessible only to admin users.
- Show an "Admin" link in the Navbar only for admin users.
- Build a catalog sync dashboard as the first admin page: sync status display, trigger sync button, real-time progress via WebSocket.

**Non-Goals:**

- Role-based access control (RBAC) or multi-admin support. Single admin via env var is sufficient.
- Admin user management page (future).
- Persisting admin status in the database (derived from env var at runtime).
- Implementing catalog sync logic (that belongs to catalog-system).
- Admin audit logging (future).

## Decisions

1. **Admin identification: env var, not DB flag**
   - **Decision:** The admin user is identified by comparing the authenticated user's email against the `DECKDEX_ADMIN_EMAIL` environment variable. No `is_admin` column in the `users` table.
   - **Rationale:** Single-admin, localhost-focused app. Env var is the simplest mechanism: no migration, no UI to manage roles, easy to change per deployment. Matches the existing pattern where secrets and deployment config live in `.env` (not `config.yaml`).
   - **Alternatives:** `is_admin` boolean column in `users` table (requires migration, seed script changes, risk of accidental admin grants); role table with many-to-many (massive overkill for single admin).

2. **`require_admin` as a FastAPI dependency**
   - **Decision:** Create an `async def require_admin(user = Depends(get_current_user))` dependency in `backend/api/dependencies.py`. It reads `DECKDEX_ADMIN_EMAIL` from env, compares to `user["email"]`, and raises `HTTPException(403)` if they don't match. Admin routes use `Depends(require_admin)`.
   - **Rationale:** Follows the existing FastAPI dependency injection pattern (like `get_current_user`, `get_current_user_id`). Composable: `require_admin` depends on `get_current_user`, so authentication is checked first, then authorization. Thin routes stay thin.
   - **Alternatives:** Middleware (too broad, would need path matching); decorator (not idiomatic FastAPI); inline check in each route (duplication).

3. **`is_admin` field in `/api/auth/me` response**
   - **Decision:** Modify the `/api/auth/me` endpoint in `backend/api/routes/auth.py` to include an `is_admin: bool` field in the `UserPayload` response. Computed at request time by comparing the user's email to `DECKDEX_ADMIN_EMAIL`.
   - **Rationale:** The frontend needs to know whether to show the Admin nav link and whether to allow navigation to `/admin`. Embedding it in the existing `/api/auth/me` response avoids an extra API call. It is computed, not stored, so it's always consistent with the env var.
   - **Alternatives:** Separate `GET /api/admin/check` endpoint (extra round-trip on every page load); embed in JWT claims (stale if env var changes during token lifetime).

4. **Separate `/admin` route, not inside Settings**
   - **Decision:** Admin functionality lives under a dedicated `/admin` route in the frontend, not as a tab inside the Settings modal. The admin page has its own layout (admin navigation sidebar or header) separate from the regular Navbar.
   - **Rationale:** Admin operations (catalog sync, future user management) are fundamentally different from user settings (profile, preferences). Mixing them creates confusion. A separate route allows the admin area to grow independently with its own navigation.
   - **Alternatives:** Tab in Settings modal (cluttered, hard to extend); top-level route without separate nav (no room for future admin pages).

5. **`AdminRoute` guard component**
   - **Decision:** Create `frontend/src/components/AdminRoute.tsx` that wraps children, checks `user.is_admin` from `AuthContext`, and redirects non-admin users to `/dashboard`. Similar to `ProtectedRoute` but adds the admin check on top of authentication.
   - **Rationale:** Follows the existing `ProtectedRoute` pattern exactly. Clean separation: `ProtectedRoute` checks auth, `AdminRoute` checks auth + admin. Route-level guard means individual admin pages don't need to repeat the check.
   - **Alternatives:** Inline check in each admin page (duplication); single `ProtectedRoute` with role parameter (over-generalizing for one case).

6. **Admin nav link conditionally rendered in Navbar**
   - **Decision:** Add an "Admin" entry to the `navLinks` array in `frontend/src/components/Navbar.tsx`, but only render it when `user.is_admin` is true. The link points to `/admin` and uses a shield/settings icon to distinguish it from regular nav items.
   - **Rationale:** Admin link should be visible in the primary navigation for discoverability, but only for the admin user. Conditional rendering keeps the regular user's experience clean.
   - **Alternatives:** Only in user dropdown (easy to miss); always visible but disabled (confusing for non-admins).

7. **Admin routes under `/api/admin/` prefix**
   - **Decision:** All admin API routes live under `/api/admin/` prefix. The catalog sync endpoints are: `POST /api/admin/catalog/sync` (trigger sync), `GET /api/admin/catalog/sync/status` (get status). These delegate to the same catalog service that powers `/api/catalog/sync` but are gated by `require_admin`.
   - **Rationale:** Clear URL separation between user endpoints and admin endpoints. The `/api/admin/` prefix makes it obvious in logs, docs, and CORS config that these are privileged endpoints. The admin routes delegate to the catalog service, keeping routes thin.
   - **Alternatives:** Reuse `/api/catalog/sync` with admin check (mixes concerns; sync should be admin-only but search should not); separate FastAPI app (overkill).

8. **Catalog sync dashboard UI**
   - **Decision:** The admin catalog dashboard shows: (a) sync status card with last sync timestamp, total cards in catalog, total images downloaded, and current sync status; (b) "Start Sync" button (disabled while sync is running); (c) progress section with phase indicator (data/images), progress bar, and current/total count. Progress updates come via WebSocket using the existing `ConnectionManager` pattern. The page polls `/api/admin/catalog/sync/status` on mount for the static status, then connects to WebSocket when a sync is running.
   - **Rationale:** Matches the existing job progress patterns (e.g., `JobsBottomBar`, `ActiveJobsContext`). Combines REST for initial state with WebSocket for real-time updates. Phase indicator is important because catalog sync has two distinct phases (data download, then image download) with very different durations.
   - **Alternatives:** Polling only (laggy for long-running sync); WebSocket only (no initial state on page load).

## Risks / Trade-offs

- **Risk:** `DECKDEX_ADMIN_EMAIL` env var is not set. **Mitigation:** If the env var is empty or missing, the `require_admin` dependency always raises 403. The `/api/auth/me` response returns `is_admin: false` for all users. The "Admin" link never appears in the Navbar. This is a safe default.
- **Risk:** Admin email changes while a user has an active session. **Mitigation:** `is_admin` is computed on every `/api/auth/me` call and every admin API request (reads env var fresh). No stale data.
- **Risk:** Catalog service from catalog-system may not be deployed yet when admin-backoffice code is deployed. **Mitigation:** Admin routes check if catalog service/repository is available and return 501 (Not Implemented) if not. Similar to how deck routes handle missing Postgres.
- **Trade-off:** Single admin via env var means no multi-admin support. This is intentional for the current scope (localhost app). A future change can introduce a role system if needed.
- **Trade-off:** Admin status is not in the JWT, so the frontend must call `/api/auth/me` to know. This is already the case (AuthContext calls `/api/auth/me` on load), so no extra cost.

## Migration Plan

1. No database migrations required. Admin status is derived from env var comparison.
2. Add `DECKDEX_ADMIN_EMAIL` to `.env.example` with a placeholder value.
3. Deploy backend with `require_admin` dependency and admin routes. Existing endpoints are unaffected.
4. Deploy frontend with `AdminRoute`, admin page, and Navbar changes. Non-admin users see no difference.
5. Set `DECKDEX_ADMIN_EMAIL` in `.env` to the desired admin email. Admin link appears for that user on next `/api/auth/me` call.

## Open Questions

- None. All decisions finalized.
