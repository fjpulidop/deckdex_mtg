"""Integration tests for cache headers on card image endpoints.

Tests that GET /api/cards/{id}/image and GET /api/catalog/cards/{scryfall_id}/image
return Cache-Control and ETag headers.

All external dependencies are mocked — no real filesystem, DB, or Scryfall calls.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.dependencies import get_current_user_id
from backend.api.main import app


class TestCardImageCacheHeaders(unittest.TestCase):
    """Test GET /api/cards/{id}/image returns cache headers."""

    def setUp(self):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        self.client = TestClient(app)
        # Create a real temp file so FileResponse can actually read it
        self.tmpdir = tempfile.mkdtemp()
        self.img_path = Path(self.tmpdir) / "test-card.jpg"
        self.img_path.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-data")

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user_id, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_etag(self, path: Path) -> str:
        s = path.stat()
        return f'"{s.st_mtime_ns:x}-{s.st_size:x}"'

    def test_image_response_includes_cache_control(self):
        """Cache-Control: public, max-age=31536000, immutable is returned."""
        etag = self._make_etag(self.img_path)
        with patch(
            "backend.api.routes.cards.get_card_image_path",
            return_value=(self.img_path, "image/jpeg", etag),
        ):
            response = self.client.get("/api/cards/1/image")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("cache-control"),
            "public, max-age=31536000, immutable",
        )

    def test_image_response_includes_etag(self):
        """ETag header is present and non-empty."""
        etag = self._make_etag(self.img_path)
        with patch(
            "backend.api.routes.cards.get_card_image_path",
            return_value=(self.img_path, "image/jpeg", etag),
        ):
            response = self.client.get("/api/cards/1/image")

        self.assertEqual(response.status_code, 200)
        self.assertIn("etag", response.headers)
        self.assertTrue(response.headers["etag"])

    def test_image_response_content_type_correct(self):
        """Content-Type matches the value returned by get_card_image_path."""
        etag = self._make_etag(self.img_path)
        with patch(
            "backend.api.routes.cards.get_card_image_path",
            return_value=(self.img_path, "image/jpeg", etag),
        ):
            response = self.client.get("/api/cards/1/image")

        self.assertEqual(response.status_code, 200)
        self.assertIn("image/jpeg", response.headers.get("content-type", ""))

    def test_image_response_404_when_not_found(self):
        """404 is returned when get_card_image_path raises FileNotFoundError."""
        with patch(
            "backend.api.routes.cards.get_card_image_path",
            side_effect=FileNotFoundError("not found"),
        ):
            response = self.client.get("/api/cards/999/image")

        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())


class TestCatalogImageCacheHeaders(unittest.TestCase):
    """Test GET /api/catalog/cards/{scryfall_id}/image returns cache headers."""

    def setUp(self):
        app.dependency_overrides[get_current_user_id] = lambda: 1
        self.client = TestClient(app)
        # Create a real temp image file so FileResponse can serve it
        self.tmpdir = tempfile.mkdtemp()
        self.img_path = Path(self.tmpdir) / "abc-123.jpg"
        self.img_path.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-data")

    def tearDown(self):
        app.dependency_overrides.pop(get_current_user_id, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_mock_store(self, path: Path, content_type: str = "image/jpeg"):
        """Build a mock image_store for catalog route injection."""
        store = MagicMock()
        store.get_path.return_value = path
        store.get_content_type.return_value = content_type
        return store

    def test_catalog_image_includes_cache_control(self):
        """Cache-Control: public, max-age=31536000, immutable is returned."""
        store = self._make_mock_store(self.img_path)
        with patch("backend.api.routes.catalog_routes._get_stores", return_value=(MagicMock(), store)):
            response = self.client.get("/api/catalog/cards/abc-123/image")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("cache-control"),
            "public, max-age=31536000, immutable",
        )

    def test_catalog_image_includes_etag(self):
        """ETag header is present and non-empty."""
        store = self._make_mock_store(self.img_path)
        with patch("backend.api.routes.catalog_routes._get_stores", return_value=(MagicMock(), store)):
            response = self.client.get("/api/catalog/cards/abc-123/image")

        self.assertEqual(response.status_code, 200)
        self.assertIn("etag", response.headers)
        self.assertTrue(response.headers["etag"])

    def test_catalog_image_404_when_not_in_store(self):
        """404 is returned when image_store.get_path returns None."""
        store = MagicMock()
        store.get_path.return_value = None
        with patch("backend.api.routes.catalog_routes._get_stores", return_value=(MagicMock(), store)):
            response = self.client.get("/api/catalog/cards/missing-id/image")

        self.assertEqual(response.status_code, 404)

    def test_catalog_image_content_type_from_store(self):
        """Content-Type matches what get_content_type returns."""
        img_path = Path(self.tmpdir) / "abc-webp.webp"
        img_path.write_bytes(b"RIFF\x00\x00\x00\x00WEBPfake")
        store = self._make_mock_store(img_path, content_type="image/webp")
        with patch("backend.api.routes.catalog_routes._get_stores", return_value=(MagicMock(), store)):
            response = self.client.get("/api/catalog/cards/abc-webp/image")

        self.assertEqual(response.status_code, 200)
        self.assertIn("image/webp", response.headers.get("content-type", ""))


if __name__ == "__main__":
    unittest.main()
