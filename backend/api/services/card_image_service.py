"""
Card image service: resolve card image by id, with on-demand fetch from Scryfall and filesystem storage.
"""
import os
import sys
from pathlib import Path
from typing import Tuple

# Project root for default data path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
from loguru import logger

from deckdex.config_loader import load_config
from deckdex.card_fetcher import CardFetcher


# Directory for stored card images (default: data/card_images under project root)
def _images_dir() -> Path:
    raw = os.getenv("DECKDEX_CARD_IMAGES_DIR", "").strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = project_root / path
    else:
        path = Path(project_root) / "data" / "card_images"
    return path


def ensure_images_dir() -> Path:
    """Create card images directory if it does not exist. Return the path."""
    d = _images_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_card_image(card_id: int) -> Tuple[bytes, str]:
    """
    Return (image_bytes, content_type) for the given card id.
    If image is already stored, read from filesystem; otherwise fetch from Scryfall, store, then return.
    Raises FileNotFoundError if card not found or image unavailable.
    """
    from ..dependencies import get_collection_repo

    repo = get_collection_repo()
    if repo is None:
        raise FileNotFoundError("Card images require PostgreSQL (DATABASE_URL)")

    card = repo.get_card_by_id(card_id)
    if not card:
        raise FileNotFoundError(f"Card id {card_id} not found")

    name = (card.get("name") or "").strip()
    if not name:
        raise FileNotFoundError(f"Card id {card_id} has no name")

    images_dir = ensure_images_dir()
    path = images_dir / f"{card_id}.jpg"

    if path.exists():
        try:
            data = path.read_bytes()
            return data, "image/jpeg"
        except Exception as e:
            logger.warning(f"Failed to read stored image {path}: {e}")
            # Fall through to re-fetch

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

    try:
        path.write_bytes(data)
    except Exception as e:
        logger.warning(f"Failed to write image to {path}: {e}")
        # Still return the bytes

    return data, "image/jpeg"
