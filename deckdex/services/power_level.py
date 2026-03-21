"""
Heuristic power level estimation for Commander decks.

Pure computation — no I/O, no database access.
Input: list of card dicts as returned by DeckRepository.get_deck_with_cards() → deck["cards"]
  Relevant keys: name, description (oracle text), type (type_line), cmc, edhrec_rank, quantity, is_commander
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Curated card sets (all lowercase)
# ---------------------------------------------------------------------------

FAST_MANA: frozenset[str] = frozenset(
    {
        "sol ring",
        "mana crypt",
        "mana vault",
        "chrome mox",
        "mox diamond",
        "mox opal",
        "lotus petal",
        "dark ritual",
        "cabal ritual",
        "elvish spirit guide",
        "simian spirit guide",
        "ancient tomb",
        "gaea's cradle",
        "serra's sanctum",
        "mishra's workshop",
        "jeweled lotus",
        "lotus bloom",
        "mox amber",
        "mana drain",
        "dockside extortionist",
        "vault of whispers",
        "seat of the synod",
        "tree of tales",
        "great furnace",
        "ancient den",
        "darksteel citadel",
    }
)

COMBO_PIECES: frozenset[str] = frozenset(
    {
        "thassa's oracle",
        "demonic consultation",
        "tainted pact",
        "laboratory maniac",
        "jace, wielder of mysteries",
        "isochron scepter",
        "dramatic reversal",
        "staff of domination",
        "umbral mantle",
        "sword of the paruns",
        "basalt monolith",
        "rings of brighthearth",
        "splinter twin",
        "kiki-jiki, mirror breaker",
        "devoted druid",
        "vizier of remedies",
        "heliod, sun-crowned",
        "walking ballista",
        "necropotence",
        "ad nauseam",
    }
)

PREMIUM_LANDS: frozenset[str] = frozenset(
    {
        # Original dual lands
        "tundra",
        "underground sea",
        "badlands",
        "taiga",
        "savannah",
        "scrubland",
        "volcanic island",
        "bayou",
        "plateau",
        "tropical island",
        # Shock lands
        "hallowed fountain",
        "watery grave",
        "blood crypt",
        "stomping ground",
        "temple garden",
        "godless shrine",
        "steam vents",
        "overgrown tomb",
        "sacred foundry",
        "breeding pool",
        # Fetch lands (Onslaught + Zendikar cycles)
        "flooded strand",
        "polluted delta",
        "bloodstained mire",
        "wooded foothills",
        "windswept heath",
        "marsh flats",
        "scalding tarn",
        "verdant catacombs",
        "arid mesa",
        "misty rainforest",
        # Zendikar battle lands
        "prairie stream",
        "sunken hollow",
        "smoldering marsh",
        "cinder glade",
        "canopy vista",
        "shambling vent",
        "wandering fumarole",
        "needle spires",
        "hissing quagmire",
        "lumbering falls",
    }
)

# ---------------------------------------------------------------------------
# Bracket mapping
# ---------------------------------------------------------------------------

_BRACKET_THRESHOLDS = [(8.0, 4), (6.0, 3), (4.0, 2)]


def _compute_bracket(score: float) -> int:
    for threshold, bracket in _BRACKET_THRESHOLDS:
        if score >= threshold:
            return bracket
    return 1


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class FactorBreakdown(BaseModel):
    fast_mana: float
    tutors: float
    combo_pieces: float
    avg_cmc: float
    land_quality: float
    staple_density: float


class PowerLevelResult(BaseModel):
    score: float
    bracket: int
    summary: str
    breakdown: FactorBreakdown


# ---------------------------------------------------------------------------
# Individual signal scorers
# ---------------------------------------------------------------------------


def _score_fast_mana(cards: list[dict[str, Any]]) -> float:
    count = sum(1 for c in cards if str(c.get("name", "")).lower() in FAST_MANA)
    return min(count / 4.0, 1.0)


def _score_tutors(cards: list[dict[str, Any]]) -> float:
    count = sum(1 for c in cards if "search your library" in str(c.get("description", "")).lower())
    return min(count / 5.0, 1.0)


def _score_combo_pieces(cards: list[dict[str, Any]]) -> float:
    count = sum(
        1
        for c in cards
        if (str(c.get("name", "")).lower() in COMBO_PIECES or "infinite" in str(c.get("description", "")).lower())
    )
    return min(count / 3.0, 1.0)


def _score_avg_cmc(cards: list[dict[str, Any]]) -> float:
    non_lands = [c for c in cards if "land" not in str(c.get("type", "")).lower()]
    if not non_lands:
        return 0.5
    total_cmc = sum(float(c.get("cmc") or 0) * int(c.get("quantity") or 1) for c in non_lands)
    count = sum(int(c.get("quantity") or 1) for c in non_lands)
    avg = total_cmc / count if count > 0 else 3.5
    if avg <= 1.5:
        return 1.0
    elif avg <= 2.0:
        return 0.85
    elif avg <= 2.5:
        return 0.70
    elif avg <= 3.0:
        return 0.55
    elif avg <= 3.5:
        return 0.40
    elif avg <= 4.0:
        return 0.25
    else:
        return 0.10


def _score_land_quality(cards: list[dict[str, Any]]) -> float:
    count = sum(1 for c in cards if str(c.get("name", "")).lower() in PREMIUM_LANDS)
    return min(count / 10.0, 1.0)


def _score_staple_density(cards: list[dict[str, Any]]) -> float:
    """Cards with EDHREC rank <= 50 are considered high-impact staples."""
    count = 0
    for c in cards:
        rank = c.get("edhrec_rank")
        if rank is not None:
            try:
                if int(rank) <= 50:
                    count += 1
            except (ValueError, TypeError):
                pass
    return min(count / 10.0, 1.0)


# ---------------------------------------------------------------------------
# Summary string builder
# ---------------------------------------------------------------------------

_POWER_ADJECTIVES = {
    (1, 3): "casual",
    (4, 5): "mid-power",
    (6, 7): "strong",
    (8, 10): "highly optimised",
}

_FACTOR_LABELS = {
    "fast_mana": "fast mana",
    "tutors": "tutors",
    "combo_pieces": "combo pieces",
    "avg_cmc": "low curve",
    "land_quality": "premium mana base",
    "staple_density": "high-impact staples",
}


def _build_summary(score: float, breakdown: FactorBreakdown) -> str:
    score_int = round(score)
    adjective = "mid-power"
    for (lo, hi), adj in _POWER_ADJECTIVES.items():
        if lo <= score_int <= hi:
            adjective = adj
            break

    scores_dict = breakdown.model_dump()
    positives = [_FACTOR_LABELS[k] for k, v in scores_dict.items() if v >= 0.7]
    absences = [_FACTOR_LABELS[k] for k, v in scores_dict.items() if v == 0.0]

    parts = [f"{score_int} \u2014 {adjective} deck"]
    if positives:
        parts.append(f"with {', '.join(positives[:2])}")
    if absences:
        parts.append(f"but no {absences[0]}")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "fast_mana": 2.5,
    "tutors": 2.0,
    "combo_pieces": 2.0,
    "avg_cmc": 1.5,
    "land_quality": 1.0,
    "staple_density": 1.0,
}
_TOTAL_WEIGHT = sum(_WEIGHTS.values())  # 10.0


def estimate_power_level(cards: list[dict[str, Any]]) -> PowerLevelResult:
    """Compute a heuristic power level score for a Commander deck.

    Args:
        cards: List of card dicts from DeckRepository.get_deck_with_cards().
               Keys used: name, description, type, cmc, edhrec_rank, quantity.

    Returns:
        PowerLevelResult with score (1–10), bracket (1–4), summary, and breakdown.
    """
    if not cards:
        breakdown = FactorBreakdown(
            fast_mana=0.0,
            tutors=0.0,
            combo_pieces=0.0,
            avg_cmc=0.5,
            land_quality=0.0,
            staple_density=0.0,
        )
        return PowerLevelResult(score=1.0, bracket=1, summary="1 \u2014 no cards in deck", breakdown=breakdown)

    breakdown = FactorBreakdown(
        fast_mana=_score_fast_mana(cards),
        tutors=_score_tutors(cards),
        combo_pieces=_score_combo_pieces(cards),
        avg_cmc=_score_avg_cmc(cards),
        land_quality=_score_land_quality(cards),
        staple_density=_score_staple_density(cards),
    )

    scores_dict = breakdown.model_dump()
    raw = sum(_WEIGHTS[k] * scores_dict[k] for k in _WEIGHTS) / _TOTAL_WEIGHT
    score = round(max(1.0, min(10.0, raw * 10)), 1)
    bracket = _compute_bracket(score)
    summary = _build_summary(score, breakdown)

    return PowerLevelResult(score=score, bracket=bracket, summary=summary, breakdown=breakdown)
