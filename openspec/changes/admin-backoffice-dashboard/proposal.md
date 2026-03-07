# Proposal: Admin Backoffice Dashboard with Catalog Sync Management

## What and Why

The admin backoffice feature gives the designated system administrator a dedicated
section of the web dashboard for managing catalog sync operations. The catalog sync
is a long-running background job that downloads the full Scryfall bulk card data and
associated images into the local PostgreSQL database. Without an admin UI, triggering
or monitoring this operation requires direct API access or server-side intervention.

This proposal covers completing the admin backoffice deliverables that remain outstanding
after an initial implementation pass:

1. Verify and document that `/api/auth/me` correctly returns `is_admin` in its response
   payload (the `UserPayload` model and the route handler already include `is_admin`, but
   this has not been explicitly tested at the HTTP integration level).

2. Add HTTP-level integration tests for admin endpoint access control: a 401 response for
   unauthenticated requests and a 403 response for authenticated non-admin requests. The
   existing `tests/test_admin.py` exercises only inline logic mirrors, not the actual
   FastAPI route stack.

3. Add an integration test for the admin sync trigger endpoint to verify the full request
   path including the `require_admin` dependency, the `catalog_service.start_sync` call,
   and the expected response shape.

## Product Motivation

Catalog sync is the foundational operation that populates the card database used by every
feature in the app (collection search, card resolution, deck import, catalog-backed
autocomplete). An admin UI with progress monitoring is more reliable and observable than
ad-hoc API calls. The admin user can trigger syncs without needing terminal access.

## Scope

This change is narrowly scoped to the test coverage gap. The backend routes, frontend
pages, API client methods, AuthContext, AdminRoute guard, and Navbar admin link are all
already implemented and functioning. The delta is:

- Backend: confirm `/api/auth/me` returns `is_admin` (code audit, no changes needed)
- Tests: add `tests/test_admin_routes.py` with FastAPI TestClient integration tests
  covering 401/403 access control and the sync trigger happy path

## Out of Scope

- Changes to the Admin page UI (already complete and matches spec requirements)
- Changes to the Navbar or AdminRoute (already complete)
- Changes to the API client (already complete)
- i18n additions (en.json and es.json already have all required `admin.*` keys)
- Database migrations (migration 013 adding `is_admin` to users table already exists)

## Success Criteria

1. `GET /api/auth/me` response is confirmed to include `is_admin: bool` — verified by
   reading the auth route source code (already done: `UserPayload` model and route handler
   both include `is_admin`).

2. `tests/test_admin_routes.py` passes with `pytest tests/test_admin_routes.py`:
   - Unauthenticated request to `POST /api/admin/catalog/sync` returns 401.
   - Unauthenticated request to `GET /api/admin/catalog/sync/status` returns 401.
   - Authenticated non-admin request to `POST /api/admin/catalog/sync` returns 403.
   - Authenticated non-admin request to `GET /api/admin/catalog/sync/status` returns 403.
   - Authenticated admin request to `POST /api/admin/catalog/sync` returns 200 with
     `{job_id, status, message}`.
   - Authenticated admin request to `GET /api/admin/catalog/sync/status` returns 200
     with the catalog sync state shape.

3. All existing tests continue to pass (`pytest tests/`).
