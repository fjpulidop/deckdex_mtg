# Delta Spec: Card Image Storage — HTTP Cache Headers and Zero-Copy Serving

Base spec: `openspec/specs/card-image-storage/spec.md`

## Changes

### New Requirement: HTTP cache headers on image endpoints

Both `GET /api/cards/{id}/image` and `GET /api/catalog/cards/{scryfall_id}/image` SHALL return HTTP cache headers that instruct the browser to cache images indefinitely.

#### Scenario: Image response includes Cache-Control header
- **WHEN** an authenticated user requests `GET /api/cards/{id}/image` and the image exists
- **THEN** the response SHALL include `Cache-Control: public, max-age=31536000, immutable`

#### Scenario: Catalog image response includes Cache-Control header
- **WHEN** an authenticated user requests `GET /api/catalog/cards/{scryfall_id}/image` and the image exists
- **THEN** the response SHALL include `Cache-Control: public, max-age=31536000, immutable`

#### Scenario: Image response includes ETag header
- **WHEN** an authenticated user requests either image endpoint and the image exists
- **THEN** the response SHALL include an `ETag` header derived from the image file's mtime and size
- **AND** the ETag SHALL be formatted as a quoted hex string: `"<st_mtime_ns_hex>-<st_size_hex>"`

#### Rationale for `immutable`
- Images are keyed by `scryfall_id` (Scryfall UUID), which identifies a specific card printing
- The image content for a given `scryfall_id` never changes — Scryfall assigns a new UUID for new printings
- `immutable` suppresses conditional revalidation requests on page reload, eliminating round-trips

### New Requirement: Zero-copy image serving via FileResponse

Image endpoints SHALL serve images using `FileResponse` (OS-level file transfer) rather than loading image bytes into Python memory.

#### Scenario: No heap allocation on cache hit
- **WHEN** `GET /api/cards/{id}/image` is called and the image exists in the filesystem store
- **THEN** the image bytes SHALL NOT be loaded into Python memory (no `read_bytes()` call on the happy path)
- **AND** the file SHALL be served via `FileResponse` using the path returned by `image_store.get_path()`

#### Scenario: Fallback to bytes for non-filesystem stores
- **WHEN** `image_store.get_path()` returns `None` (non-filesystem-backed store)
- **THEN** the route SHALL fall back to `Response(content=data, ...)` with the same cache headers
- **NOTE** This fallback exists for theoretical future store implementations; `FilesystemImageStore` always returns a path

### Preserved Requirements

All existing requirements from `openspec/specs/card-image-storage/spec.md` remain in force:
- Authentication required (401 if not authenticated)
- 404 if card not found or image unavailable
- Any authenticated user may access any card image (no ownership check)
- Scryfall fallback when `scryfall_enabled` is true in user settings
