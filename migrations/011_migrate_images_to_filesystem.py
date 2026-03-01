#!/usr/bin/env python3
"""Migration 011: Move card_image_cache BYTEA data to filesystem via ImageStore.

Idempotent: skips if card_image_cache table does not exist.
After migrating all rows, drops the card_image_cache table.
"""
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger


def run(database_url: str = None):
    from sqlalchemy import create_engine, text
    from deckdex.config_loader import load_config
    from deckdex.storage.image_store import FilesystemImageStore

    if not database_url:
        database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set, skipping migration 011")
        return

    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    image_dir = config.catalog.image_dir
    if not os.path.isabs(image_dir):
        image_dir = os.path.join(project_root, image_dir)

    store = FilesystemImageStore(image_dir)
    engine = create_engine(database_url, pool_pre_ping=True)

    with engine.connect() as conn:
        # Check if card_image_cache table exists
        exists = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'card_image_cache')"
        )).scalar()
        if not exists:
            logger.info("card_image_cache table does not exist, skipping migration 011")
            return

        # Count rows
        total = conn.execute(text("SELECT COUNT(*) FROM card_image_cache")).scalar()
        logger.info(f"Migrating {total} images from card_image_cache to filesystem")

        # Iterate and write to filesystem
        migrated = 0
        rows = conn.execute(text(
            "SELECT scryfall_id, content_type, data FROM card_image_cache"
        ))
        for row in rows:
            scryfall_id, content_type, data = row[0], row[1], row[2]
            if not scryfall_id or not data:
                continue
            if store.exists(scryfall_id):
                migrated += 1
                continue
            try:
                store.put(scryfall_id, bytes(data), content_type or "image/jpeg")
                migrated += 1
            except Exception as e:
                logger.warning(f"Failed to migrate image {scryfall_id}: {e}")

        logger.info(f"Migrated {migrated}/{total} images to filesystem")

        # Drop the table
        conn.execute(text("DROP TABLE IF EXISTS card_image_cache"))
        conn.commit()
        logger.info("Dropped card_image_cache table")


if __name__ == "__main__":
    run()
