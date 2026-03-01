## 1. ImageStore abstraction and FilesystemImageStore

- [ ] 1.1 Create `deckdex/storage/image_store.py`: `ImageStore` ABC with `get(key)`, `put(key, data, content_type)`, `exists(key)`, `delete(key)`. `FilesystemImageStore` implementation: files at `{base_dir}/{key}.{ext}`, `.meta` JSON sidecar for content_type, atomic writes via temp file + `os.replace`, auto-create base_dir.
- [ ] 1.2 Add `CatalogConfig` dataclass to `deckdex/config.py`: `image_dir` (default `data/images`), `bulk_data_url` (default Scryfall default cards URL), `image_size` (default `normal`). Add to `ProcessorConfig`.
- [ ] 1.3 Update `deckdex/config_loader.py`: load `catalog` section from config.yaml into `CatalogConfig`. Support `DECKDEX_CATALOG_*` env overrides.
- [ ] 1.4 Add `catalog` section to `config.yaml` with defaults for all three profiles.

## 2. Migrate card_image_service to ImageStore

- [ ] 2.1 Update `backend/api/services/card_image_service.py`: replace all `repo.get_card_image_by_scryfall_id()` / `repo.save_card_image_to_global_cache()` calls with `ImageStore.get()` / `ImageStore.put()`. Initialize `FilesystemImageStore` from `CatalogConfig.image_dir`.
- [ ] 2.2 Update `backend/api/dependencies.py`: create and expose a shared `ImageStore` instance (initialized from config).

## 3. Database migrations

- [ ] 3.1 Create `migrations/010_catalog_tables.sql`: `catalog_cards` table (scryfall_id PK, oracle_id, name, type_line, oracle_text, mana_cost, cmc, colors, color_identity, power, toughness, rarity, set_id, set_name, collector_number, release_date, image_uri_small, image_uri_normal, image_uri_large, prices_eur, prices_usd, prices_usd_foil, edhrec_rank, keywords, legalities JSONB, scryfall_uri, image_status TEXT DEFAULT 'pending', synced_at, created_at). Indexes: name, oracle_id, set_id, image_status. `catalog_sync_state` singleton table (id=1 CHECK, last_bulk_sync, last_image_cursor, total_cards, total_images_downloaded, status, error_message, updated_at). Insert initial idle row.
- [ ] 3.2 Create `migrations/011_migrate_images_to_filesystem.py`: Python script that reads all `card_image_cache` rows, writes each to filesystem via ImageStore, then drops `card_image_cache` table. Idempotent (skip if table doesn't exist).

## 4. Catalog repository

- [ ] 4.1 Create `deckdex/catalog/__init__.py` (empty).
- [ ] 4.2 Create `deckdex/catalog/repository.py`: `CatalogRepository` class with PostgreSQL backend. Methods: `search_by_name(query, limit=20)`, `autocomplete(query, limit=20)`, `get_by_scryfall_id(id)`, `upsert_cards(cards: List[Dict])` (batch UPSERT), `get_sync_state()`, `update_sync_state(...)`, `update_image_status(scryfall_id, status)`, `get_pending_images(after_cursor=None, limit=100)`.

## 5. Catalog sync job

- [ ] 5.1 Create `deckdex/catalog/sync_job.py`: `CatalogSyncJob` class. Phase 1: download Scryfall bulk data JSON (stream download, ~200MB), parse entries, batch UPSERT into `catalog_cards` (batches of 1000). Update `catalog_sync_state` with progress. Phase 2: iterate pending images (cursor-based via `get_pending_images`), download each image (normal size) from Scryfall URL in `image_uri_normal`, store via ImageStore, update `image_status`. Respect 100ms rate limit. 3 retries per image with backoff; mark `failed` and continue on persistent failure. Update cursor in `catalog_sync_state` after each batch.
- [ ] 5.2 Add progress callback support: `CatalogSyncJob` accepts a callback function `(phase, current, total)` for WebSocket integration. Emit progress every 100 cards (data phase) or every image (image phase).

## 6. Backend catalog service and routes

- [ ] 6.1 Create `backend/api/services/catalog_service.py`: service layer wrapping `CatalogRepository` and `CatalogSyncJob`. Methods: `search(query, limit)`, `autocomplete(query, limit)`, `get_card(scryfall_id)`, `get_image(scryfall_id)` (via ImageStore), `start_sync()` (launch background thread, create job in `jobs` table, return job_id), `get_sync_status()`.
- [ ] 6.2 Create `backend/api/routes/catalog_routes.py`: `GET /api/catalog/search?q=&limit=`, `GET /api/catalog/autocomplete?q=`, `GET /api/catalog/cards/{scryfall_id}`, `GET /api/catalog/cards/{scryfall_id}/image`, `POST /api/catalog/sync` (returns job_id; 409 if already running), `GET /api/catalog/sync/status`. All endpoints require authentication.
- [ ] 6.3 Register catalog router in `backend/api/main.py`.
- [ ] 6.4 Wire `CatalogRepository` and `ImageStore` in `backend/api/dependencies.py`: create shared instances on startup, expose via dependency injection.

## 7. Tests

- [ ] 7.1 Unit tests for `ImageStore`: test `FilesystemImageStore` put/get/exists/delete, atomic write, auto-create dir, missing key returns None.
- [ ] 7.2 Unit tests for `CatalogRepository`: test search_by_name, autocomplete, upsert_cards, sync_state tracking (mock DB or use test DB if available).
- [ ] 7.3 Unit tests for `CatalogSyncJob`: test bulk data parsing, image download with mock HTTP, cursor resume logic, failure handling.
- [ ] 7.4 Integration tests for catalog routes: test search, autocomplete, get card, get image, trigger sync, sync status.
