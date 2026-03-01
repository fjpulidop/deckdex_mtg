"""Catalog sync job: download Scryfall bulk data and card images."""

import json
import time
from typing import Callable, Optional

import requests
from loguru import logger

from deckdex.catalog.repository import CatalogRepository
from deckdex.storage.image_store import ImageStore


# Scryfall TOS: at least 50-100ms between requests
_IMAGE_DELAY_SECONDS = 0.1
_IMAGE_RETRIES = 3
_UPSERT_BATCH_SIZE = 1000
_IMAGE_BATCH_SIZE = 100

# Type for progress callback: (phase, current, total)
ProgressCallback = Callable[[str, int, int], None]


class CatalogSyncJob:
    """Two-phase catalog sync: bulk data download then image download.

    Phase 1 (data):  download Scryfall bulk JSON → UPSERT into catalog_cards.
    Phase 2 (images): iterate pending images, download to ImageStore, cursor-based resume.
    """

    def __init__(
        self,
        catalog_repo: CatalogRepository,
        image_store: ImageStore,
        bulk_data_url: str = "https://api.scryfall.com/bulk-data/default-cards",
        image_size: str = "normal",
        on_progress: Optional[ProgressCallback] = None,
    ):
        self._repo = catalog_repo
        self._store = image_store
        self._bulk_url = bulk_data_url
        self._image_size = image_size
        self._on_progress = on_progress
        self._cancelled = False

    def cancel(self):
        """Request cancellation (checked between batches)."""
        self._cancelled = True

    def _emit(self, phase: str, current: int, total: int):
        if self._on_progress:
            try:
                self._on_progress(phase, current, total)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self):
        """Execute the full sync (data + images).  Raises on fatal error."""
        self._cancelled = False
        try:
            self._repo.update_sync_state(status="syncing_data", error_message=None)
            self._sync_data()
            if self._cancelled:
                self._repo.update_sync_state(status="idle")
                return

            self._repo.update_sync_state(status="syncing_images")
            self._sync_images()

            status = "completed" if not self._cancelled else "idle"
            total_cards = self._repo.count_cards()
            total_images = self._repo.count_downloaded_images()
            self._repo.update_sync_state(
                status=status,
                total_cards=total_cards,
                total_images_downloaded=total_images,
            )
        except Exception as e:
            logger.error(f"Catalog sync failed: {e}")
            self._repo.update_sync_state(status="failed", error_message=str(e)[:500])
            raise

    # ------------------------------------------------------------------
    # Phase 1: bulk data
    # ------------------------------------------------------------------

    def _sync_data(self):
        """Download Scryfall bulk JSON and UPSERT all cards."""
        logger.info(f"Phase 1: downloading bulk data from {self._bulk_url}")

        # Step 1: get the download URI from the bulk-data endpoint
        resp = requests.get(self._bulk_url, timeout=30)
        resp.raise_for_status()
        meta = resp.json()
        download_uri = meta.get("download_uri")
        if not download_uri:
            raise RuntimeError("Scryfall bulk-data response missing download_uri")

        # Step 2: stream-download the actual JSON file
        logger.info(f"Downloading bulk file from {download_uri}")
        resp = requests.get(download_uri, timeout=300, stream=True)
        resp.raise_for_status()

        # Read the full JSON (typically ~200MB)
        raw = resp.content
        cards_json = json.loads(raw)
        total = len(cards_json)
        logger.info(f"Parsed {total} cards from bulk data")

        # Step 3: batch UPSERT
        batch = []
        for i, card in enumerate(cards_json):
            if self._cancelled:
                return
            parsed = self._parse_scryfall_card(card)
            if parsed:
                batch.append(parsed)
            if len(batch) >= _UPSERT_BATCH_SIZE:
                self._repo.upsert_cards(batch)
                batch.clear()
                if (i + 1) % (_UPSERT_BATCH_SIZE * 10) == 0:
                    self._emit("data", i + 1, total)

        if batch:
            self._repo.upsert_cards(batch)

        total_cards = self._repo.count_cards()
        self._repo.update_sync_state(
            last_bulk_sync="NOW()",
            total_cards=total_cards,
        )
        # Fix: update with actual SQL NOW()
        from sqlalchemy import text
        with self._repo._engine().connect() as conn:
            conn.execute(text(
                "UPDATE catalog_sync_state SET last_bulk_sync = NOW() WHERE id = 1"
            ))
            conn.commit()

        self._emit("data", total, total)
        logger.info(f"Phase 1 complete: {total_cards} cards in catalog")

    def _parse_scryfall_card(self, card: dict) -> Optional[dict]:
        """Extract the fields we care about from a Scryfall card object."""
        sid = card.get("id")
        name = card.get("name")
        if not sid or not name:
            return None

        # Image URIs: top-level or first face for double-faced cards
        image_uris = card.get("image_uris") or {}
        if not image_uris and card.get("card_faces"):
            faces = card["card_faces"]
            if faces and isinstance(faces[0], dict):
                image_uris = faces[0].get("image_uris") or {}

        prices = card.get("prices") or {}
        colors = card.get("colors")
        color_identity = card.get("color_identity")
        keywords = card.get("keywords")
        legalities = card.get("legalities")

        return {
            "scryfall_id": sid,
            "oracle_id": card.get("oracle_id"),
            "name": name,
            "type_line": card.get("type_line"),
            "oracle_text": card.get("oracle_text"),
            "mana_cost": card.get("mana_cost"),
            "cmc": card.get("cmc"),
            "colors": ",".join(colors) if isinstance(colors, list) else colors,
            "color_identity": ",".join(color_identity) if isinstance(color_identity, list) else color_identity,
            "power": card.get("power"),
            "toughness": card.get("toughness"),
            "rarity": card.get("rarity"),
            "set_id": card.get("set"),
            "set_name": card.get("set_name"),
            "collector_number": card.get("collector_number"),
            "release_date": card.get("released_at"),
            "image_uri_small": image_uris.get("small"),
            "image_uri_normal": image_uris.get("normal"),
            "image_uri_large": image_uris.get("large"),
            "prices_eur": prices.get("eur"),
            "prices_usd": prices.get("usd"),
            "prices_usd_foil": prices.get("usd_foil"),
            "edhrec_rank": card.get("edhrec_rank"),
            "keywords": ",".join(keywords) if isinstance(keywords, list) else keywords,
            "legalities": json.dumps(legalities) if isinstance(legalities, dict) else legalities,
            "scryfall_uri": card.get("scryfall_uri"),
        }

    # ------------------------------------------------------------------
    # Phase 2: images
    # ------------------------------------------------------------------

    def _sync_images(self):
        """Download pending card images to filesystem, respecting rate limit."""
        state = self._repo.get_sync_state()
        cursor = state.get("last_image_cursor")

        # Count total pending for progress
        from sqlalchemy import text
        with self._repo._engine().connect() as conn:
            total_pending = conn.execute(
                text("SELECT COUNT(*) FROM catalog_cards WHERE image_status = 'pending'")
            ).scalar() or 0
        total_downloaded = state.get("total_images_downloaded") or 0

        logger.info(f"Phase 2: {total_pending} images pending, cursor={cursor}")
        processed = 0

        while not self._cancelled:
            batch = self._repo.get_pending_images(after_cursor=cursor, limit=_IMAGE_BATCH_SIZE)
            if not batch:
                break

            for card in batch:
                if self._cancelled:
                    return

                sid = card["scryfall_id"]
                image_url = card.get(f"image_uri_{self._image_size}") or card.get("image_uri_normal")

                if not image_url:
                    self._repo.update_image_status(sid, "failed")
                    cursor = sid
                    continue

                success = self._download_image(sid, image_url)
                if success:
                    self._repo.update_image_status(sid, "downloaded")
                    total_downloaded += 1
                else:
                    self._repo.update_image_status(sid, "failed")

                cursor = sid
                processed += 1
                self._emit("images", total_downloaded, total_downloaded + total_pending - processed)

                time.sleep(_IMAGE_DELAY_SECONDS)

            # Update cursor after each batch
            self._repo.update_sync_state(
                last_image_cursor=cursor,
                total_images_downloaded=total_downloaded,
            )

        logger.info(f"Phase 2 complete: {total_downloaded} images downloaded")

    def _download_image(self, scryfall_id: str, url: str) -> bool:
        """Download a single image with retries.  Returns True on success."""
        if self._store.exists(scryfall_id):
            return True

        for attempt in range(1, _IMAGE_RETRIES + 1):
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "image/jpeg")
                self._store.put(scryfall_id, resp.content, content_type)
                return True
            except Exception as e:
                if attempt < _IMAGE_RETRIES:
                    time.sleep(0.5 * attempt)
                else:
                    logger.warning(f"Failed to download image {scryfall_id} after {_IMAGE_RETRIES} attempts: {e}")
        return False
