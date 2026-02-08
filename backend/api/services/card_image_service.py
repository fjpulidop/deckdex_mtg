"""
Card image service: resolve card image by id, with on-demand fetch from Scryfall and database storage.
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
    If image is already stored in the database, return it; otherwise fetch from Scryfall, store in DB, then return.
    Raises FileNotFoundError if card not found or image unavailable.
    """
    from ..dependencies import get_collection_repo

    repo = get_collection_repo()
    if repo is None:
        raise FileNotFoundError("Card images require PostgreSQL (DATABASE_URL)")

    # 1) Try database first
    try:
        stored = repo.get_card_image(card_id)
        if stored is not None:
            return stored
    except Exception as e:
        logger.warning(f"Failed to read card image from DB for card_id={card_id}: {e}")
        # Fall through to fetch from Scryfall

    # 2) Card lookup and Scryfall fetch
    card = repo.get_card_by_id(card_id)
    if not card:
        raise FileNotFoundError(f"Card id {card_id} not found")

    name = (card.get("name") or "").strip()
    if not name:
        raise FileNotFoundError(f"Card id {card_id} has no name")

    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    fetcher = CardFetcher(config.scryfall, config.openai)

    try:
        scryfall_card = fetcher.search_card(name)
    except Exception as e:
        logger.warning(f"Scryfall lookup failed for '{name}': {e}")
        raise FileNotFoundError(f"Could not fetch image for card '{name}'") from e

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

    try:
        resp = requests.get(image_url, timeout=config.scryfall.timeout)
        resp.raise_for_status()
        data = resp.content
    except Exception as e:
        logger.warning(f"Failed to download image from Scryfall: {e}")
        raise FileNotFoundError(f"Could not download image for '{name}'") from e

    content_type = "image/jpeg"
    try:
        repo.save_card_image(card_id, content_type, data)
    except Exception as e:
        logger.warning(f"Failed to save card image to DB for card_id={card_id}: {e}")
        # Still return the bytes

    return data, content_type
