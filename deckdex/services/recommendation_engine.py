"""Recommendation engine: compute deck card suggestions from a new Scryfall set."""

import statistics
from collections import Counter
from typing import Any, Dict, List, Optional

from loguru import logger


class RecommendationEngine:
    """Computes card suggestions for a deck based on a newly released set."""

    def __init__(self, deck_repo: Any, suggestion_repo: Any) -> None:
        self._deck_repo = deck_repo
        self._suggestion_repo = suggestion_repo

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_suggestions_for_deck(
        self,
        deck_id: int,
        user_id: int,
        new_cards: List[Dict[str, Any]],
        set_code: str,
        set_name: str,
    ) -> List[Dict[str, Any]]:
        """Compute and return up to 5 suggestion dicts for a deck, sorted by score DESC."""
        deck = self._deck_repo.get_deck_with_cards(deck_id, user_id)
        if deck is None:
            return []

        cards = deck.get("cards", [])

        # --- Derive deck properties ---
        commander_color_identity = _compute_commander_color_identity(cards)
        deck_card_types = _compute_deck_card_types(cards)
        deck_median_cmc = _compute_deck_median_cmc(cards)
        deck_card_count = sum(
            1
            for c in cards
            if not _is_land(c.get("type_line", "") or "")
            and not c.get("is_commander", False)
        )
        existing_scryfall_ids = _collect_existing_scryfall_ids(cards)

        # --- Score each candidate ---
        candidates: List[tuple] = []
        for card in new_cards:
            card_color_identity = _parse_color_identity(card.get("color_identity") or "")
            # Filter: color identity must be subset of commander's
            if card_color_identity and not card_color_identity.issubset(commander_color_identity):
                continue
            # Filter: skip cards already in deck
            card_scryfall_id = card.get("scryfall_id") or card.get("id") or ""
            if card_scryfall_id and card_scryfall_id in existing_scryfall_ids:
                continue

            score, reason = _score_card(
                card=card,
                deck_card_types=deck_card_types,
                deck_card_count=deck_card_count,
                deck_median_cmc=deck_median_cmc,
            )

            # Build suggestion dict
            suggestion: Dict[str, Any] = {
                "deck_id": deck_id,
                "user_id": user_id,
                "set_code": set_code,
                "scryfall_id": card_scryfall_id,
                "card_name": card.get("name", ""),
                "mana_cost": card.get("mana_cost"),
                "cmc": card.get("cmc"),
                "type_line": card.get("type_line"),
                "color_identity": card.get("color_identity"),
                "oracle_text": card.get("oracle_text"),
                "reason": reason,
                "score": round(score, 4),
                "image_uri": _extract_image_uri(card),
            }
            candidates.append((score, suggestion))

        # Sort descending by score, keep top 5
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in candidates[:5]]


# ---------------------------------------------------------------------------
# Module-level function (called by the poller for all decks)
# ---------------------------------------------------------------------------


def compute_suggestions_for_all_decks(
    engine: Any,
    suggestion_repo: Any,
    deck_repo: Any,
    new_cards: List[Dict[str, Any]],
    set_code: str,
    set_name: str,
) -> int:
    """Compute and upsert suggestions for every deck in the database.

    Queries distinct (deck_id, user_id) pairs from the decks table, runs the
    engine for each, and bulk-upserts results.  Returns the total number of
    suggestion rows inserted/updated.
    """
    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id AS deck_id, user_id FROM decks WHERE user_id IS NOT NULL")).fetchall()

    if not rows:
        return 0

    engine_obj = RecommendationEngine(deck_repo=deck_repo, suggestion_repo=suggestion_repo)
    total = 0
    for row in rows:
        deck_id = row[0]
        user_id = row[1]
        if user_id is None:
            continue
        try:
            suggestions = engine_obj.compute_suggestions_for_deck(
                deck_id=deck_id,
                user_id=user_id,
                new_cards=new_cards,
                set_code=set_code,
                set_name=set_name,
            )
            if suggestions:
                suggestion_repo.upsert_suggestions(suggestions)
                total += len(suggestions)
        except Exception as exc:
            logger.error(f"Failed to compute suggestions for deck {deck_id} (user {user_id}): {exc}")

    return total


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_color_identity(color_identity_str: str) -> set:
    """Parse a comma-separated color identity string into a set of color letters."""
    if not color_identity_str:
        return set()
    return {c.strip().upper() for c in color_identity_str.split(",") if c.strip()}


def _compute_commander_color_identity(cards: List[Dict[str, Any]]) -> set:
    """Return color identity set from the commander; union of all if no commander."""
    commander_cards = [c for c in cards if c.get("is_commander")]
    if commander_cards:
        commander = commander_cards[0]
        return _parse_color_identity(commander.get("color_identity") or "")
    # No commander: union of all cards
    result: set = set()
    for c in cards:
        result |= _parse_color_identity(c.get("color_identity") or "")
    return result


