# Design: Card Image Cache Headers and Security Fix

## 1. Key Validation Security Fix

### Current behavior (`deckdex/storage/image_store.py`, line 56)

```python
if not key or ".." in key or key.startswith("/") or "\x00" in key:
    raise ValueError(f"Invalid image store key: {key!r}")
```

`key.startswith("/")` rejects absolute paths but permits embedded slashes, e.g. `"uuid/../../secret"`. Combined with `base_dir / f"{key}{ext}"`, Python's `Path` resolves the `..` components, potentially escaping `base_dir`.

### Fix

Replace `key.startswith("/")` with `"/" in key`:

```python
if not key or ".." in key or "/" in key or "\x00" in key:
    raise ValueError(f"Invalid image store key: {key!r}")
```

**Why `"/" in key` is correct**: Scryfall UUIDs are hyphen-separated hex (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`). No legitimate key ever contains a forward slash. Rejecting `/` anywhere closes the path traversal vector completely, regardless of whether it appears at position 0 or in the middle.

**Backward compatibility**: All existing callers pass `scryfall_id` values from the database (UUIDs). No existing test key contains `/`. The change is strictly more restrictive — it only affects keys that were already dangerous.

---

## 2. FileResponse for Zero-Copy Serving

### Problem

Both image endpoints currently use the same pattern:

```python
# cards.py line 295
data, media_type = resolve_card_image(id, user_id=user_id)
return Response(content=data, media_type=media_type)

# catalog_routes.py line 85-86
data, content_type = result
return Response(content=data, media_type=content_type)
```

`resolve_card_image` calls `image_store.get(scryfall_id)` which calls `img.read_bytes()` — the entire image is read from disk into a Python `bytes` object and then copied again into the HTTP response buffer.

`FileResponse` avoids this by passing the file descriptor to uvicorn, which uses `sendfile(2)` on Linux or equivalent zero-copy transfer. This is identical to the pattern used in `backend/api/routes/auth.py` for avatar images (lines 560, 588, 622).

### Service layer change (`card_image_service.py`)

The current `get_card_image` signature returns `(bytes, str)`. To support `FileResponse` at the route layer, we need to return the file path instead of (or alongside) the bytes.

**Decision**: Add a new function `get_card_image_path` that returns `(Path, str)` — the absolute file path and content type. The existing `get_card_image` function is **preserved unchanged** for backward compatibility (tests, any other callers). The route layer calls `get_card_image_path` for the happy path.

`get_card_image_path` follows the same logic as `get_card_image` but:
- On ImageStore cache hit: returns `(img_path, content_type)` — retrieved from `FilesystemImageStore._find_image_path` via a new public `get_path(key)` method
- On Scryfall download: stores via `image_store.put(...)` then resolves path via `image_store.get_path(key)`

**Alternative considered**: Return `Union[bytes, Path]` from `get_card_image`. Rejected — changes the return type contract of an existing function that has tests.

### `ImageStore` interface addition

Add `get_path(key: str) -> Optional[Path]` to the `ImageStore` ABC:

```python
@abstractmethod
def get_path(self, key: str) -> Optional[Path]:
    """Return the filesystem path for the image, or None if not stored.
    Only meaningful for filesystem-backed stores."""
```

`FilesystemImageStore.get_path` delegates to `_find_image_path`. For non-filesystem stores (future), returning `None` is acceptable — callers fall back to the bytes path.

### Route changes

**`backend/api/routes/cards.py` — `GET /api/cards/{id}/image`**:

```python
from fastapi.responses import FileResponse
from ..services.card_image_service import get_card_image_path

@router.get("/{id}/image")
async def get_card_image(id: int, user_id: int = Depends(get_current_user_id)):
    try:
        file_path, media_type, etag = get_card_image_path(id, user_id=user_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Card or image not found")
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": etag,
        },
    )
```

**`backend/api/routes/catalog_routes.py` — `GET /api/catalog/cards/{scryfall_id}/image`**:

```python
from fastapi.responses import FileResponse

@router.get("/cards/{scryfall_id}/image")
async def get_card_image(scryfall_id: str, user_id: int = Depends(get_current_user_id)):
    _, image_store = _get_stores()
    file_path = image_store.get_path(scryfall_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    content_type = _resolve_content_type(image_store, scryfall_id, file_path)
    etag = _make_etag(file_path)
    return FileResponse(
        file_path,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": etag,
        },
    )
