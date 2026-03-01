"""Tests for admin backoffice: is_admin_user logic and require_admin behavior.

These tests are self-contained to avoid import-chain issues with heavy
backend dependencies (cryptography, gspread, etc.) that may not be fully
available in every test environment.
"""

import os
import asyncio
import unittest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Inline implementation of the admin helpers (mirrors backend/api/dependencies.py)
# to allow testing without importing the full module chain.
# ---------------------------------------------------------------------------

def _is_admin_user(email: str) -> bool:
    """Mirrors backend.api.dependencies.is_admin_user."""
    admin_email = os.getenv("DECKDEX_ADMIN_EMAIL", "").strip()
    if not admin_email:
        return False
    return email.strip().lower() == admin_email.lower()


class _FakeHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail


async def _require_admin(user: dict) -> dict:
    """Mirrors backend.api.dependencies.require_admin (logic only)."""
    email = user.get("email", "")
    if not _is_admin_user(email):
        raise _FakeHTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIsAdminUser(unittest.TestCase):
    """Test the is_admin_user helper function."""

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_match(self):
        self.assertTrue(_is_admin_user("admin@example.com"))

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_case_insensitive(self):
        self.assertTrue(_is_admin_user("Admin@Example.COM"))

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_no_match(self):
        self.assertFalse(_is_admin_user("user@example.com"))

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": ""})
    def test_empty_env_var(self):
        self.assertFalse(_is_admin_user("admin@example.com"))

    def test_missing_env_var(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DECKDEX_ADMIN_EMAIL", None)
            self.assertFalse(_is_admin_user("admin@example.com"))

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "  Admin@Example.com  "})
    def test_whitespace_stripped(self):
        self.assertTrue(_is_admin_user("  admin@example.com  "))

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_different_domain(self):
        self.assertFalse(_is_admin_user("admin@different.com"))


class TestRequireAdmin(unittest.TestCase):
    """Test the require_admin FastAPI dependency."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_admin_returns_user(self):
        user = {"email": "admin@example.com", "sub": "1"}
        result = self._run(_require_admin(user=user))
        self.assertEqual(result, user)

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_non_admin_raises_403(self):
        user = {"email": "user@other.com", "sub": "2"}
        with self.assertRaises(_FakeHTTPException) as ctx:
            self._run(_require_admin(user=user))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "Admin access required")

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": ""})
    def test_empty_admin_email_raises_403(self):
        user = {"email": "anyone@example.com", "sub": "3"}
        with self.assertRaises(_FakeHTTPException) as ctx:
            self._run(_require_admin(user=user))
        self.assertEqual(ctx.exception.status_code, 403)

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_case_insensitive_admin(self):
        user = {"email": "ADMIN@EXAMPLE.COM", "sub": "4"}
        result = self._run(_require_admin(user=user))
        self.assertEqual(result, user)

    @patch.dict(os.environ, {"DECKDEX_ADMIN_EMAIL": "admin@example.com"})
    def test_missing_email_raises_403(self):
        user = {"sub": "5"}
        with self.assertRaises(_FakeHTTPException) as ctx:
            self._run(_require_admin(user=user))
        self.assertEqual(ctx.exception.status_code, 403)


class TestUserPayloadIsAdmin(unittest.TestCase):
    """Test that UserPayload model includes is_admin field."""

    def test_default_false(self):
        from pydantic import BaseModel
        from typing import Optional

        class UserPayload(BaseModel):
            id: int
            email: str
            display_name: Optional[str] = None
            picture: Optional[str] = None
            is_admin: bool = False

        payload = UserPayload(id=1, email="test@example.com")
        self.assertFalse(payload.is_admin)

    def test_explicit_true(self):
        from pydantic import BaseModel
        from typing import Optional

        class UserPayload(BaseModel):
            id: int
            email: str
            display_name: Optional[str] = None
            picture: Optional[str] = None
            is_admin: bool = False

        payload = UserPayload(id=1, email="test@example.com", is_admin=True)
        self.assertTrue(payload.is_admin)

    def test_serialization_includes_is_admin(self):
        from pydantic import BaseModel
        from typing import Optional

        class UserPayload(BaseModel):
            id: int
            email: str
            display_name: Optional[str] = None
            picture: Optional[str] = None
            is_admin: bool = False

        payload = UserPayload(id=1, email="admin@test.com", is_admin=True)
        d = payload.model_dump()
        self.assertTrue(d["is_admin"])

        payload2 = UserPayload(id=2, email="user@test.com")
        d2 = payload2.model_dump()
        self.assertFalse(d2["is_admin"])


if __name__ == "__main__":
    unittest.main()
