"""
End-to-end tests for the authentication flow.

Covers:
- JWT creation and validation (valid, expired, malformed)
- OAuth callback (mock Google, new user creation, existing user login)
- Auth code exchange (valid, expired, reused)
- Token refresh (new token issued, old JTI blacklisted)
- Logout (JTI blacklisted, cookie cleared)
- Get current user (/api/auth/me)
- Token blacklist enforcement
- Error cases (missing credentials, invalid tokens)
- Profile update (valid, invalid avatar URL, unauthenticated)

Uses unittest.TestCase with setUp/tearDown per class.
Mocks httpx.AsyncClient for all Google OAuth calls.
"""

import os
import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Env vars must be set before importing backend modules that read them at import time
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests")
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")

from fastapi.testclient import TestClient
from jose import jwt

import backend.api.dependencies as deps_module
import backend.api.routes.auth as auth_module
from backend.api.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

JWT_SECRET = "test-secret-key-for-unit-tests"
JWT_ALGORITHM = "HS256"


def _make_token(
    user_id: int = 1,
    email: str = "user@example.com",
    display_name: str = "Test User",
    jti: str | None = None,
    exp_delta: timedelta = timedelta(hours=1),
) -> str:
    """Create a JWT directly (bypasses create_jwt module-level env var check)."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "display_name": display_name,
        "jti": jti or str(uuid.uuid4()),
        "exp": datetime.utcnow() + exp_delta,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _make_expired_token(user_id: int = 1, email: str = "user@example.com") -> str:
    """Create an already-expired JWT."""
    return _make_token(user_id=user_id, email=email, exp_delta=timedelta(seconds=-10))


def _make_mock_httpx_token_response(access_token: str = "google-access-token") -> MagicMock:
    """Mock httpx response for Google token endpoint."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"access_token": access_token, "token_type": "Bearer"}
    return resp


