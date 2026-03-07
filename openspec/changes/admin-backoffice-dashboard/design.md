# Design: Admin Backoffice Dashboard — Test Coverage Gap

## Change Summary

The admin backoffice feature is substantially complete. All backend routes, frontend
pages, API client methods, AuthContext, AdminRoute guard, and Navbar conditional link
are implemented and match the spec. The `/api/auth/me` endpoint returns `is_admin` via
the `UserPayload` Pydantic model in `backend/api/routes/auth.py` (line 100-106) and the
route handler (lines 330-368).

The single remaining gap is HTTP-level integration tests. The existing
`tests/test_admin.py` uses an inline mirror of the business logic rather than the actual
FastAPI application, so it does not verify that the dependency chain (`require_admin`
→ `get_current_user` → JWT extraction → DB admin check) works correctly at the HTTP
boundary.

## Impact Analysis

### What is already implemented (no changes needed)

| File | What it covers |
|------|----------------|
| `backend/api/routes/admin_routes.py` | `POST /api/admin/catalog/sync`, `GET /api/admin/catalog/sync/status`, both gated by `require_admin` |
| `backend/api/dependencies.py` | `require_admin`, `is_admin_user`, `promote_bootstrap_admin`, `get_current_user` |
| `backend/api/routes/auth.py` | `GET /api/auth/me` returns `UserPayload` with `is_admin: bool` |
| `backend/api/services/catalog_service.py` | `start_sync`, `get_sync_status` |
| `frontend/src/pages/Admin.tsx` | Full admin page: status grid, progress bar, WebSocket, sync button |
| `frontend/src/contexts/AuthContext.tsx` | `User.is_admin?: boolean`, populated from `/api/auth/me` |
| `frontend/src/components/AdminRoute.tsx` | Route guard: unauthenticated → /login, non-admin → /dashboard |
| `frontend/src/components/Navbar.tsx` | Admin link conditionally rendered when `user?.is_admin` |
| `frontend/src/api/client.ts` | `adminTriggerCatalogSync()`, `adminGetCatalogSyncStatus()`, `CatalogSyncStatus` type |
| `frontend/src/locales/en.json` | All `admin.*` i18n keys present |
| `frontend/src/locales/es.json` | All `admin.*` i18n keys present |

### What needs to be created

| File | What it adds |
|------|--------------|
| `tests/test_admin_routes.py` | FastAPI TestClient integration tests for admin endpoint access control and sync trigger |

## Implementation Design

### Test architecture

The test module uses FastAPI's `TestClient` (which wraps Starlette's test client) against
the real application from `backend/api/main.py`. This exercises the full middleware and
dependency injection stack, unlike the existing `tests/test_admin.py` which mirrors the
logic inline.

**Authentication mock pattern**: The tests must simulate JWT cookie authentication. The
cleanest approach is to patch `backend.api.dependencies.get_current_user` via
`app.dependency_overrides` to inject a controlled user payload without going through the
full OAuth flow. This is the same pattern used in `tests/test_decks.py` with
`require_deck_repo` overrides.

For admin tests, three user states are needed:
1. **Unauthenticated**: let `get_current_user` raise `HTTPException(401)` (no override,
   or override to raise)
2. **Non-admin**: override `get_current_user` to return `{"sub": "2", "email": "user@example.com"}`
   and override `is_admin_user` to return `False`
3. **Admin**: override `get_current_user` to return `{"sub": "1", "email": "admin@example.com"}`
   and override `is_admin_user` to return `True`; also override `promote_bootstrap_admin`
   to no-op

**Catalog service mock**: The `start_sync` function launches a background thread and
requires a `CatalogRepository` and `ImageStore`. For integration tests we must mock
`catalog_service.start_sync` at the service layer to avoid starting real threads or
requiring a database. The 501 case is tested by mocking `get_catalog_repo` to return
`None`.

**Key design decisions**:

1. Use `app.dependency_overrides` rather than `@patch` decorators for `get_current_user`
   because FastAPI's dependency resolution happens inside the framework, not in Python
   callsite scope. `@patch` cannot intercept FastAPI DI.

2. All pytest fixtures must use `scope="function"` (not `scope="module"`) to avoid
   cross-test pollution via the `dependency_overrides` dict.

3. `require_admin` itself is not overridden — it is tested through its real implementation,
   which calls `is_admin_user`. Only `is_admin_user` and `get_current_user` are overridden.
   This validates the actual dependency chain.

4. For the sync trigger test, `catalog_service.start_sync` is patched at the module level
   in `admin_routes` (`backend.api.routes.admin_routes.catalog_service.start_sync`) to
   return a fixed UUID string. This is more robust than patching the service module
   directly because it intercepts at the call site.

