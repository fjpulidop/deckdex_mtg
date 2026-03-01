"""
Scryfall service: card name suggestions (autocomplete) and resolve card by name.

Catalog-first: queries the local catalog first, falls back to Scryfall only
when the user has enabled it in their external API settings.
"""
import os
import sys
from typing import List, Dict, Any, Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger

from deckdex.config_loader import load_config
from deckdex.card_fetcher import CardFetcher


def _get_fetcher() -> CardFetcher:
    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    return CardFetcher(config.scryfall, config.openai)


def _is_scryfall_enabled(user_id: int) -> bool:
    """Check if the user has enabled Scryfall fallback."""
    from ..dependencies import get_user_settings_repo
    repo = get_user_settings_repo()
    if repo is None:
        return False
    settings = repo.get_external_apis_settings(user_id)
    return settings.get("scryfall_enabled", False)


def _get_catalog_repo():
    """Get catalog repo (may be None)."""
    from ..dependencies import get_catalog_repo
    return get_catalog_repo()


def suggest_card_names(q: str, user_id: Optional[int] = None) -> List[str]:
    """
    Return up to 20 card name suggestions.

    1. Search local catalog first.
    2. If catalog has results, return them.
    3. If catalog is empty and Scryfall is enabled for the user, fall back.
    4. Otherwise return empty list.
    """
    if not q or len((q or "").strip()) < 2:
        return []

    q = q.strip()

    # 1. Catalog first
    catalog_repo = _get_catalog_repo()
    if catalog_repo is not None:
        try:
            results = catalog_repo.autocomplete(q, limit=20)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Catalog autocomplete failed for q={q!r}: {e}")

    # 2. Scryfall fallback
    if user_id is not None and _is_scryfall_enabled(user_id):
        try:
            fetcher = _get_fetcher()
            return fetcher.autocomplete(q)
        except Exception as e:
            logger.warning(f"Scryfall suggest failed for q={q!r}: {e}")

    return []


class CardNotFoundError(Exception):
    """Raised when a card name cannot be resolved."""


def _map_catalog_card(card: Dict[str, Any]) -> Dict[str, Any]:
    """Map a catalog_cards row to the internal card payload format."""
    return {
        "name": card.get("name"),
        "type": card.get("type_line"),
        "rarity": card.get("rarity"),
        "set_name": card.get("set_name"),
        "price": card.get("price_usd") or card.get("price_eur"),
        "description": card.get("oracle_text"),
        "mana_cost": card.get("mana_cost"),
        "cmc": card.get("cmc"),
        "power": card.get("power"),
        "toughness": card.get("toughness"),
        "colors": card.get("colors"),
        "color_identity": card.get("color_identity"),
    }


def resolve_card_by_name(
    name: str,
    from_collection: Dict[str, Any] | None = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Return full card payload for create.

    1. Check from_collection (already in user's collection).
    2. Search local catalog.
    3. If not in catalog and Scryfall enabled, fall back to Scryfall.
    4. Otherwise raise CardNotFoundError.
    """
    name = (name or "").strip()
    if not name:
        raise CardNotFoundError("Card name is empty")

    if from_collection and (from_collection.get("name") or "").strip().lower() == name.lower():
        return {k: v for k, v in from_collection.items() if v is not None}

    # Catalog lookup
    catalog_repo = _get_catalog_repo()
    if catalog_repo is not None:
        try:
            results = catalog_repo.search_by_name(name, limit=1)
            if results:
                return _map_catalog_card(results[0])
        except Exception as e:
            logger.warning(f"Catalog search failed for {name!r}: {e}")

    # Scryfall fallback
    if user_id is not None and _is_scryfall_enabled(user_id):
        try:
            fetcher = _get_fetcher()
            scryfall = fetcher.search_card(name)
        except Exception as e:
            logger.warning(f"Scryfall resolve failed for {name!r}: {e}")
            raise CardNotFoundError(f"Card not found: {name}") from e

        card_type = scryfall.get("type_line") or scryfall.get("type")
        prices = scryfall.get("prices") or {}
        price = prices.get("eur") or prices.get("usd") or None
        if price is not None:
            price = str(price)
        colors_raw = scryfall.get("colors")
        color_identity_raw = scryfall.get("color_identity")
        colors = ",".join(colors_raw) if isinstance(colors_raw, list) else colors_raw
        color_identity = ",".join(color_identity_raw) if isinstance(color_identity_raw, list) else color_identity_raw

        return {
            "name": scryfall.get("name"),
            "type": card_type,
            "rarity": scryfall.get("rarity"),
            "set_name": scryfall.get("set_name"),
            "price": price,
            "description": scryfall.get("oracle_text"),
            "mana_cost": scryfall.get("mana_cost"),
            "cmc": scryfall.get("cmc"),
            "power": scryfall.get("power"),
            "toughness": scryfall.get("toughness"),
            "colors": colors,
            "color_identity": color_identity,
        }

    raise CardNotFoundError(
        f"Card not found in catalog: {name}. Enable Scryfall in Settings to search online."
    )
