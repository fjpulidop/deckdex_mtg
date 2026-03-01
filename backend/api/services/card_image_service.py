"""
Card image service: resolve card image by id, using filesystem ImageStore keyed by scryfall_id.

Catalog-first: checks ImageStore (includes catalog-synced images) before
falling back to Scryfall download (only when the user has enabled Scryfall).
"""
import os
import sys
from typing import Optional, Tuple

# Project root for default data path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
from loguru import logger

from deckdex.config_loader import load_config
from deckdex.card_fetcher import CardFetcher
from deckdex.storage.image_store import ImageStore


def get_card_image(
    card_id: int,
    image_store: ImageStore = None,
    user_id: Optional[int] = None,
) -> Tuple[bytes, str]:
    """
    Return (image_bytes, content_type) for the given card id.

    Lookup flow:
      1. Resolve card row to get name + scryfall_id.
      2. If scryfall_id known: check ImageStore -> return if hit.
      3. If user has Scryfall enabled: fetch from Scryfall, download image, store.
      4. Otherwise raise FileNotFoundError.

    Raises FileNotFoundError if card not found or image unavailable.
    """
    from ..dependencies import get_collection_repo, get_image_store, get_user_settings_repo

    repo = get_collection_repo()
    if repo is None:
        raise FileNotFoundError("Card images require PostgreSQL (DATABASE_URL)")

    if image_store is None:
        image_store = get_image_store()

    # 1) Resolve card row
    card = repo.get_card_by_id(card_id)
    if not card:
        raise FileNotFoundError(f"Card id {card_id} not found")

    name = (card.get("name") or "").strip()
    if not name:
        raise FileNotFoundError(f"Card id {card_id} has no name")

    scryfall_id = card.get("scryfall_id") or None

    # 2) Cache hit via known scryfall_id (filesystem / catalog-synced images)
    if scryfall_id:
        try:
            cached = image_store.get(scryfall_id)
            if cached is not None:
                return cached
        except Exception as e:
            logger.warning(f"Failed to read image store for scryfall_id={scryfall_id}: {e}")

    # 3) Check if Scryfall fallback is allowed for this user
    scryfall_enabled = False
    if user_id is not None:
        settings_repo = get_user_settings_repo()
        if settings_repo is not None:
            settings = settings_repo.get_external_apis_settings(user_id)
            scryfall_enabled = settings.get("scryfall_enabled", False)

    if not scryfall_enabled:
        raise FileNotFoundError(
            f"Image not found in local store for card '{name}'. "
            "Enable Scryfall in Settings to download images online."
        )

    # 4) Fetch from Scryfall to get scryfall_id + image URL
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

    # 5) Persist scryfall_id to cards row (lazy)
    if fetched_scryfall_id and fetched_scryfall_id != scryfall_id:
        try:
            repo.update_card_scryfall_id(card_id, fetched_scryfall_id)
            scryfall_id = fetched_scryfall_id
        except Exception as e:
            logger.warning(f"Failed to persist scryfall_id for card_id={card_id}: {e}")
            scryfall_id = fetched_scryfall_id

    # 6) Check ImageStore again (race condition guard)
    if scryfall_id:
        try:
            cached = image_store.get(scryfall_id)
            if cached is not None:
                return cached
        except Exception as e:
            logger.warning(f"Failed to read image store (second check) for scryfall_id={scryfall_id}: {e}")

    # 7) Download and store via ImageStore
    try:
        resp = requests.get(image_url, timeout=config.scryfall.timeout)
        resp.raise_for_status()
        data = resp.content
    except Exception as e:
        logger.warning(f"Failed to download image from Scryfall: {e}")
        raise FileNotFoundError(f"Could not download image for '{name}'") from e

    content_type = resp.headers.get('content-type', 'image/jpeg')
    if scryfall_id:
        try:
            image_store.put(scryfall_id, data, content_type)
        except Exception as e:
            logger.warning(f"Failed to save image to store for scryfall_id={scryfall_id}: {e}")

    return data, content_type