5. The 409 (sync already running) case is tested by patching `start_sync` to raise
   `RuntimeError("A catalog sync is already running")`.

6. The 501 (catalog unavailable) case is tested by patching
   `backend.api.routes.admin_routes.get_catalog_repo` (the helper inside admin_routes)
   — or more precisely, `backend.api.routes.admin_routes._get_catalog_repo_or_501` —
   but since `_get_catalog_repo_or_501` calls `get_catalog_repo()` from dependencies,
   the cleanest approach is to override the `get_catalog_repo` dependency in
   `dependencies.py` to return `None`.

### Test structure

```
tests/test_admin_routes.py

Fixtures (all scope="function"):
  - app_client: TestClient with no dependency overrides (unauthenticated state)
  - non_admin_client: TestClient with get_current_user overridden to return non-admin user
  - admin_client: TestClient with get_current_user overridden to return admin user,
                   is_admin_user overridden to return True

Test classes:
  TestAdminCatalogSyncAccessControl:
    - test_unauthenticated_sync_trigger_returns_401
    - test_unauthenticated_sync_status_returns_401
    - test_non_admin_sync_trigger_returns_403
    - test_non_admin_sync_status_returns_403

  TestAdminSyncTrigger:
    - test_admin_sync_trigger_returns_200_with_job_id
    - test_admin_sync_trigger_returns_409_when_already_running
    - test_admin_sync_trigger_returns_501_when_catalog_unavailable

  TestAdminSyncStatus:
    - test_admin_sync_status_returns_200_with_expected_shape
    - test_admin_sync_status_returns_501_when_catalog_unavailable
```

### Dependency override pattern

```python
# Correct pattern — scope="function" mandatory
@pytest.fixture(scope="function")
def admin_client():
    from backend.api.main import app
    from backend.api.dependencies import get_current_user, is_admin_user, promote_bootstrap_admin

    async def mock_admin_user(request: Request):
        return {"sub": "1", "email": "admin@example.com"}

    app.dependency_overrides[get_current_user] = mock_admin_user
    app.dependency_overrides[is_admin_user] = lambda email: True  # Not a FastAPI dep
    # is_admin_user is NOT a FastAPI dependency — it's called inside require_admin.
    # Must patch via unittest.mock.patch instead.
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

Because `is_admin_user` is a plain function (not a FastAPI `Depends`), it cannot be
overridden via `dependency_overrides`. The correct approach is to patch it at the call
site inside `dependencies.py` using `unittest.mock.patch`:

```python
@pytest.fixture(scope="function")
def admin_client():
    from backend.api.main import app
    from backend.api import dependencies

    async def mock_admin_user(request):
        return {"sub": "1", "email": "admin@example.com"}

    app.dependency_overrides[dependencies.get_current_user] = mock_admin_user
    with patch.object(dependencies, "is_admin_user", return_value=True), \
         patch.object(dependencies, "promote_bootstrap_admin"):
        with TestClient(app) as client:
            yield client
    app.dependency_overrides.clear()
```

### Rationale: Why not test the frontend?

Frontend components are already exercised by manual verification and the existing Admin
page code is straightforward (no complex logic beyond the WebSocket state machine). The
highest-value test surface is the backend HTTP boundary where access control bugs would
cause real security issues.

## Risks and Considerations

### Risk: `backend.api.main` import chain

Importing `backend.api.main` in tests pulls in all route modules, services, and core
packages. This can fail if environment variables (e.g., `DATABASE_URL`, `JWT_SECRET_KEY`)
are not set. The existing test suite handles this by using `@pytest.fixture` with mocked
dependencies; the new tests must follow the same pattern and not require a real database
connection.

Mitigation: The test file must set any required environment variables at module import
time using `os.environ` patching or a `conftest.py` fixture, following the established
pattern in the test suite.

### Risk: Thread leakage from start_sync

If `catalog_service.start_sync` is not mocked, the admin sync trigger test will start a
real background thread that tries to connect to a catalog repository and image store that
don't exist in the test environment, causing hangs or errors that surface after the test
returns.

Mitigation: Always patch `catalog_service.start_sync` in any test that calls
`POST /api/admin/catalog/sync`. The patch target is
`backend.api.routes.admin_routes.catalog_service.start_sync`.

### Risk: is_admin_user DB path

The real `is_admin_user` function first tries a DB query (via `get_engine()`). In tests,
`get_engine()` will return `None` if `DATABASE_URL` is not set, falling through to the
env var check. This is safe — the env var fallback is sufficient for tests. But to be
explicit, `is_admin_user` should be patched to avoid any DB calls in the test
environment.

### Risk: `promote_bootstrap_admin` side effects

`require_admin` calls `promote_bootstrap_admin(email)` after the admin check passes. This
function does a DB write. It must be patched to a no-op in tests to avoid DB errors.
