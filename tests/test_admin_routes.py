"""Integration tests for admin API routes (backend/api/routes/admin_routes.py).

Tests all endpoints via FastAPI TestClient:
- POST /api/admin/catalog/sync
- GET  /api/admin/catalog/sync/status

Access-control matrix:
- Unauthenticated → 401
- Authenticated non-admin → 403
- Authenticated admin → route-specific responses

Patches:
- get_current_user via app.dependency_overrides (FastAPI DI)
- is_admin_user via patch.object on the dependencies module (plain function)
- promote_bootstrap_admin via patch.object (plain function with DB side effects)
- catalog_service.start_sync at the call site in admin_routes
- get_catalog_repo at the call site in admin_routes (for 501 cases)
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from backend.api import dependencies as deps
from backend.api.main import app

# ---------------------------------------------------------------------------
# Fixtures — all scope="function" to prevent cross-test pollution
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def app_client():
    """TestClient with no dependency overrides (unauthenticated state).

    The real get_current_user will raise 401 because no JWT cookie is present.
    """
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    # No overrides were added — nothing to clean up.


@pytest.fixture(scope="function")
def non_admin_client():
    """TestClient with get_current_user overridden to return a non-admin user.

    is_admin_user is patched to return False so require_admin raises 403.
    """

    async def _mock_non_admin_user(request: Request):
        return {"sub": "2", "email": "user@example.com"}

    app.dependency_overrides[deps.get_current_user] = _mock_non_admin_user

    with patch.object(deps, "is_admin_user", return_value=False):
        client = TestClient(app, raise_server_exceptions=False)
        yield client

    # Remove only the overrides this fixture added — do NOT call .clear()
    # which would destroy overrides set by other test modules at module level.
    app.dependency_overrides.pop(deps.get_current_user, None)


@pytest.fixture(scope="function")
def admin_client():
    """TestClient with get_current_user overridden to return an admin user.

    is_admin_user is patched to return True; promote_bootstrap_admin is a no-op.
    """

    async def _mock_admin_user(request: Request):
        return {"sub": "1", "email": "admin@example.com"}

    app.dependency_overrides[deps.get_current_user] = _mock_admin_user

    with (
        patch.object(deps, "is_admin_user", return_value=True),
        patch.object(deps, "promote_bootstrap_admin"),
    ):
        client = TestClient(app, raise_server_exceptions=False)
        yield client

    # Remove only the overrides this fixture added — do NOT call .clear()
    # which would destroy overrides set by other test modules at module level.
    app.dependency_overrides.pop(deps.get_current_user, None)


# ---------------------------------------------------------------------------
# TestAdminCatalogSyncAccessControl — 401 and 403 cases
# ---------------------------------------------------------------------------


class TestAdminCatalogSyncAccessControl:
    """Verify that admin endpoints enforce authentication and admin-role checks."""

    def test_unauthenticated_sync_trigger_returns_401(self, app_client):
        """POST /api/admin/catalog/sync returns 401 with no JWT present."""
        response = app_client.post("/api/admin/catalog/sync")

        assert response.status_code == 401

    def test_unauthenticated_sync_status_returns_401(self, app_client):
        """GET /api/admin/catalog/sync/status returns 401 with no JWT present."""
        response = app_client.get("/api/admin/catalog/sync/status")

        assert response.status_code == 401

    def test_non_admin_sync_trigger_returns_403(self, non_admin_client):
        """POST /api/admin/catalog/sync returns 403 for authenticated non-admin user."""
        response = non_admin_client.post("/api/admin/catalog/sync")

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"

    def test_non_admin_sync_status_returns_403(self, non_admin_client):
        """GET /api/admin/catalog/sync/status returns 403 for authenticated non-admin user."""
        response = non_admin_client.get("/api/admin/catalog/sync/status")

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"


# ---------------------------------------------------------------------------
# TestAdminSyncTrigger — happy path and error cases
# ---------------------------------------------------------------------------


class TestAdminSyncTrigger:
    """Verify POST /api/admin/catalog/sync behaviour for admin users."""

    def test_admin_sync_trigger_returns_200_with_job_id(self, admin_client):
        """Admin sync trigger returns 200 with job_id, status, and message."""
        mock_catalog_repo = MagicMock()

        with (
            patch("backend.api.routes.admin_routes.get_catalog_repo", return_value=mock_catalog_repo),
            patch("backend.api.routes.admin_routes.get_image_store", return_value=MagicMock()),
            patch("backend.api.routes.admin_routes.get_job_repo", return_value=None),
            patch(
                "backend.api.routes.admin_routes.catalog_service.start_sync",
                return_value="test-job-id-1234",
            ),
        ):
            response = admin_client.post("/api/admin/catalog/sync")

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] == "started"
        assert data["message"] == "Catalog sync started"
        assert data["job_id"] == "test-job-id-1234"

    def test_admin_sync_trigger_returns_409_when_already_running(self, admin_client):
        """Admin sync trigger returns 409 when a sync is already in progress."""
        mock_catalog_repo = MagicMock()

        with (
            patch("backend.api.routes.admin_routes.get_catalog_repo", return_value=mock_catalog_repo),
            patch("backend.api.routes.admin_routes.get_image_store", return_value=MagicMock()),
            patch("backend.api.routes.admin_routes.get_job_repo", return_value=None),
            patch(
                "backend.api.routes.admin_routes.catalog_service.start_sync",
                side_effect=RuntimeError("A catalog sync is already running"),
            ),
        ):
            response = admin_client.post("/api/admin/catalog/sync")

        assert response.status_code == 409
        assert response.json()["detail"] == "Catalog sync already in progress"

    def test_admin_sync_trigger_returns_501_when_catalog_unavailable(self, admin_client):
        """Admin sync trigger returns 501 when catalog system is unavailable."""
        with patch("backend.api.routes.admin_routes.get_catalog_repo", return_value=None):
            response = admin_client.post("/api/admin/catalog/sync")

        assert response.status_code == 501
        assert response.json()["detail"] == "Catalog system not available"


# ---------------------------------------------------------------------------
# TestAdminSyncStatus — GET /api/admin/catalog/sync/status
# ---------------------------------------------------------------------------


class TestAdminSyncStatus:
    """Verify GET /api/admin/catalog/sync/status behaviour for admin users."""

    def test_admin_sync_status_returns_200_with_expected_shape(self, admin_client):
        """Admin sync status returns 200 with the full catalog sync state shape."""
        mock_catalog_repo = MagicMock()
        mock_catalog_repo.get_sync_state.return_value = {
            "last_bulk_sync": None,
            "total_cards": 0,
            "total_images_downloaded": 0,
            "status": "idle",
            "error_message": None,
        }

        with patch("backend.api.routes.admin_routes.get_catalog_repo", return_value=mock_catalog_repo):
            response = admin_client.get("/api/admin/catalog/sync/status")

        assert response.status_code == 200
        data = response.json()
        assert "last_bulk_sync" in data
        assert "total_cards" in data
        assert "total_images_downloaded" in data
        assert "status" in data
        assert "error_message" in data

    def test_admin_sync_status_returns_501_when_catalog_unavailable(self, admin_client):
        """Admin sync status returns 501 when catalog system is unavailable."""
        with patch("backend.api.routes.admin_routes.get_catalog_repo", return_value=None):
            response = admin_client.get("/api/admin/catalog/sync/status")

        assert response.status_code == 501
        assert response.json()["detail"] == "Catalog system not available"