def _make_mock_httpx_userinfo_response(
    sub: str = "google-123",
    email: str = "newuser@example.com",
    name: str = "New User",
    picture: str = "https://lh3.googleusercontent.com/photo.jpg",
) -> MagicMock:
    """Mock httpx response for Google userinfo endpoint."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "sub": sub,
        "email": email,
        "name": name,
        "picture": picture,
    }
    return resp


# ---------------------------------------------------------------------------
# JWT Unit Tests (no HTTP, pure logic)
# ---------------------------------------------------------------------------


class TestJwtCreation(unittest.TestCase):
    """Test JWT creation logic via the create_jwt function."""

    def setUp(self):
        # Ensure env var is set for the module
        self._orig_secret = os.environ.get("JWT_SECRET_KEY")
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        # Patch module-level var in auth module (read at import time)
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._secret_patcher.start()

    def tearDown(self):
        self._secret_patcher.stop()
        if self._orig_secret is not None:
            os.environ["JWT_SECRET_KEY"] = self._orig_secret
        else:
            os.environ.pop("JWT_SECRET_KEY", None)

    def test_create_jwt_returns_string(self):
        token = auth_module.create_jwt({"id": 1, "email": "a@b.com"})
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_create_jwt_payload_contains_expected_fields(self):
        token = auth_module.create_jwt({"id": 42, "email": "a@b.com", "display_name": "Alice"})
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["email"], "a@b.com")
        self.assertEqual(payload["display_name"], "Alice")
        self.assertIn("jti", payload)
        self.assertIn("exp", payload)

    def test_create_jwt_jti_is_unique(self):
        user = {"id": 1, "email": "a@b.com"}
        t1 = auth_module.create_jwt(user)
        t2 = auth_module.create_jwt(user)
        p1 = jwt.decode(t1, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        p2 = jwt.decode(t2, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        self.assertNotEqual(p1["jti"], p2["jti"])

    def test_create_jwt_raises_without_secret(self):
        with patch.object(auth_module, "JWT_SECRET_KEY", ""):
            with self.assertRaises(ValueError):
                auth_module.create_jwt({"id": 1, "email": "a@b.com"})


class TestJwtDecoding(unittest.TestCase):
    """Test JWT decoding via decode_jwt and decode_jwt_token."""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._secret_patcher.start()
        # Clear blacklist before each test
        deps_module._token_blacklist.clear()

    def tearDown(self):
        self._secret_patcher.stop()
        deps_module._token_blacklist.clear()

    def test_decode_jwt_valid_token(self):
        token = _make_token(user_id=5, email="b@c.com")
        payload = auth_module.decode_jwt(token)
        self.assertEqual(payload["sub"], "5")
        self.assertEqual(payload["email"], "b@c.com")

    def test_decode_jwt_raises_on_expired_token(self):
        from jose import JWTError
        token = _make_expired_token()
        with self.assertRaises(JWTError):
            auth_module.decode_jwt(token)

    def test_decode_jwt_raises_on_malformed_token(self):
        from jose import JWTError
        with self.assertRaises((JWTError, Exception)):
            auth_module.decode_jwt("not.a.valid.jwt")

    def test_decode_jwt_token_checks_blacklist(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        # Blacklist the JTI
        deps_module.blacklist_token(jti, datetime.utcnow() + timedelta(hours=1))
        with self.assertRaises(ValueError):
            deps_module.decode_jwt_token(token)

    def test_decode_jwt_token_valid_not_blacklisted(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti, email="c@d.com")
        payload = deps_module.decode_jwt_token(token)
        self.assertEqual(payload["email"], "c@d.com")


# ---------------------------------------------------------------------------
# Token Blacklist Tests
# ---------------------------------------------------------------------------


class TestTokenBlacklist(unittest.TestCase):
    """Test blacklist_token and is_token_blacklisted in dependencies."""

    def setUp(self):
        deps_module._token_blacklist.clear()

    def tearDown(self):
        deps_module._token_blacklist.clear()

    def test_fresh_jti_is_not_blacklisted(self):
        jti = str(uuid.uuid4())
        self.assertFalse(deps_module.is_token_blacklisted(jti))

    def test_blacklisted_jti_is_detected(self):
        jti = str(uuid.uuid4())
        deps_module.blacklist_token(jti, datetime.utcnow() + timedelta(hours=1))
        self.assertTrue(deps_module.is_token_blacklisted(jti))

    def test_blacklist_multiple_tokens(self):
        jtis = [str(uuid.uuid4()) for _ in range(5)]
        for jti in jtis:
            deps_module.blacklist_token(jti, datetime.utcnow() + timedelta(hours=1))
        for jti in jtis:
            self.assertTrue(deps_module.is_token_blacklisted(jti))


# ---------------------------------------------------------------------------
# Auth Code Exchange Tests
# ---------------------------------------------------------------------------


class TestAuthCodeExchange(unittest.TestCase):
    """Test the /api/auth/exchange endpoint."""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._secret_patcher.start()
        # Clear auth codes and blacklist
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()
        self.client = TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        self._secret_patcher.stop()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()

    def test_exchange_valid_code_returns_200_and_sets_cookie(self):
        token = _make_token()
        code = str(uuid.uuid4())
        auth_module._auth_codes[code] = {
            "jwt": token,
            "expires": datetime.utcnow() + timedelta(minutes=5),
        }
        resp = self.client.get(f"/api/auth/exchange?code={code}", follow_redirects=False)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", resp.cookies)

    def test_exchange_removes_code_after_use(self):
        token = _make_token()
        code = str(uuid.uuid4())
        auth_module._auth_codes[code] = {
            "jwt": token,
            "expires": datetime.utcnow() + timedelta(minutes=5),
        }
        self.client.get(f"/api/auth/exchange?code={code}")
        self.assertNotIn(code, auth_module._auth_codes)

    def test_exchange_reused_code_returns_400(self):
        token = _make_token()
        code = str(uuid.uuid4())
        auth_module._auth_codes[code] = {
            "jwt": token,
            "expires": datetime.utcnow() + timedelta(minutes=5),
        }
        self.client.get(f"/api/auth/exchange?code={code}")
        resp = self.client.get(f"/api/auth/exchange?code={code}")
        self.assertEqual(resp.status_code, 400)

    def test_exchange_expired_code_returns_400(self):
        token = _make_token()
        code = str(uuid.uuid4())
        auth_module._auth_codes[code] = {
            "jwt": token,
            "expires": datetime.utcnow() - timedelta(minutes=1),  # already expired
        }
        resp = self.client.get(f"/api/auth/exchange?code={code}")
        self.assertEqual(resp.status_code, 400)

    def test_exchange_unknown_code_returns_400(self):
        resp = self.client.get("/api/auth/exchange?code=nonexistent-code")
        self.assertEqual(resp.status_code, 400)

    def test_exchange_response_body_has_ok(self):
        token = _make_token()
        code = str(uuid.uuid4())
        auth_module._auth_codes[code] = {
            "jwt": token,
            "expires": datetime.utcnow() + timedelta(minutes=5),
        }
        resp = self.client.get(f"/api/auth/exchange?code={code}")
        self.assertEqual(resp.json(), {"ok": True})


# ---------------------------------------------------------------------------
# Token Refresh Tests
# ---------------------------------------------------------------------------


class TestTokenRefresh(unittest.TestCase):
    """Test the /api/auth/refresh endpoint."""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._secret_patcher.start()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()
        self.client = TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        self._secret_patcher.stop()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()

    def test_refresh_with_valid_cookie_returns_200(self):
        token = _make_token()
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/refresh")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})

    def test_refresh_blacklists_old_jti(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        self.client.cookies.set("access_token", token)
        self.client.post("/api/auth/refresh")
        self.assertTrue(deps_module.is_token_blacklisted(jti))

    def test_refresh_sets_new_cookie(self):
        token = _make_token()
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/refresh")
        self.assertIn("access_token", resp.cookies)

    def test_refresh_new_token_has_different_jti(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/refresh")
        new_token = resp.cookies.get("access_token")
        if new_token:
            new_payload = jwt.decode(new_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            self.assertNotEqual(new_payload["jti"], jti)

    def test_refresh_with_bearer_token_returns_200(self):
        token = _make_token()
        self.client.cookies.clear()
        resp = self.client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)

    def test_refresh_without_token_returns_401(self):
        self.client.cookies.clear()
        resp = self.client.post("/api/auth/refresh")
        self.assertEqual(resp.status_code, 401)

    def test_refresh_with_expired_token_returns_401(self):
        token = _make_expired_token()
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/refresh")
        self.assertEqual(resp.status_code, 401)

    def test_refresh_with_blacklisted_token_returns_401(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        deps_module.blacklist_token(jti, datetime.utcnow() + timedelta(hours=1))
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/refresh")
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Logout Tests
# ---------------------------------------------------------------------------


class TestLogout(unittest.TestCase):
    """Test the /api/auth/logout endpoint."""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._secret_patcher.start()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()
        self.client = TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        self._secret_patcher.stop()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()

    def test_logout_returns_200(self):
        token = _make_token()
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/logout")
        self.assertEqual(resp.status_code, 200)

    def test_logout_response_has_message(self):
        token = _make_token()
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/logout")
        data = resp.json()
        self.assertIn("message", data)

    def test_logout_blacklists_token_jti(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        self.client.cookies.set("access_token", token)
        self.client.post("/api/auth/logout")
        self.assertTrue(deps_module.is_token_blacklisted(jti))

    def test_logout_without_token_returns_200(self):
        """Logout should succeed even if no token is present."""
        self.client.cookies.clear()
        resp = self.client.post("/api/auth/logout")
        self.assertEqual(resp.status_code, 200)

    def test_logout_with_bearer_token_blacklists_jti(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        self.client.cookies.clear()
        resp = self.client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(deps_module.is_token_blacklisted(jti))

    def test_logout_with_expired_token_still_returns_200(self):
        """Expired token on logout should not cause server error."""
        token = _make_expired_token()
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/logout")
        self.assertEqual(resp.status_code, 200)

    def test_token_rejected_after_logout(self):
        """After logout, the blacklisted JTI should cause 401 on protected endpoints."""
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        deps_module.blacklist_token(jti, datetime.utcnow() + timedelta(hours=1))
        # Attempting refresh with a blacklisted token must fail
        self.client.cookies.set("access_token", token)
        resp = self.client.post("/api/auth/refresh")
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Auth Health Endpoint
# ---------------------------------------------------------------------------


class TestAuthHealth(unittest.TestCase):
    """Test /api/auth/health endpoint."""

    def setUp(self):
        self.client = TestClient(app)

    def test_auth_health_returns_200(self):
        resp = self.client.get("/api/auth/health")
        self.assertEqual(resp.status_code, 200)

    def test_auth_health_has_status_ok(self):
        resp = self.client.get("/api/auth/health")
        self.assertEqual(resp.json(), {"status": "ok"})


# ---------------------------------------------------------------------------
# Google OAuth Callback Tests
# ---------------------------------------------------------------------------


class TestOAuthCallback(unittest.TestCase):
    """Test /api/auth/callback with mocked Google HTTP calls."""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        os.environ["GOOGLE_OAUTH_CLIENT_ID"] = "test-client-id"
        os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "test-client-secret"
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._client_id_patcher = patch.object(auth_module, "GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        self._client_secret_patcher = patch.object(auth_module, "GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")
        self._secret_patcher.start()
        self._client_id_patcher.start()
        self._client_secret_patcher.start()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        self._secret_patcher.stop()
        self._client_id_patcher.stop()
        self._client_secret_patcher.stop()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()

    def _make_mock_repo(self, existing_user=None, created_user=None):
        """Build a mock repo for OAuth callback tests."""
        mock_repo = MagicMock()
        mock_repo.get_user_by_google_id.return_value = existing_user
        mock_repo.get_user_by_email.return_value = None
        mock_repo.create_user.return_value = created_user or {
            "id": 99,
            "email": "newuser@example.com",
            "display_name": "New User",
            "avatar_url": "https://lh3.googleusercontent.com/photo.jpg",
            "google_id": "google-123",
        }
        mock_repo.update_user_last_login.return_value = None
        return mock_repo

    def _make_async_client_mock(self, token_resp, userinfo_resp):
        """Build an AsyncMock for httpx.AsyncClient used in the callback."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=token_resp)
        mock_client.get = AsyncMock(return_value=userinfo_resp)
        return mock_client

    def test_callback_with_error_param_redirects_to_login_error(self):
        resp = self.client.get("/api/auth/callback?error=access_denied", follow_redirects=False)
        self.assertEqual(resp.status_code, 307)
        self.assertIn("error=auth_failed", resp.headers["location"])

    def test_callback_without_code_redirects_to_login_error(self):
        resp = self.client.get("/api/auth/callback", follow_redirects=False)
        self.assertEqual(resp.status_code, 307)
        self.assertIn("error=auth_failed", resp.headers["location"])

    def test_callback_creates_auth_code_for_new_user(self):
        token_resp = _make_mock_httpx_token_response()
        userinfo_resp = _make_mock_httpx_userinfo_response(
            sub="google-new-456",
            email="brand_new@example.com",
        )

        mock_client = self._make_async_client_mock(token_resp, userinfo_resp)
        mock_repo = self._make_mock_repo(
            existing_user=None,
            created_user={
                "id": 100,
                "email": "brand_new@example.com",
                "display_name": "Brand New",
                "avatar_url": None,
                "google_id": "google-new-456",
            },
        )

        with (
            patch("backend.api.routes.auth.httpx.AsyncClient", return_value=mock_client),
            patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo),
        ):
            resp = self.client.get(
                "/api/auth/callback?code=google-oauth-code", follow_redirects=False
            )

        self.assertEqual(resp.status_code, 307)
        location = resp.headers["location"]
        self.assertIn("/auth/callback?code=", location)
        # Verify auth code was stored (then popped by redirect, so check it was set)
        self.assertNotIn("error=auth_failed", location)

    def test_callback_logs_in_existing_user(self):
        existing_user = {
            "id": 7,
            "email": "existing@example.com",
            "display_name": "Existing",
            "avatar_url": None,
            "google_id": "google-existing-789",
        }
        token_resp = _make_mock_httpx_token_response()
        userinfo_resp = _make_mock_httpx_userinfo_response(
            sub="google-existing-789",
            email="existing@example.com",
        )
        mock_client = self._make_async_client_mock(token_resp, userinfo_resp)
        mock_repo = self._make_mock_repo(existing_user=existing_user)

        with (
            patch("backend.api.routes.auth.httpx.AsyncClient", return_value=mock_client),
            patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo),
        ):
            resp = self.client.get(
                "/api/auth/callback?code=google-oauth-code", follow_redirects=False
            )

        self.assertEqual(resp.status_code, 307)
        location = resp.headers["location"]
        self.assertIn("/auth/callback?code=", location)
        self.assertNotIn("error", location)

    def test_callback_without_credentials_configured_redirects_to_error(self):
        with (
            patch.object(auth_module, "GOOGLE_OAUTH_CLIENT_ID", ""),
            patch.object(auth_module, "GOOGLE_OAUTH_CLIENT_SECRET", ""),
        ):
            resp = self.client.get(
                "/api/auth/callback?code=google-oauth-code", follow_redirects=False
            )
        self.assertEqual(resp.status_code, 307)
        self.assertIn("error=auth_failed", resp.headers["location"])

    def test_callback_without_repo_redirects_to_error(self):
        token_resp = _make_mock_httpx_token_response()
        userinfo_resp = _make_mock_httpx_userinfo_response()
        mock_client = self._make_async_client_mock(token_resp, userinfo_resp)

        with (
            patch("backend.api.routes.auth.httpx.AsyncClient", return_value=mock_client),
            patch("backend.api.routes.auth.get_collection_repo", return_value=None),
        ):
            resp = self.client.get(
                "/api/auth/callback?code=google-oauth-code", follow_redirects=False
            )

        self.assertEqual(resp.status_code, 307)
        self.assertIn("error=auth_failed", resp.headers["location"])


