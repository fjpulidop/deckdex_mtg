"""Caching service layer for deck power level estimation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from deckdex.services.power_level import PowerLevelResult, estimate_power_level
from deckdex.storage.deck_repository import DeckRepository

_cache: dict[tuple, tuple[PowerLevelResult, datetime]] = {}
_CACHE_TTL_SECONDS = 300


def _cache_key(deck: dict, user_id: int) -> tuple:
    return (
        deck["id"],
        user_id,
        len(deck.get("cards", [])),
        deck.get("updated_at", ""),
    )


def get_power_level(deck_id: int, repo: DeckRepository, user_id: int) -> Optional[PowerLevelResult]:
    """Return cached or freshly computed power level for a deck.

    Returns None if the deck does not exist or does not belong to the user.
    """
    deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
    if deck is None:
        return None

    key = _cache_key(deck, user_id)
    now = datetime.now(tz=timezone.utc)

    if key in _cache:
        result, cached_at = _cache[key]
        if (now - cached_at).total_seconds() < _CACHE_TTL_SECONDS:
            return result

    result = estimate_power_level(deck.get("cards", []))
    _cache[key] = (result, now)
    return result