```

The catalog route already has the `scryfall_id` directly — it can call `image_store.get_path(scryfall_id)` without going through `card_image_service`.

---

## 3. Cache-Control and ETag Headers

### Header values

| Header | Value | Rationale |
|--------|-------|-----------|
| `Cache-Control` | `public, max-age=31536000, immutable` | Images are immutable by `scryfall_id`; 1-year max-age; `immutable` prevents revalidation on reload |
| `ETag` | `"<hex>"` derived from file mtime + size | Provides conditional GET support; cheap to compute, no file read required |

### ETag computation

```python
import stat

def _make_etag(path: Path) -> str:
    s = path.stat()
    return f'"{s.st_mtime_ns:x}-{s.st_size:x}"'
```

Using `st_mtime_ns` (nanosecond mtime) and `st_size` — fast, no content read, stable for immutable files.

**Decision against content-hash ETag**: A SHA-256 hash requires reading the file to compute. For immutable assets this provides no benefit over mtime/size, and adds latency. Strong ETags from mtime are RFC 7232 compliant for this use case.

### Where to put `_make_etag`

A module-level private helper in each route file, or a shared utility. Given that only two route files need it, a local helper in each is simpler and avoids creating a new module. If a third image endpoint appears, extract to `backend/api/utils/http.py`.

---

## 4. Content-type Resolution for Catalog Route

The catalog `get_card_image` endpoint currently calls `catalog_service.get_image(image_store, scryfall_id)` which returns `(bytes, content_type)`. After switching to `FileResponse`, we need the content type without reading bytes.

Add `get_image_content_type(image_store, key) -> Optional[str]` to `catalog_service`, or read it from the meta sidecar. The cleaner approach: `FilesystemImageStore.get_path` returns only the path; a companion `get_content_type(key)` reads only the `.meta` sidecar (a small JSON file). This avoids reading image bytes just to get the media type.

Add `get_content_type(key: str) -> Optional[str]` to `FilesystemImageStore` (not abstract — callers that need it can check for the method, falling back to extension-based inference).

---

## 5. Affected Files Summary

| File | Change |
|------|--------|
| `deckdex/storage/image_store.py` | Fix `_validate_key` (`"/" in key`); add `get_path()` to ABC and impl; add `get_content_type()` to `FilesystemImageStore` |
| `backend/api/services/card_image_service.py` | Add `get_card_image_path()` returning `(Path, str, str)` (path, content_type, etag) |
| `backend/api/routes/cards.py` | Import `FileResponse`; call `get_card_image_path`; add cache headers |
| `backend/api/routes/catalog_routes.py` | Import `FileResponse`; call `image_store.get_path`; add cache headers |
| `tests/test_image_store.py` | Add 2 tests for `/`-in-key validation |
| `tests/test_card_image_cache.py` | New file: integration tests for cache headers on both endpoints |

---

## 6. No Migration Required

No schema changes. No data migration. The `FilesystemImageStore` filesystem layout is unchanged — `get_path` and `get_content_type` are read-only additions.

---

## 7. Edge Cases and Risks

**FileResponse with non-existent path**: `FileResponse` raises `FileNotFoundError` if the path disappears between the `get_path` check and the actual send (TOCTOU race). This is acceptable — the file can only disappear if `delete()` is called concurrently, which only happens during catalog sync or manual cleanup. The OS will return a 500 in this rare case, same as today.

**ETag on catalog route**: The catalog endpoint has `scryfall_id` as a path parameter that is already validated by FastAPI as a string. It passes through to `image_store.get_path(scryfall_id)` which calls `_validate_key`. The security fix in step 1 ensures any embedded `/` in a crafted URL is rejected at the storage layer.

**`get_card_image` (bytes path) preserved**: The bytes-returning function is still used in tests. No test changes required for existing tests.

**Conditional GET (`If-None-Match`)**: Not explicitly implemented — FastAPI/Starlette's `FileResponse` handles `If-Modified-Since` automatically. Adding `ETag` in the response headers means browsers will send `If-None-Match` on subsequent requests; without a handler, the server returns 200 again. This is acceptable for localhost use. A full conditional GET handler is out of scope.
