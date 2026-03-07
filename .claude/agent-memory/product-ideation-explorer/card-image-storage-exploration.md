# Card Image Storage Optimization - Exploration (2026-03-07)

## Area: Card image storage optimization

### Current State

**Architecture**: Two-tier image system:
1. **Backend (FilesystemImageStore)**: Abstract `ImageStore` ABC with `FilesystemImageStore` implementation. Images stored as `{base_dir}/{scryfall_id}.{ext}` with `.meta` JSON sidecar files. Atomic writes via `tempfile` + `os.replace`. Default dir: `data/images/`.
2. **Frontend (useImageCache)**: Module-level `Map<number, string>` keyed by card ID (not scryfall_id). Each card triggers individual `GET /api/cards/{id}/image` fetch. Blob URLs created via `URL.createObjectURL()` and intentionally never revoked (session-lifetime cache).

**Image sources**:
- **Catalog sync** (bulk): `CatalogSyncJob._sync_images()` downloads from Scryfall in batches of 100, 100ms delay between requests, 3 retries. Cursor-based resume. Tracks `image_status` (pending/downloaded/failed) per catalog card.
- **On-demand** (per-card): `card_image_service.get_card_image()` fetches from Scryfall when a user requests a card image not yet cached. Requires Scryfall to be enabled in user settings.

**Serving path**: `GET /api/cards/{id}/image` reads entire file into memory (`img.read_bytes()`) and returns as `Response(content=data)`. No streaming. No HTTP cache headers. No `FileResponse`.

**Gallery view**: `CardGallery.tsx` uses `IntersectionObserver` with 200px rootMargin for lazy loading. Each visible tile calls `useImageCache(cardId)` which triggers individual API fetch.

**Tests**: 10 unit tests for `FilesystemImageStore` (good coverage of CRUD, extension changes, meta sidecars). 5 tests for `useImageCache` (null state, fetch, error, dedup, session cache).

### Gaps Found

#### SECURITY: Key validation incomplete (spec violation)
- **Spec says**: reject keys containing `..`, `/`, or null bytes
- **Implementation**: only checks `key.startswith("/")` -- embedded `/` chars (e.g., `foo/bar`) are NOT rejected
- This allows subdirectory creation within base_dir (not a path traversal escape, but violates spec intent)
- File: `/Users/javi/repos/deckdex_mtg/deckdex/storage/image_store.py` line 56

#### PERFORMANCE: No HTTP cache headers on image responses
- Both `GET /api/cards/{id}/image` and `GET /api/catalog/cards/{scryfall_id}/image` return raw `Response(content=data)` with zero cache headers
- No `Cache-Control`, no `ETag`, no `Last-Modified`
- Browser makes full round-trip on every request even though card images are immutable (same scryfall_id = same image forever)
- Files: `/Users/javi/repos/deckdex_mtg/backend/api/routes/cards.py` line 295, `/Users/javi/repos/deckdex_mtg/backend/api/routes/catalog_routes.py` line 86

#### PERFORMANCE: Full file read into memory for every image serve
- `FilesystemImageStore.get()` does `img.read_bytes()` (loads entire image into Python memory)
- Route then passes bytes to `Response(content=data)` -- another copy
- For a gallery with 50 cards visible, this means 50 concurrent full-file reads into memory
- FastAPI's `FileResponse` would use zero-copy sendfile, dramatically reducing memory usage
- Note: `FileResponse` is already used in `auth.py` for avatar images -- the pattern exists in the codebase

#### PERFORMANCE: No batch image endpoint
- Gallery view triggers N individual HTTP requests (one per visible card)
- Each request: HTTP overhead + auth check + DB lookup (card -> scryfall_id) + filesystem read
- A batch endpoint (`POST /api/cards/images` with list of IDs) could return multiple images or at minimum their URLs
- Alternative: return scryfall_id in card list response so frontend can use catalog image endpoint directly

#### PERFORMANCE: Frontend cache keyed by card ID, not scryfall_id
- The same physical card (same scryfall_id) in different collections or appearing in different contexts triggers separate fetches because cache key is `card.id` (surrogate PK), not `scryfall_id`
- If a user has the same card in collection + a deck view, two fetches for the same image
- Gallery note from previous exploration: "50 cards/page = 50 individual image fetches"

#### PERFORMANCE: Blob URLs never revoked (memory leak over session)
- `useImageCache` comment: "Blob URLs are never revoked -- intentional, as revocation defeats the cache"
- For large collections (1000+ cards browsed), blob URLs accumulate in browser memory
- Each blob URL holds a reference to the full image data in memory
- No LRU eviction or size limit on the cache

