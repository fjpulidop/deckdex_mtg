## Context

- Every card lookup (autocomplete, resolve, image) currently goes to Scryfall's API in real time. There is no local catalog of cards.
- Card images are stored in PostgreSQL BYTEA (`card_image_cache` table, keyed by `scryfall_id`). This works for on-demand caching of a few hundred images but won't scale to 400k images (~20GB).
- The app is moving toward internet deployment with multiple users. PostgreSQL BYTEA for images is expensive and adds unnecessary DB load at scale.
- Scryfall offers a bulk data API (JSON download of all cards, ~200MB compressed) but no bulk image download — images must be fetched individually at 100ms rate limit (~11 hours for all 400k cards).
- Existing patterns: `CollectionRepository` (ABC + Postgres impl), `CardFetcher` (Scryfall client), WebSocket progress (`ConnectionManager`), background jobs (`jobs` table), config via dataclasses + `config_loader.py`.

## Goals / Non-Goals

**Goals:**

- Store all ~400k Scryfall card printings locally in a `catalog_cards` table.
- Download and store all card images on filesystem, replacing PostgreSQL BYTEA.
- Provide an abstract `ImageStore` interface for easy S3 migration later.
- Background sync job (admin-triggered) that is resumable across interruptions.
- Catalog repository for local card lookups (search, autocomplete, get by ID).
- WebSocket progress for the sync job.

**Non-Goals:**

