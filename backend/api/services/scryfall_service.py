"""
Scryfall service: card name suggestions (autocomplete) and resolve card by name for Add card flow.
"""
import os
import sys
from typing import List, Dict, Any

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger

from deckdex.config_loader import load_config
from deckdex.card_fetcher import CardFetcher


def _get_fetcher() -> CardFetcher:
    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))
    return CardFetcher(config.scryfall, config.openai)


def suggest_card_names(q: str) -> List[str]:
    """
    Return up to 20 card names from Scryfall autocomplete.
    Returns empty list if q is missing, too short, or on error.
    """
    if not q or len((q or "").strip()) < 2:
        return []
    try:
        fetcher = _get_fetcher()
        return fetcher.autocomplete(q.strip())
    except Exception as e:
        logger.warning(f"Scryfall suggest failed for q={q!r}: {e}")
        return []


class CardNotFoundError(Exception):
    """Raised when a card name cannot be resolved from Scryfall or collection."""


def resolve_card_by_name(name: str, from_collection: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Return full card payload (name, type, rarity, set_name, price, ...) for create.
    If from_collection is provided and matches the name, return it. Otherwise fetch from Scryfall.
    Raises CardNotFoundError if not found.
    """
    name = (name or "").strip()
    if not name:
        raise CardNotFoundError("Card name is empty")

    if from_collection and (from_collection.get("name") or "").strip().lower() == name.lower():
        return {k: v for k, v in from_collection.items() if v is not None}

    try:
        fetcher = _get_fetcher()
        scryfall = fetcher.search_card(name)
    except Exception as e:
        logger.warning(f"Scryfall resolve failed for {name!r}: {e}")
        raise CardNotFoundError(f"Card not found: {name}") from e

    # Map Scryfall card to our card model (strings; Scryfall uses lists for colors)
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
