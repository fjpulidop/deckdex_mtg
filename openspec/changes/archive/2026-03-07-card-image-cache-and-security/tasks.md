# Tasks: Card Image Cache Headers and Security Fix

## Task 1: [x] Fix key validation security bug in FilesystemImageStore

**File**: `deckdex/storage/image_store.py`

**Change**: In `FilesystemImageStore._validate_key`, replace `key.startswith("/")` with `"/" in key`.

Before:
```python
if not key or ".." in key or key.startswith("/") or "\x00" in key:
```
After:
```python
if not key or ".." in key or "/" in key or "\x00" in key:
```

**Acceptance criteria**:
- `_validate_key("foo/bar")` raises `ValueError`
- `_validate_key("foo/../../etc/passwd")` raises `ValueError`
- `_validate_key("/absolute")` still raises `ValueError`
- `_validate_key("valid-uuid-key")` does not raise

**Depends on**: nothing

---

## Task 2: Add `get_path` to ImageStore ABC and FilesystemImageStore

**File**: `deckdex/storage/image_store.py`

Add to `ImageStore` ABC:
```python
@abstractmethod
def get_path(self, key: str) -> Optional[Path]:
    """Return the filesystem path for the stored image, or None if not found.
    Validates key. Returns None for non-filesystem-backed implementations."""
```

Add to `FilesystemImageStore`:
```python
def get_path(self, key: str) -> Optional[Path]:
    self._validate_key(key)
    return self._find_image_path(key)
```

**Acceptance criteria**:
- After `put("abc", data, "image/jpeg")`, `get_path("abc")` returns a `Path` that exists and equals `base_dir/abc.jpg`
- `get_path("nonexistent")` returns `None`
- `get_path("bad/key")` raises `ValueError`

**Depends on**: Task 1

---

## Task 3: Add `get_content_type` to FilesystemImageStore

**File**: `deckdex/storage/image_store.py`

Add to `FilesystemImageStore` (not to the ABC — this is a filesystem-specific convenience):
```python
def get_content_type(self, key: str) -> Optional[str]:
    """Return content_type for key without loading image bytes.
    Reads .meta sidecar if present; falls back to extension inference.
    Returns None if no image exists for the key."""
    self._validate_key(key)
    img = self._find_image_path(key)
    if img is None:
        return None
    meta = self._meta_path(key)
    if meta.exists():
        try:
            return json.loads(meta.read_text()).get("content_type", "image/jpeg")
        except Exception:
            pass
    return _EXT_TO_CONTENT_TYPE.get(img.suffix, "image/jpeg")
```

**Acceptance criteria**:
- After `put("abc", data, "image/webp")`, `get_content_type("abc")` returns `"image/webp"` without reading image bytes
- `get_content_type("missing")` returns `None`
- If `.meta` sidecar is absent, content type is inferred from extension

**Depends on**: Task 2

---

## Task 4: Add `get_card_image_path` to card_image_service

**File**: `backend/api/services/card_image_service.py`

Add a new function below the existing `get_card_image`:

```python
def get_card_image_path(
    card_id: int,
    image_store: ImageStore = None,
    user_id: Optional[int] = None,
) -> Tuple[Path, str, str]:
    """
    Return (file_path, content_type, etag) for the given card id.

    Same lookup flow as get_card_image, but returns the filesystem path
    for zero-copy serving via FileResponse instead of loading bytes into memory.

    Raises FileNotFoundError if card not found or image unavailable.
    """
    from pathlib import Path as _Path
    from ..dependencies import get_image_store

    if image_store is None:
        image_store = get_image_store()

    # Run the full resolution to ensure image is downloaded/stored if needed.
    # On cache hit this reads bytes once; the FileResponse skips the second read.
    # The overhead is one read_bytes() on first-ever request per card; subsequent
    # requests hit the filesystem directly via get_path().
    data, content_type = get_card_image(card_id, image_store=image_store, user_id=user_id)

    # Retrieve the path after resolution (scryfall_id may have been persisted lazily)
    from ..dependencies import get_collection_repo
    repo = get_collection_repo()
    card = repo.get_card_by_id(card_id)
    scryfall_id = card.get("scryfall_id") if card else None

    if scryfall_id:
        file_path = image_store.get_path(scryfall_id)
        if file_path is not None:
            s = file_path.stat()
            etag = f'"{s.st_mtime_ns:x}-{s.st_size:x}"'
            ct = image_store.get_content_type(scryfall_id) or content_type
            return file_path, ct, etag

    # Fallback: no path available — caller must use bytes Response
    raise FileNotFoundError(f"Image path not available for card_id={card_id}")
```

**Note**: The implementation above calls `get_card_image` first (to trigger download if needed), then resolves the path. This means first-ever requests still read bytes; all subsequent requests use only `get_path`. This avoids duplicating the complex resolution logic.