# ---------------------------------------------------------------------------
# Google Login Redirect Tests
# ---------------------------------------------------------------------------


class TestGoogleLogin(unittest.TestCase):
    """Test /api/auth/google redirect endpoint."""

    def setUp(self):
        self._client_id_patcher = patch.object(auth_module, "GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        self._client_id_patcher.start()
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        self._client_id_patcher.stop()

    def test_google_login_redirects_to_google(self):
        resp = self.client.get("/api/auth/google", follow_redirects=False)
        self.assertEqual(resp.status_code, 307)
        self.assertIn("accounts.google.com", resp.headers["location"])

    def test_google_login_redirect_contains_client_id(self):
        resp = self.client.get("/api/auth/google", follow_redirects=False)
        self.assertIn("test-client-id", resp.headers["location"])

    def test_google_login_without_client_id_returns_500(self):
        with patch.object(auth_module, "GOOGLE_OAUTH_CLIENT_ID", ""):
            resp = self.client.get("/api/auth/google", follow_redirects=False)
        self.assertEqual(resp.status_code, 500)


# ---------------------------------------------------------------------------
# Get Current User Tests (/api/auth/me)
# ---------------------------------------------------------------------------


class TestGetCurrentUser(unittest.TestCase):
    """Test /api/auth/me endpoint."""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._secret_patcher.start()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()
        self.client = TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        self._secret_patcher.stop()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()

    def _make_mock_repo_with_user(self, user_row: dict):
        """Build a mock repo whose engine returns a user row for /me."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)

        mock_result = MagicMock()
        mock_result.mappings.return_value.fetchone.return_value = user_row

        mock_conn.execute.return_value = mock_result

        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn

        mock_repo = MagicMock()
        mock_repo._get_engine.return_value = mock_engine

        return mock_repo

    def test_me_without_token_returns_401(self):
        self.client.cookies.clear()
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)

    def test_me_with_valid_token_returns_user(self):
        token = _make_token(user_id=3, email="me@example.com", display_name="Me")
        user_row = {
            "id": 3,
            "email": "me@example.com",
            "display_name": "Me",
            "avatar_url": None,
            "is_admin": False,
        }
        mock_repo = self._make_mock_repo_with_user(user_row)

        self.client.cookies.set("access_token", token)
        with (
            patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo),
            patch("backend.api.routes.auth.is_admin_user", return_value=False),
        ):
            resp = self.client.get("/api/auth/me")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["email"], "me@example.com")
        self.assertEqual(data["display_name"], "Me")
        self.assertFalse(data["is_admin"])

    def test_me_with_expired_token_returns_401(self):
        token = _make_expired_token()
        self.client.cookies.set("access_token", token)
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)

    def test_me_with_blacklisted_token_returns_401(self):
        jti = str(uuid.uuid4())
        token = _make_token(jti=jti)
        deps_module.blacklist_token(jti, datetime.utcnow() + timedelta(hours=1))
        self.client.cookies.set("access_token", token)
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)

    def test_me_with_malformed_token_returns_401(self):
        self.client.cookies.set("access_token", "totally.wrong.token")
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)

    def test_me_with_bearer_token_returns_user(self):
        token = _make_token(user_id=5, email="bearer@example.com")
        user_row = {
            "id": 5,
            "email": "bearer@example.com",
            "display_name": None,
            "avatar_url": None,
            "is_admin": False,
        }
        mock_repo = self._make_mock_repo_with_user(user_row)

        self.client.cookies.clear()
        with (
            patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo),
            patch("backend.api.routes.auth.is_admin_user", return_value=False),
        ):
            resp = self.client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "bearer@example.com")


# ---------------------------------------------------------------------------
# Profile Update Tests
# ---------------------------------------------------------------------------


class TestProfileUpdate(unittest.TestCase):
    """Test /api/auth/profile PATCH endpoint."""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET
        self._secret_patcher = patch.object(auth_module, "JWT_SECRET_KEY", JWT_SECRET)
        self._secret_patcher.start()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()
        self.client = TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        self._secret_patcher.stop()
        auth_module._auth_codes.clear()
        deps_module._token_blacklist.clear()

    def _make_profile_mock_repo(self, updated_user: dict):
        mock_repo = MagicMock()
        mock_repo.update_user_profile.return_value = updated_user
        return mock_repo

    def test_profile_update_without_token_returns_401(self):
        self.client.cookies.clear()
        resp = self.client.patch("/api/auth/profile", json={"display_name": "New Name"})
        self.assertEqual(resp.status_code, 401)

    def test_profile_update_display_name_succeeds(self):
        token = _make_token(user_id=10, email="user10@example.com")
        updated = {
            "id": 10,
            "email": "user10@example.com",
            "display_name": "Updated Name",
            "avatar_url": None,
            "is_admin": False,
        }
        mock_repo = self._make_profile_mock_repo(updated)

        self.client.cookies.set("access_token", token)
        with patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo):
            resp = self.client.patch("/api/auth/profile", json={"display_name": "Updated Name"})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["display_name"], "Updated Name")

    def test_profile_update_invalid_avatar_url_http_returns_400(self):
        token = _make_token(user_id=10, email="user10@example.com")
        self.client.cookies.set("access_token", token)
        resp = self.client.patch(
            "/api/auth/profile",
            json={"avatar_url": "http://lh3.googleusercontent.com/photo.jpg"},  # http not https
        )
        self.assertEqual(resp.status_code, 400)

    def test_profile_update_disallowed_avatar_domain_returns_400(self):
        token = _make_token(user_id=10, email="user10@example.com")
        self.client.cookies.set("access_token", token)
        resp = self.client.patch(
            "/api/auth/profile",
            json={"avatar_url": "https://evil.com/photo.jpg"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_profile_update_valid_google_avatar_url_succeeds(self):
        token = _make_token(user_id=10, email="user10@example.com")
        avatar = "https://lh3.googleusercontent.com/photo.jpg"
        updated = {
            "id": 10,
            "email": "user10@example.com",
            "display_name": None,
            "avatar_url": avatar,
            "is_admin": False,
        }
        mock_repo = self._make_profile_mock_repo(updated)

        self.client.cookies.set("access_token", token)
        with patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo):
            resp = self.client.patch("/api/auth/profile", json={"avatar_url": avatar})

        self.assertEqual(resp.status_code, 200)

    def test_profile_update_without_repo_returns_500(self):
        token = _make_token(user_id=10, email="user10@example.com")
        self.client.cookies.set("access_token", token)
        with patch("backend.api.routes.auth.get_collection_repo", return_value=None):
            resp = self.client.patch("/api/auth/profile", json={"display_name": "X"})
        self.assertEqual(resp.status_code, 500)

    def test_profile_update_user_not_found_returns_404(self):
        token = _make_token(user_id=99, email="ghost@example.com")
        mock_repo = self._make_profile_mock_repo(updated_user=None)

        self.client.cookies.set("access_token", token)
        with patch("backend.api.routes.auth.get_collection_repo", return_value=mock_repo):
            resp = self.client.patch("/api/auth/profile", json={"display_name": "Ghost"})

        self.assertEqual(resp.status_code, 404)