- Frontend changes (admin UI, settings toggles — those are separate changes).
- Changing existing card lookup flows to use catalog-first (separate change: `external-apis-settings`).
- S3ImageStore implementation (future; we build the interface now).
- Incremental/delta sync (full re-sync only; Scryfall bulk data doesn't support delta).

## Decisions

1. **Image storage: filesystem, not PostgreSQL BYTEA**
   - **Decision:** All images (catalog and user-requested) stored on filesystem at `data/images/{scryfall_id}.jpg`. Abstract `ImageStore` interface with `FilesystemImageStore` implementation. Existing `card_image_cache` BYTEA data migrated to filesystem, table dropped.
   - **Rationale:** 20GB in PostgreSQL makes pg_dump slow, backups expensive, and adds query overhead for blob serving. Filesystem is fast, cheap, and can be served by nginx/CDN. The abstract interface makes S3 migration a single implementation swap.
   - **Alternatives:** Keep PostgreSQL BYTEA (doesn't scale), S3 directly (adds infra complexity now).

2. **Single `data/images/` directory for ALL images (unified)**
   - **Decision:** Both catalog images and on-demand user cache images go to the same directory. No separate `catalog_images/` vs `user_images/`. Key is always `scryfall_id`.
   - **Rationale:** An image is an image regardless of how it got there. Unifying avoids duplication (catalog downloads an image, then a user requests it — same file). Simpler to reason about.
   - **Alternatives:** Separate directories (adds complexity, potential duplication).

3. **Scryfall bulk data JSON for card metadata**
   - **Decision:** Download Scryfall's "Default Cards" bulk data file (~200MB JSON). Parse and UPSERT all cards into `catalog_cards`. This is a single HTTP download, not per-card API calls.
   - **Rationale:** Scryfall explicitly provides bulk exports for this purpose. One download vs 400k individual API calls. The "Default Cards" file includes one entry per unique printing with all metadata we need.
   - **Alternatives:** "All Cards" bulk file (larger, includes digital-only); per-card API calls (violates rate limits for this volume).

4. **Image download: per-card with 100ms rate limit, cursor-based resume**
   - **Decision:** After bulk JSON is loaded, iterate `catalog_cards` ordered by `scryfall_id`. For each card with `image_status = 'pending'`, download the `normal` size image from Scryfall. Sleep 100ms between requests. Track progress in `catalog_sync_state.last_image_cursor`. On restart, resume from cursor.
   - **Rationale:** Scryfall has no bulk image download. 100ms rate limit is their TOS requirement. Cursor-based resume means an 11-hour job that crashes at hour 6 only repeats from the crash point. `image_status` per card means we can also skip already-downloaded images.
   - **Alternatives:** Download all sizes (triples storage and time); skip images entirely (breaks the purpose).

5. **Sync job as background thread with WebSocket progress**
   - **Decision:** Sync job runs in a background thread (like existing process/import jobs). Reports progress via the existing `ConnectionManager` WebSocket pattern. Job tracked in the `jobs` table with type `catalog_sync`. Single sync at a time (409 if already running).
   - **Rationale:** Follows existing patterns exactly. No new infrastructure needed.
   - **Alternatives:** Celery worker (overkill); cron job (no progress reporting).

6. **Catalog repository: separate from CollectionRepository**
   - **Decision:** New `CatalogRepository` class (not extending `CollectionRepository`). Different table, different purpose. Methods: `search_by_name(query, limit)`, `autocomplete(query, limit)`, `get_by_scryfall_id(id)`, `get_sync_state()`, `upsert_cards(cards_batch)`, `update_sync_state(...)`.
   - **Rationale:** Catalog is read-heavy, admin-write. Collection is user-owned CRUD. Mixing them violates SRP. Catalog doesn't need user scoping (shared data).
   - **Alternatives:** Extend CollectionRepository (muddies the interface); use raw SQL in service (breaks repository pattern).

7. **ImageStore interface**
   - **Decision:** Abstract base class with `get(key) -> Optional[Tuple[bytes, str]]`, `put(key, data, content_type)`, `exists(key) -> bool`, `delete(key)`. `FilesystemImageStore` implementation stores files at `{base_dir}/{key}.{ext}` with a `.meta` JSON sidecar for content_type. Extension derived from content_type (`image/jpeg` → `.jpg`, `image/png` → `.png`).
   - **Rationale:** Clean interface that maps directly to S3 semantics (key-value with metadata). Sidecar avoids needing a DB lookup for content-type.
   - **Alternatives:** Store content-type in filename (fragile); always assume JPEG (wrong for some cards); use DB for metadata (defeats purpose).

8. **Config: CatalogConfig dataclass**
   - **Decision:** New `CatalogConfig` dataclass with `image_dir` (default `data/images`), `bulk_data_url` (default Scryfall default cards URL), `image_size` (default `normal`). Added to `ProcessorConfig`. Loaded via `config_loader.py` from `catalog` section in `config.yaml`.
   - **Rationale:** Follows existing config pattern exactly. Image dir is configurable for Docker volume mounts.
   - **Alternatives:** Hardcode paths (breaks Docker); separate config file (breaks convention).

9. **Migration: BYTEA → filesystem with data migration script**
   - **Decision:** Migration 010 creates `catalog_cards` and `catalog_sync_state`. Migration 011 is a Python script (not SQL) that reads existing `card_image_cache` rows, writes them to filesystem via ImageStore, then drops the table. The `card_image_service.py` is updated to use `ImageStore` for both reads and writes.
   - **Rationale:** Can't do binary file writes in SQL. Python migration script can iterate rows, write files, and verify. Table drop only after successful migration.
   - **Alternatives:** Keep both systems running (complexity); drop BYTEA without migration (data loss).

## Risks / Trade-offs

- **Risk:** 11-hour image sync may fail mid-way due to network issues or Scryfall downtime. **Mitigation:** Cursor-based resume; per-card `image_status` tracking; automatic retry with backoff per image (3 attempts, then mark `failed` and continue).
- **Risk:** Filesystem images need backup separately from DB. **Mitigation:** Images are reconstructible (re-sync from Scryfall). Document that image dir should be in backup plan but is not critical data.
- **Risk:** Concurrent access to filesystem images during sync. **Mitigation:** Write to temp file, then atomic rename (`os.rename`). Readers either get old file or new file, never partial.
- **Trade-off:** `catalog_cards` duplicates some data that's also in the user's `cards` table. This is intentional — catalog is the reference, collection is the user's owned cards with their quantities and prices.
- **Trade-off:** Dropping `card_image_cache` table means the migration is irreversible. **Mitigation:** Migration script verifies all images were written to filesystem before dropping.

## Migration Plan

1. Migration 010: Create `catalog_cards` and `catalog_sync_state` tables (pure SQL, no data).
2. Deploy backend with new code (ImageStore, catalog repository, catalog service, routes).
3. Migration 011: Python script migrates `card_image_cache` BYTEA → filesystem, then drops table.
4. `card_image_service.py` updated to use ImageStore. Reads from filesystem; if image not found on filesystem, falls back to Scryfall fetch and stores on filesystem.
5. Admin triggers catalog sync (separate change provides the UI; for now, API endpoint only).

## Open Questions

- None. All decisions finalized in explore session.