**Acceptance criteria**:
- Returns `(Path, str, str)` tuple when image exists in store
- Raises `FileNotFoundError` if card not found
- Does not break existing `get_card_image` callers

**Depends on**: Tasks 2, 3

---

## Task 5: Update `GET /api/cards/{id}/image` to use FileResponse and cache headers

**File**: `backend/api/routes/cards.py`

1. Add import at top: `from fastapi.responses import FileResponse`
2. Add import: `from ..services.card_image_service import get_card_image, get_card_image_path`
3. Replace the `get_card_image` route handler body:

```python
@router.get("/{id}/image")
async def get_card_image(id: int, user_id: int = Depends(get_current_user_id)):
    """
    Return the card's image by surrogate id.
    Served via FileResponse (zero-copy). Cache-Control: immutable (1 year).
    Returns 404 if card not found or image unavailable.
    """
    try:
        file_path, media_type, etag = get_card_image_path(id, user_id=user_id)
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": etag,
            },
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Card or image not found")
```

**Acceptance criteria**:
- Response includes `Cache-Control: public, max-age=31536000, immutable`
- Response includes a non-empty `ETag` header
- Response status 200 with correct `Content-Type` when image exists
- Response status 404 when card or image not found
- Existing behavior (auth, no ownership check) unchanged

**Depends on**: Task 4

---

## Task 6: Update `GET /api/catalog/cards/{scryfall_id}/image` to use FileResponse and cache headers

**File**: `backend/api/routes/catalog_routes.py`

1. Add import: `from fastapi.responses import FileResponse`
2. Replace the `get_card_image` handler:

```python
@router.get("/cards/{scryfall_id}/image")
async def get_card_image(
    scryfall_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Serve a catalog card image from filesystem. Cache-Control: immutable."""
    _, image_store = _get_stores()
    file_path = image_store.get_path(scryfall_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    content_type = image_store.get_content_type(scryfall_id) or "image/jpeg"
    s = file_path.stat()
    etag = f'"{s.st_mtime_ns:x}-{s.st_size:x}"'
    return FileResponse(
        file_path,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": etag,
        },
    )
```

Note: `image_store` is `FilesystemImageStore` which has `get_path` and `get_content_type`. Cast/type-ignore is not needed since we know the concrete type; if a future store lacks `get_path`, it returns `None` and we 404 (safe).

**Acceptance criteria**:
- Response includes `Cache-Control: public, max-age=31536000, immutable`
- Response includes a non-empty `ETag` header
- 404 when image not in store
- No `Response(content=data)` pattern remains in this handler

**Depends on**: Tasks 2, 3

---

## Task 7: Add tests for key validation fix

**File**: `tests/test_image_store.py`

Add to `TestFilesystemImageStore`:

```python
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
    # Does not raise
    self.store.put("a1b2c3d4-1234-5678-abcd-ef0123456789", b"data", "image/jpeg")
    self.assertIsNotNone(self.store.get("a1b2c3d4-1234-5678-abcd-ef0123456789"))
```

Also add tests for `get_path` and `get_content_type`:

```python
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
```

**Acceptance criteria**:
- All new tests pass
- All existing 10 tests continue to pass
- `pytest tests/test_image_store.py` exits 0

**Depends on**: Tasks 1, 2, 3

---

## Task 8: Add integration tests for cache headers

**File**: `tests/test_card_image_cache_headers.py` (new file)

Write `pytest`-style tests using `fastapi.testclient.TestClient` that:

1. Mock `get_card_image_path` to return a real temp file path, a content type, and an etag string
2. Call `GET /api/cards/1/image` (authenticated, mock JWT)
3. Assert `response.headers["cache-control"] == "public, max-age=31536000, immutable"`
4. Assert `"etag"` in `response.headers`

Similarly for the catalog endpoint:
1. Mock `image_store.get_path(scryfall_id)` to return a real temp file path
2. Mock `image_store.get_content_type(scryfall_id)` to return `"image/jpeg"`
3. Call `GET /api/catalog/cards/{scryfall_id}/image`
4. Assert `Cache-Control` and `ETag` headers are present

**Acceptance criteria**:
- New test file passes: `pytest tests/test_card_image_cache_headers.py`
- Tests mock all external dependencies (no real Scryfall calls, no real DB)

**Depends on**: Tasks 5, 6

---

## Execution Order

```
Task 1 (validate key fix)
  └── Task 2 (get_path on ABC)
        └── Task 3 (get_content_type on FilesystemImageStore)
              ├── Task 4 (get_card_image_path service)
              │     └── Task 5 (cards route update)
              │           └── Task 8 (integration tests)
              └── Task 6 (catalog route update)
                    └── Task 8
Task 7 (unit tests for Tasks 1-3) — can run after Task 3
```

Tasks 5 and 6 can be implemented in parallel once Tasks 2-4 (for 5) and 2-3 (for 6) are complete. Task 8 must follow both 5 and 6.
