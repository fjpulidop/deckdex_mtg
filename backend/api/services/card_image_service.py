"""
Card image service: resolve card image by id, using a global cache keyed by scryfall_id.
On cache miss, fetch from Scryfall, persist scryfall_id to cards row, store in global cache.
"""
import os
import sys
from typing import Tuple

# Project root for default data path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
from loguru import logger

from deckdex.config_loader import load_config
from deckdex.card_fetcher import CardFetcher


def get_card_image(card_id: int) -> Tuple[bytes, str]:
    """
    Return (image_bytes, content_type) for the given card id.

    Lookup flow:
      1. Resolve card row to get name + scryfall_id.
      2. If scryfall_id known: check global cache → return if hit.
      3. Fetch from Scryfall by name to obtain scryfall_id and image URL.
      4. Persist scryfall_id to cards row (lazy population).
      5. Check global cache again (another user may have just populated it).
      6. Download image, store in global cache, return.

    Raises FileNotFoundError if card not found or image unavailable.
    """
    from ..dependencies import get_collection_repo

    repo = get_collection_repo()
    if repo is None:
        raise FileNotFoundError("Card images require PostgreSQL (DATABASE_URL)")

    # 1) Resolve card row
    card = repo.get_card_by_id(card_id)
    if not card:
        raise FileNotFoundError(f"Card id {card_id} not found")

    name = (card.get("name") or "").strip()
    if not name:
        raise FileNotFoundError(f"Card id {card_id} has no name")

    scryfall_id = card.get("scryfall_id") or None

    # 2) Cache hit via known scryfall_id
    if scryfall_id:
        try:
            cached = repo.get_card_image_by_scryfall_id(scryfall_id)
            if cached is not None:
                return cached
        except Exception as e:
            logger.warning(f"Failed to read global image cache for scryfall_id={scryfall_id}: {e}")

    # 3) Fetch from Scryfall to get scryfall_id + image URL
    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    fetcher = CardFetcher(config.scryfall, config.openai)

    try:
        scryfall_card = fetcher.search_card(name)
    except Exception as e:
        logger.warning(f"Scryfall lookup failed for '{name}': {e}")
        raise FileNotFoundError(f"Could not fetch image for card '{name}'") from e

    fetched_scryfall_id = scryfall_card.get("id")

    # Single-faced: image_uris at top level; double-faced: use first face
    image_uris = None
    if "card_faces" in scryfall_card and scryfall_card["card_faces"]:
        first_face = scryfall_card["card_faces"][0]
        image_uris = first_face.get("image_uris") if isinstance(first_face, dict) else None
    if not image_uris:
        image_uris = scryfall_card.get("image_uris") or {}
    image_url = image_uris.get("normal") or image_uris.get("large")
    if not image_url:
        raise FileNotFoundError(f"No image URL for card '{name}'")

    # 4) Persist scryfall_id to cards row (lazy)
    if fetched_scryfall_id and fetched_scryfall_id != scryfall_id:
        try:
            repo.update_card_scryfall_id(card_id, fetched_scryfall_id)
            scryfall_id = fetched_scryfall_id
        except Exception as e:
            logger.warning(f"Failed to persist scryfall_id for card_id={card_id}: {e}")
            scryfall_id = fetched_scryfall_id

    # 5) Check global cache again (race condition guard)
    if scryfall_id:
        try:
            cached = repo.get_card_image_by_scryfall_id(scryfall_id)
            if cached is not None:
                return cached
        except Exception as e:
            logger.warning(f"Failed to read global image cache (second check) for scryfall_id={scryfall_id}: {e}")

    # 6) Download and store in global cache
    try:
        resp = requests.get(image_url, timeout=config.scryfall.timeout)
        resp.raise_for_status()
        data = resp.content
    except Exception as e:
        logger.warning(f"Failed to download image from Scryfall: {e}")
        raise FileNotFoundError(f"Could not download image for '{name}'") from e

    content_type = "image/jpeg"
    if scryfall_id:
        try:
            repo.save_card_image_to_global_cache(scryfall_id, content_type, data)
        except Exception as e:
            logger.warning(f"Failed to save image to global cache for scryfall_id={scryfall_id}: {e}")

    return data, content_type
