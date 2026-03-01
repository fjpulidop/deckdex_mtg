"""Abstract image storage interface with filesystem implementation."""

import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger


_CONTENT_TYPE_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

_EXT_TO_CONTENT_TYPE = {v: k for k, v in _CONTENT_TYPE_TO_EXT.items()}


class ImageStore(ABC):
    """Abstract interface for image persistence."""

    @abstractmethod
    def get(self, key: str) -> Optional[Tuple[bytes, str]]:
        """Return (data, content_type) or None if not found."""

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store image data with the given content type."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if an image exists for the given key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove image for the given key (no-op if missing)."""


class FilesystemImageStore(ImageStore):
    """Store images as files on disk with JSON metadata sidecars.

    Layout::
        {base_dir}/{key}.jpg      — image data
        {base_dir}/{key}.meta     — {"content_type": "image/jpeg"}
    """

    def __init__(self, base_dir: str):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _ext_for(self, content_type: str) -> str:
        return _CONTENT_TYPE_TO_EXT.get(content_type, ".jpg")

    def _find_image_path(self, key: str) -> Optional[Path]:
        """Find existing image file for key (any extension)."""
        for ext in _CONTENT_TYPE_TO_EXT.values():
            p = self._base / f"{key}{ext}"
            if p.exists():
                return p
        return None

    def _meta_path(self, key: str) -> Path:
        return self._base / f"{key}.meta"

    def get(self, key: str) -> Optional[Tuple[bytes, str]]:
        img = self._find_image_path(key)
        if img is None:
            return None
        meta = self._meta_path(key)
        if meta.exists():
            try:
                content_type = json.loads(meta.read_text()).get("content_type", "image/jpeg")
            except Exception:
                content_type = "image/jpeg"
        else:
            content_type = _EXT_TO_CONTENT_TYPE.get(img.suffix, "image/jpeg")
        try:
            return img.read_bytes(), content_type
        except Exception as e:
            logger.warning(f"Failed to read image {img}: {e}")
            return None

    def put(self, key: str, data: bytes, content_type: str) -> None:
        ext = self._ext_for(content_type)
        img_path = self._base / f"{key}{ext}"
        meta_path = self._meta_path(key)

        # Remove any existing file with a different extension
        existing = self._find_image_path(key)
        if existing and existing != img_path:
            existing.unlink(missing_ok=True)

        # Atomic write: temp file in same dir, then os.replace
        fd, tmp = tempfile.mkstemp(dir=self._base, suffix=ext)
        try:
            os.write(fd, data)
            os.close(fd)
            os.replace(tmp, img_path)
        except Exception:
            os.close(fd) if not os.get_inheritable(fd) else None
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

        # Write metadata sidecar (not atomic — acceptable for metadata)
        try:
            meta_path.write_text(json.dumps({"content_type": content_type}))
        except Exception as e:
            logger.warning(f"Failed to write meta for {key}: {e}")

    def exists(self, key: str) -> bool:
        return self._find_image_path(key) is not None

    def delete(self, key: str) -> None:
        img = self._find_image_path(key)
        if img:
            img.unlink(missing_ok=True)
        meta = self._meta_path(key)
        meta.unlink(missing_ok=True)
