"""Tests for ImageStore ABC and FilesystemImageStore."""

import os
import shutil
import tempfile
import unittest

from deckdex.storage.image_store import FilesystemImageStore


class TestFilesystemImageStore(unittest.TestCase):
    """Test FilesystemImageStore put/get/exists/delete."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = FilesystemImageStore(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_put_and_get_jpeg(self):
        data = b"\xff\xd8\xff\xe0fake-jpeg-data"
        self.store.put("card-001", data, "image/jpeg")
        result = self.store.get("card-001")
        self.assertIsNotNone(result)
        got_data, got_ct = result
        self.assertEqual(got_data, data)
        self.assertEqual(got_ct, "image/jpeg")

    def test_put_and_get_png(self):
        data = b"\x89PNGfake-png-data"
        self.store.put("card-002", data, "image/png")
        result = self.store.get("card-002")
        self.assertIsNotNone(result)
        got_data, got_ct = result
        self.assertEqual(got_data, data)
        self.assertEqual(got_ct, "image/png")

    def test_exists_true(self):
        self.store.put("card-003", b"data", "image/jpeg")
        self.assertTrue(self.store.exists("card-003"))

    def test_exists_false(self):
        self.assertFalse(self.store.exists("nonexistent"))

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.store.get("nonexistent"))

    def test_delete(self):
        self.store.put("card-004", b"data", "image/jpeg")
        self.assertTrue(self.store.exists("card-004"))
        self.store.delete("card-004")
        self.assertFalse(self.store.exists("card-004"))
        self.assertIsNone(self.store.get("card-004"))

    def test_delete_nonexistent_no_error(self):
        self.store.delete("never-existed")  # should not raise

    def test_auto_create_base_dir(self):
        nested = os.path.join(self.tmpdir, "a", "b", "c")
        store = FilesystemImageStore(nested)
        self.assertTrue(os.path.isdir(nested))
        store.put("test", b"data", "image/jpeg")
        self.assertIsNotNone(store.get("test"))

    def test_overwrite_replaces_file(self):
        self.store.put("card-005", b"old-data", "image/jpeg")
        self.store.put("card-005", b"new-data", "image/jpeg")
        data, _ = self.store.get("card-005")
        self.assertEqual(data, b"new-data")

    def test_extension_change_cleans_old_file(self):
        self.store.put("card-006", b"jpeg-data", "image/jpeg")
        # Overwrite with png — old .jpg should be cleaned up
        self.store.put("card-006", b"png-data", "image/png")
        result = self.store.get("card-006")
        self.assertIsNotNone(result)
        data, ct = result
        self.assertEqual(data, b"png-data")
        self.assertEqual(ct, "image/png")
        # .jpg file should not exist anymore
        old_jpg = os.path.join(self.tmpdir, "card-006.jpg")
        self.assertFalse(os.path.exists(old_jpg))

    def test_default_extension_for_unknown_content_type(self):
        self.store.put("card-007", b"data", "image/bmp")
        # Falls back to .jpg
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "card-007.jpg")))
        result = self.store.get("card-007")
        self.assertIsNotNone(result)

    def test_meta_sidecar_written(self):
        self.store.put("card-008", b"data", "image/webp")
        meta_path = os.path.join(self.tmpdir, "card-008.meta")
        self.assertTrue(os.path.exists(meta_path))
        import json

        meta = json.loads(open(meta_path).read())
        self.assertEqual(meta["content_type"], "image/webp")

    # ------------------------------------------------------------------
    # Security: key validation
    # ------------------------------------------------------------------

    def test_validate_key_rejects_embedded_slash(self):
        """Embedded slash must be rejected to prevent subdirectory traversal."""
        with self.assertRaises(ValueError):
            self.store.get("foo/bar")

    def test_validate_key_rejects_traversal_without_leading_slash(self):
        """Path traversal without leading slash must be rejected."""
        with self.assertRaises(ValueError):
            self.store.get("uuid/../../etc/passwd")

    def test_validate_key_accepts_uuid(self):
        """Standard Scryfall UUID key must be accepted."""
        self.store.put("a1b2c3d4-1234-5678-abcd-ef0123456789", b"data", "image/jpeg")
        self.assertIsNotNone(self.store.get("a1b2c3d4-1234-5678-abcd-ef0123456789"))

    # ------------------------------------------------------------------
    # get_path and get_content_type
    # ------------------------------------------------------------------

    def test_get_path_returns_path_after_put(self):
        self.store.put("card-path-001", b"data", "image/jpeg")
        p = self.store.get_path("card-path-001")
        self.assertIsNotNone(p)
        self.assertTrue(p.exists())
        self.assertTrue(p.is_file())

    def test_get_path_returns_none_for_missing(self):
        self.assertIsNone(self.store.get_path("nonexistent-path-key"))

    def test_get_content_type_without_reading_bytes(self):
        self.store.put("card-ct-001", b"data", "image/webp")
        ct = self.store.get_content_type("card-ct-001")
        self.assertEqual(ct, "image/webp")

    def test_get_content_type_returns_none_for_missing(self):
        self.assertIsNone(self.store.get_content_type("totally-missing"))


if __name__ == "__main__":
    unittest.main()
