# Proposal: Card Image Cache Headers and Security Fix

## What

Three targeted improvements to card image serving:

1. **HTTP cache headers**: Add `Cache-Control: public, max-age=31536000, immutable` and `ETag` headers to all image endpoints. Without these, every page load triggers a full re-fetch from the server even though images are byte-for-byte identical across requests.

2. **Zero-copy serving**: Switch from `Response(content=data)` (loads full image into Python heap) to `FileResponse` (OS-level sendfile). The `FilesystemImageStore` stores images as files on disk — we should serve them directly from disk, not read bytes into memory then copy to the response buffer. `FileResponse` is already the established pattern in `auth.py` for avatar images.

3. **Key validation security fix**: `FilesystemImageStore._validate_key` currently rejects keys that _start with_ `/` but does not reject keys that _contain_ `/` in the middle. A key like `foo/../../etc/passwd` passes the current check (it does not start with `/`), allowing path traversal to arbitrary subdirectories under `base_dir` and potentially escaping it with `..`. The fix: reject any key where `/` appears _anywhere_.

## Why

**Correctness/security**: The key validation bug is a security vulnerability. Scryfall IDs are UUIDs (e.g. `a1b2c3d4-...`) and never contain `/`, but any code path that passes untrusted input as a key (e.g. the `scryfall_id` column value from a database row) could be exploited if that column is compromised. Defense-in-depth requires rejecting `/` at the storage layer regardless of how the key was formed.

**Performance — heap allocation**: Card images are ~60–150 KB JPEG/WebP files. At 50 concurrent gallery requests, `Response(content=data)` allocates ~7.5 MB of Python heap per batch. `FileResponse` delegates to uvicorn's `StaticFiles` infrastructure which uses `asyncio` file reads and avoids the Python-layer copy.

**Performance — HTTP caching**: Without `Cache-Control`, the browser must round-trip the server for every image on every navigation. Card images keyed by `scryfall_id` are immutable by definition — a Scryfall UUID identifies a specific card printing, and the image for that UUID never changes. `immutable` is the correct directive here; it suppresses even conditional revalidation requests.

## Scope

- `deckdex/storage/image_store.py` — key validation fix in `_validate_key`
- `backend/api/routes/cards.py` — `GET /api/cards/{id}/image`: add cache headers + FileResponse
- `backend/api/routes/catalog_routes.py` — `GET /api/catalog/cards/{scryfall_id}/image`: add cache headers + FileResponse
- `backend/api/services/card_image_service.py` — expose file path alongside bytes for FileResponse callers
- `tests/test_image_store.py` — new tests for the security fix
- `tests/test_card_image_cache.py` — new tests for cache headers

## Success Criteria

- `GET /api/cards/{id}/image` response includes `Cache-Control: public, max-age=31536000, immutable` and an `ETag` derived from the image file
- `GET /api/catalog/cards/{scryfall_id}/image` includes the same headers
- A key containing `/` (not at position 0) raises `ValueError` from `FilesystemImageStore._validate_key`
- No image bytes are loaded into Python memory on a cache-hit path when `FileResponse` is used
- All existing `test_image_store.py` tests continue to pass
- New test for `_validate_key` with embedded `/` passes

## Out of Scope

- Changing the `ImageStore` abstract interface signatures
- Frontend changes (the browser will respect HTTP headers automatically)
- ETags based on content hash vs. file mtime (mtime is sufficient for immutable assets)
- Nginx/reverse-proxy-level caching configuration
