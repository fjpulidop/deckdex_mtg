## Why

Every card lookup (autocomplete, resolve, image fetch) currently makes a real-time request to the Scryfall API. This means the app is fully dependent on an external service for basic operations — if Scryfall is slow or down, the app breaks. It also means every user interaction has network latency baked in, and Scryfall's rate limits (100ms between requests) bottleneck bulk operations like import enrichment.

We need a local card catalog that acts as the primary data source, with Scryfall demoted to a sync source (admin-triggered) and optional user fallback.

## What Changes

- New **catalog_cards** table storing all ~400k MTG card printings from Scryfall's bulk data export, with full card metadata.
- New **catalog_sync_state** singleton table tracking sync progress (resumable across restarts).
- New **ImageStore** abstraction replacing PostgreSQL BYTEA storage with filesystem-based image storage (`data/catalog_images/{scryfall_id}.jpg`), designed for future S3 swap.
- Migration of existing `card_image_cache` (BYTEA) to filesystem.
- New **CatalogSyncJob** background job that downloads Scryfall bulk JSON + images, with WebSocket progress reporting and cursor-based resumability.
- New **catalog repository** for local card lookups (search by name, autocomplete, get by scryfall_id).
- New **catalog API routes** for searching the catalog and serving catalog images.
- New **CatalogConfig** in config system for catalog-related settings (image directory, sync options).

## Capabilities

### New Capabilities

- `catalog-system`: Local card catalog backed by PostgreSQL + filesystem images. Bulk sync from Scryfall. Catalog repository for lookups (name search, autocomplete, get by ID). Background sync job with progress tracking.
- `image-store`: Abstract image storage interface (ImageStore ABC) with FilesystemImageStore implementation. Replaces PostgreSQL BYTEA pattern. Prepared for S3ImageStore.

### Modified Capabilities

- `card-image-storage`: Images now served from filesystem via ImageStore instead of PostgreSQL BYTEA. Existing `card_image_cache` table data migrated to filesystem, table eventually dropped.
- `global-image-cache`: Cache is now filesystem-based. Same semantics (shared across users, keyed by scryfall_id) but backed by files instead of BYTEA rows.
- `configuration-management`: New `catalog` section in config.yaml (image_dir, bulk_data_url).

## Impact

- **Database**: New migration for `catalog_cards` and `catalog_sync_state` tables. Migration to move BYTEA images to filesystem and drop `card_image_cache`.
- **Core (deckdex/)**: New `deckdex/catalog/` package (repository, sync_job). New `deckdex/storage/image_store.py`. New `CatalogConfig` dataclass.
- **Backend**: New `catalog_routes.py` and `catalog_service.py`. Modified `card_image_service.py` to use ImageStore. New routes registered in `main.py`.
- **Frontend**: No frontend changes in this change (admin UI and settings toggles are separate changes).
- **Specs**: New `catalog-system` spec. Delta updates to `global-image-cache`, `card-image-storage`, `configuration-management`.
