# Tasks: Admin Backoffice Dashboard — Test Coverage Gap

## Overview

The backend, frontend, and API client for the admin backoffice are fully implemented.
The only remaining work is adding HTTP-level integration tests for admin endpoint access
control and the sync trigger. All tasks below are in the Tests layer.

---

## Layer: Tests

### Task T-1: Create `tests/test_admin_routes.py` with fixture infrastructure

**File**: `tests/test_admin_routes.py` (new file)

**Description**:
Create the test module and define the three core pytest fixtures needed by all test
classes. These fixtures set up `TestClient` instances with different authentication
states by overriding FastAPI dependencies and patching plain functions.

All fixtures MUST use `scope="function"` to prevent cross-test pollution via
`app.dependency_overrides`.

Fixture definitions:

1. `app_client` — returns a `TestClient` with no overrides (unauthenticated state; the
   real `get_current_user` will raise 401 because no JWT cookie is present).

2. `non_admin_client` — overrides `backend.api.dependencies.get_current_user` to return
   `{"sub": "2", "email": "user@example.com"}`, and patches
   `backend.api.dependencies.is_admin_user` to return `False`. Clears overrides after
   the test.

3. `admin_client` — overrides `backend.api.dependencies.get_current_user` to return
   `{"sub": "1", "email": "admin@example.com"}`, patches
   `backend.api.dependencies.is_admin_user` to return `True`, and patches
   `backend.api.dependencies.promote_bootstrap_admin` to a no-op. Clears overrides
   after the test.

Import pattern for `get_current_user` override:
```python
from backend.api import dependencies as deps

async def _mock_admin_user(request):
    return {"sub": "1", "email": "admin@example.com"}

app.dependency_overrides[deps.get_current_user] = _mock_admin_user
```

Cleanup in all fixtures: call `app.dependency_overrides.clear()` in a `finally` block
or yield-based teardown to avoid state leakage between tests.

**Acceptance criteria**:
- Module imports without errors when run with `pytest --collect-only tests/test_admin_routes.py`
- All three fixtures are collected and yield valid `TestClient` instances
- No `scope="module"` or `scope="class"` used anywhere in this file

**Dependencies**: None (first task)

---

### Task T-2: Add access control tests — unauthenticated (401)

**File**: `tests/test_admin_routes.py`

**Description**:
Add `TestAdminCatalogSyncAccessControl` test class with two test methods covering the
unauthenticated case. Use the `app_client` fixture (no JWT present).

```
test_unauthenticated_sync_trigger_returns_401:
  POST /api/admin/catalog/sync → expect 401

test_unauthenticated_sync_status_returns_401:
  GET /api/admin/catalog/sync/status → expect 401
```

For the unauthenticated fixture, no JWT cookie is set on the `TestClient`, so the real
`get_current_user` dependency will raise 401 as expected. Do NOT mock `get_current_user`
for this fixture.

**Acceptance criteria**:
- Both tests pass with `pytest tests/test_admin_routes.py::TestAdminCatalogSyncAccessControl`
- Response status is 401 for both endpoints when no auth is provided

**Dependencies**: T-1

---

### Task T-3: Add access control tests — non-admin (403)

**File**: `tests/test_admin_routes.py`

**Description**:
Add two test methods to `TestAdminCatalogSyncAccessControl` covering the non-admin case.
Use the `non_admin_client` fixture.

```
test_non_admin_sync_trigger_returns_403:
  POST /api/admin/catalog/sync → expect 403
  Response body must contain {"detail": "Admin access required"}

test_non_admin_sync_status_returns_403:
  GET /api/admin/catalog/sync/status → expect 403
  Response body must contain {"detail": "Admin access required"}
```

**Acceptance criteria**:
- Both tests pass
- `response.json()["detail"]` equals `"Admin access required"` in both cases

**Dependencies**: T-1

---

### Task T-4: Add sync trigger integration tests — happy path and error cases

**File**: `tests/test_admin_routes.py`

**Description**:
Add `TestAdminSyncTrigger` test class with three test methods using the `admin_client`
fixture. All tests must patch `catalog_service.start_sync` at its call site to avoid
spawning real background threads.

The correct patch target is:
`backend.api.routes.admin_routes.catalog_service.start_sync`

```
test_admin_sync_trigger_returns_200_with_job_id:
  - Patch start_sync to return "test-job-id-1234"
  - Also patch _get_catalog_repo_or_501 to return a MagicMock (or patch get_catalog_repo
    to return a non-None MagicMock so the 501 check passes)
  - POST /api/admin/catalog/sync → expect 200
  - response.json() must have keys: "job_id", "status", "message"
  - response.json()["status"] == "started"
  - response.json()["message"] == "Catalog sync started"
  - response.json()["job_id"] == "test-job-id-1234"

test_admin_sync_trigger_returns_409_when_already_running:
  - Patch start_sync to raise RuntimeError("A catalog sync is already running")
  - Also patch catalog repo to return a non-None value
  - POST /api/admin/catalog/sync → expect 409
  - response.json()["detail"] == "Catalog sync already in progress"

test_admin_sync_trigger_returns_501_when_catalog_unavailable:
  - Patch get_catalog_repo (in admin_routes module) to return None
  - POST /api/admin/catalog/sync → expect 501
  - response.json()["detail"] == "Catalog system not available"
```

For the 501 test, the cleanest patch target is:
`backend.api.routes.admin_routes.get_catalog_repo`

Note: `get_job_repo` and `get_image_store` are also called in the trigger route.
Patch them to return `MagicMock()` / `None` respectively so they don't fail.
`get_job_repo` returning `None` is safe (catalog_service.start_sync guards it).
`get_image_store` should return a `MagicMock()`.

**Acceptance criteria**:
- All three tests pass
- No real threads are spawned during any of these tests (verified by start_sync being mocked)
- No DB connections are attempted

**Dependencies**: T-1, T-2, T-3 (for file structure; logically independent)

---

### Task T-5: Add sync status integration tests

**File**: `tests/test_admin_routes.py`

**Description**:
Add `TestAdminSyncStatus` test class with two test methods using the `admin_client`
fixture.

```
test_admin_sync_status_returns_200_with_expected_shape:
  - Patch get_catalog_repo (in admin_routes module) to return a MagicMock whose
    get_sync_state() method returns:
    {
      "last_bulk_sync": None,
      "total_cards": 0,
      "total_images_downloaded": 0,
      "status": "idle",
      "error_message": None
    }
  - GET /api/admin/catalog/sync/status → expect 200
  - Verify response.json() contains all five keys: last_bulk_sync, total_cards,
    total_images_downloaded, status, error_message

test_admin_sync_status_returns_501_when_catalog_unavailable:
  - Patch get_catalog_repo (in admin_routes module) to return None
  - GET /api/admin/catalog/sync/status → expect 501
  - response.json()["detail"] == "Catalog system not available"
```

**Acceptance criteria**:
- Both tests pass
- The 200 test verifies the complete response shape (all five fields present)
- The 501 test verifies the error detail string

**Dependencies**: T-1

---

### Task T-6: Verify full test suite passes

**Description**:
Run the complete test suite to confirm no regressions were introduced.

```bash
pytest tests/
```

Confirm:
- All existing tests pass (no regressions)
- All new tests in `tests/test_admin_routes.py` pass
- No `scope="module"` warnings or fixture pollution errors

**Acceptance criteria**:
- `pytest tests/` exits with code 0
- `tests/test_admin_routes.py` contributes at least 9 passing tests

**Dependencies**: T-1, T-2, T-3, T-4, T-5