def _is_land(type_line: str) -> bool:
    return "land" in type_line.lower()


def _compute_deck_card_types(cards: List[Dict[str, Any]]) -> Counter:
    """Count type tokens for non-land cards."""
    counter: Counter = Counter()
    for c in cards:
        type_line = c.get("type_line") or ""
        if _is_land(type_line):
            continue
        for token in type_line.replace("—", "").split():
            if token.strip():
                counter[token.strip()] += 1
    return counter


def _compute_deck_median_cmc(cards: List[Dict[str, Any]]) -> float:
    """Return median CMC of non-land, non-commander cards; default 3.0 if empty."""
    cmcs = []
    for c in cards:
        if c.get("is_commander"):
            continue
        type_line = c.get("type_line") or ""
        if _is_land(type_line):
            continue
        cmc = c.get("cmc")
        if cmc is not None:
            try:
                cmcs.append(float(cmc))
            except (TypeError, ValueError):
                pass
    return statistics.median(cmcs) if cmcs else 3.0


def _collect_existing_scryfall_ids(cards: List[Dict[str, Any]]) -> set:
    """Collect all non-empty scryfall_id values from deck cards."""
    result = set()
    for c in cards:
        sid = c.get("scryfall_id")
        if sid:
            result.add(sid)
    return result


def _extract_image_uri(card: Dict[str, Any]) -> Optional[str]:
    """Extract the normal image URI from a Scryfall card object."""
    image_uris = card.get("image_uris")
    if isinstance(image_uris, dict):
        return image_uris.get("normal")
    return None


def _score_card(
    card: Dict[str, Any],
    deck_card_types: Counter,
    deck_card_count: int,
    deck_median_cmc: float,
) -> tuple:
    """Compute (score, reason) for a candidate card.

    Score breakdown:
      type_match_bonus:  sum of deck type frequencies for matching tokens,
                         normalised by deck_card_count, capped at 0.6.
      cmc_proximity_bonus: max(0, 0.3 - 0.1 * |card_cmc - deck_median_cmc|)
      rarity_bonus:      mythic=0.1, rare=0.07, uncommon=0.03, common=0.0
    """
    type_line = card.get("type_line") or ""
    card_cmc = card.get("cmc")
    rarity = (card.get("rarity") or "").lower()

    # Type match bonus
    type_match = 0.0
    if deck_card_count > 0:
        matched_count = 0
        for token in type_line.replace("—", "").split():
            token = token.strip()
            if token in deck_card_types:
                matched_count += deck_card_types[token]
        type_match = min(0.6, matched_count / deck_card_count)

    # CMC proximity bonus
    cmc_bonus = 0.0
    if card_cmc is not None:
        try:
            cmc_bonus = max(0.0, 0.3 - 0.1 * abs(float(card_cmc) - deck_median_cmc))
        except (TypeError, ValueError):
            cmc_bonus = 0.0

    # Rarity bonus
    rarity_bonus = {"mythic": 0.1, "rare": 0.07, "uncommon": 0.03}.get(rarity, 0.0)

    score = type_match + cmc_bonus + rarity_bonus

    # Determine reason from dominant factor
    reason = _build_reason(
        type_match=type_match,
        cmc_bonus=cmc_bonus,
        deck_median_cmc=deck_median_cmc,
        type_line=type_line,
        deck_card_types=deck_card_types,
    )

    return score, reason


def _build_reason(
    type_match: float,
    cmc_bonus: float,
    deck_median_cmc: float,
    type_line: str,
    deck_card_types: Counter,
) -> str:
    """Build a human-readable reason string from scoring factors."""
    dominant_type = deck_card_types.most_common(1)[0][0] if deck_card_types else "card"
    dominant_count = deck_card_types.most_common(1)[0][1] if deck_card_types else 0

    has_type_match = type_match >= 0.1
    has_cmc_match = cmc_bonus >= 0.1

    if has_type_match and has_cmc_match:
        card_type_tokens = [t.strip() for t in type_line.replace("—", "").split() if t.strip()]
        primary = next((t for t in card_type_tokens if t in deck_card_types), dominant_type)
        return f"{primary} that fits your mana curve (median CMC {deck_median_cmc:.1f})"
    elif has_type_match:
        return f"Matches your heavy {dominant_type} base ({dominant_count} {dominant_type.lower()}s)"
    elif has_cmc_match:
        return f"Fits your mana curve (median CMC {deck_median_cmc:.1f})"
    else:
        return "Fits your deck's color identity"