#### MISSING: No disk space management
- No maximum cache size configuration
- No eviction policy for old/unused images
- Full Scryfall catalog is ~80K+ unique cards; at ~50KB per "normal" image = ~4GB
- No admin UI to see disk usage or purge cache
- No cleanup of orphaned images (images for cards no longer in any collection)

#### MISSING: No image size variants
- Config supports `image_size: "normal"` (50KB) but only one size is downloaded per sync
- Gallery thumbnails don't need "normal" size -- "small" (15KB) would be 3x more efficient
- Card detail modal could use "large" for high-res zoom
- Would need multiple files per scryfall_id or lazy download of alternate sizes

#### BUG: `put()` error handling has fd leak potential
- Line 110: `os.close(fd) if not os.get_inheritable(fd) else None` -- `os.get_inheritable()` is not a reliable check for whether the fd is already closed; after `os.close(fd)` on line 107, calling `os.get_inheritable(fd)` on an already-closed fd raises `OSError`
- Should use a flag or try/except pattern instead

### Improvement Ideas

| # | Idea | Value | Complexity | Impact/Effort |
|---|------|-------|------------|---------------|
| 1 | **Add Cache-Control headers** (`Cache-Control: public, max-age=31536000, immutable` for images served by scryfall_id) | HIGH - eliminates redundant fetches for browser-cached images | SMALL - 2-3 lines per route | **BEST** |
| 2 | **Use FileResponse instead of Response(content=bytes)** | HIGH - zero-copy sendfile, dramatically less memory per request | SMALL - change get() to return path, use FileResponse | **EXCELLENT** |
| 3 | **Fix key validation** (reject `/` anywhere, not just startswith) | MEDIUM - security spec compliance | TRIVIAL - change one condition | **EXCELLENT** |
| 4 | **Return scryfall_id in card list API response** so frontend can construct direct image URLs without per-card lookups | HIGH - eliminates N DB lookups per gallery page | SMALL - add field to response model | **EXCELLENT** |
| 5 | **Frontend: cache by scryfall_id instead of card.id** | MEDIUM - deduplicates same-printing images across views | SMALL - change cache key, requires #4 | HIGH |
| 6 | **Add LRU eviction to frontend blob cache** (e.g., max 500 entries, revoke oldest) | MEDIUM - prevents memory growth in long sessions | SMALL - wrap Map with LRU logic | HIGH |
| 7 | **Fix put() fd leak** in error path | LOW - edge case but correct code matters | TRIVIAL | GOOD |
| 8 | **Multi-size image support** (small for gallery, normal for list, large for detail) | HIGH - 3x bandwidth savings for gallery | MEDIUM - store multiple sizes, add size param to API | GOOD |
| 9 | **Batch image endpoint** (`POST /api/cards/images/batch`) | MEDIUM - reduces HTTP overhead for gallery | MEDIUM - new endpoint, response format design | MODERATE |
| 10 | **Disk space management** (max cache size, eviction, admin stats) | LOW (localhost app) - nice-to-have | LARGE - LRU on disk, admin UI | LOW |
| 11 | **ETag support** based on scryfall_id hash for conditional requests | MEDIUM - saves bandwidth on re-validation | SMALL - but Cache-Control immutable is simpler | MODERATE |

### Recommended Top Pick

**Ideas #1 + #2 + #3 as a single small change** (combined effort: ~1 hour).

1. **Cache-Control: immutable** on image responses. Card images keyed by scryfall_id never change -- this is the single highest-impact optimization possible. One header addition eliminates all redundant image fetches after first load. The browser's native cache handles everything.

2. **FileResponse** instead of loading bytes into Python memory. The pattern already exists in `auth.py` (avatar images). This changes `ImageStore.get()` to also expose a `get_path()` method (or the route bypasses the store and constructs the path). Result: zero-copy kernel-level file serving, no Python memory allocation per image.

3. **Fix `/` in key validation**. One character change (`"/" in key` instead of `key.startswith("/")`), brings implementation into spec compliance.

These three changes together transform the image serving from "read entire file into Python memory on every request with no browser caching" to "kernel-level zero-copy file serving with permanent browser caching." For a gallery view showing 50 cards, this is the difference between 50 HTTP requests loading ~2.5MB into Python memory vs. 50 requests served from browser cache with zero backend load after first visit.

**Next priority after that**: Idea #4 (return scryfall_id in card list response) + #5 (frontend cache by scryfall_id). This eliminates the per-card DB lookup overhead and deduplicates cross-view image caching.
