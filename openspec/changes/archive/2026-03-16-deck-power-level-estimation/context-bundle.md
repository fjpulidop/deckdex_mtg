# Context Bundle: Deck Power Level Auto-Estimation

This file collects the exact code context, file paths, and concrete change snippets an implementer needs without having to read the full codebase. Read design.md for the full rationale.

---

## 1. New Files to Create

### `deckdex/services/__init__.py`

Check whether this directory and `__init__.py` exist first. If `deckdex/services/` does not exist:

```bash
mkdir -p deckdex/services
touch deckdex/services/__init__.py
```

### `deckdex/services/power_level.py`

Complete implementation skeleton:

```python
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

FAST_MANA: frozenset[str] = frozenset({
    "sol ring", "mana crypt", "mana vault", "chrome mox", "mox diamond",
    "mox opal", "lotus petal", "dark ritual", "cabal ritual",
    "elvish spirit guide", "simian spirit guide", "ancient tomb",
    "gaea's cradle", "serra's sanctum", "mishra's workshop",
    "jeweled lotus", "lotus bloom", "mox amber",
    "mana drain", "dockside extortionist",
    "vault of whispers", "seat of the synod", "tree of tales",
    "great furnace", "ancient den", "darksteel citadel",
})

COMBO_PIECES: frozenset[str] = frozenset({
    "thassa's oracle", "demonic consultation", "tainted pact",
    "laboratory maniac", "jace, wielder of mysteries",
    "isochron scepter", "dramatic reversal",
    "staff of domination", "umbral mantle", "sword of the paruns",
    "basalt monolith", "rings of brighthearth",
    "splinter twin", "kiki-jiki, mirror breaker",
    "devoted druid", "vizier of remedies",
    "heliod, sun-crowned", "walking ballista",
    "necropotence", "ad nauseam",
})

PREMIUM_LANDS: frozenset[str] = frozenset({
    # Original dual lands
    "tundra", "underground sea", "badlands", "taiga", "savannah",
    "scrubland", "volcanic island", "bayou", "plateau", "tropical island",
    # Shock lands
    "hallowed fountain", "watery grave", "blood crypt", "stomping ground",
    "temple garden", "godless shrine", "steam vents", "overgrown tomb",
    "sacred foundry", "breeding pool",
    # Fetch lands (Onslaught + Zendikar cycles)
    "flooded strand", "polluted delta", "bloodstained mire", "wooded foothills",
    "windswept heath", "marsh flats", "scalding tarn", "verdant catacombs",
    "arid mesa", "misty rainforest",
    # Zendikar battle lands
    "prairie stream", "sunken hollow", "smoldering marsh", "cinder glade",
    "canopy vista", "shambling vent", "wandering fumarole", "needle spires",
    "hissing quagmire", "lumbering falls",
})

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
    count = sum(
        1 for c in cards
        if "search your library" in str(c.get("description", "")).lower()
    )
    return min(count / 5.0, 1.0)


def _score_combo_pieces(cards: list[dict[str, Any]]) -> float:
    count = sum(
        1 for c in cards
        if (
            str(c.get("name", "")).lower() in COMBO_PIECES
            or "infinite" in str(c.get("description", "")).lower()
        )
    )
    return min(count / 3.0, 1.0)


def _score_avg_cmc(cards: list[dict[str, Any]]) -> float:
    non_lands = [
        c for c in cards
        if "land" not in str(c.get("type", "")).lower()
    ]
    if not non_lands:
        return 0.5
    total_cmc = sum(
        float(c.get("cmc") or 0) * int(c.get("quantity") or 1)
        for c in non_lands
    )
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
            fast_mana=0.0, tutors=0.0, combo_pieces=0.0,
            avg_cmc=0.5, land_quality=0.0, staple_density=0.0,
        )
        return PowerLevelResult(score=1.0, bracket=1, summary="1 — no cards in deck", breakdown=breakdown)

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
```

---

### `backend/api/services/power_level_service.py`

```python
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
```

---

## 2. Files to Modify

### `backend/api/routes/decks.py`

**After the existing imports**, add:

```python
# (no new top-level imports needed; power_level_service is imported inside the handler)
```

**After the existing Pydantic models** (after `BatchAddResult`), add:

```python
class PowerLevelBreakdownResponse(BaseModel):
    fast_mana: float
    tutors: float
    combo_pieces: float
    avg_cmc: float
    land_quality: float
    staple_density: float


class PowerLevelResponse(BaseModel):
    score: float
    bracket: int
    summary: str
    breakdown: PowerLevelBreakdownResponse
```

**After the `import_deck_text` route** (end of file), add:

```python
@router.get("/{deck_id}/power-level", response_model=PowerLevelResponse)
async def get_deck_power_level(
    deck_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Return heuristic power level score and Commander Bracket for a deck."""
    from ..services.power_level_service import get_power_level

    result = get_power_level(deck_id, repo, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return result
```

---

### `frontend/src/api/client.ts`

**After `BatchAddResult` interface** (line ~187), insert:

```typescript
export interface PowerLevelBreakdown {
  fast_mana: number;
  tutors: number;
  combo_pieces: number;
  avg_cmc: number;
  land_quality: number;
  staple_density: number;
}

export interface PowerLevelResponse {
  score: number;
  bracket: number;
  summary: string;
  breakdown: PowerLevelBreakdown;
}
```

**Inside the `api` object, after `importDeckText`** (line ~834), insert:

```typescript
  getDeckPowerLevel: async (deckId: number): Promise<PowerLevelResponse> => {
    const response = await apiFetch(`${API_BASE}/decks/${deckId}/power-level`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      if (response.status === 404) throw new Error('Deck not found');
      if (response.status === 501) throw new Error((err as { detail?: string }).detail || 'Decks require Postgres');
      throw new Error((err as { detail?: string }).detail || 'Failed to fetch power level');
    }
    return response.json();
  },
```

---

### `frontend/src/pages/DeckBuilder.tsx` — `DeckCardButton` component

Add `useQuery` import (already imported elsewhere in the file).

**Inside `DeckCardButton`** (after `const { src: commanderImageUrl } = useCardImage(...)`):

```typescript
  const { data: powerLevel } = useQuery({
    queryKey: ['deckPowerLevel', deck.id],
    queryFn: () => api.getDeckPowerLevel(deck.id),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const BRACKET_COLORS: Record<number, string> = {
    1: 'bg-green-600',
    2: 'bg-blue-600',
    3: 'bg-orange-500',
    4: 'bg-red-600',
  };
```

**Inside the returned JSX** (inside the `<button>`, after the card count `<span>`):

```tsx
      {powerLevel && (
        <span
          className={`absolute bottom-2 right-2 z-20 text-white text-xs font-semibold px-1.5 py-0.5 rounded ${BRACKET_COLORS[powerLevel.bracket] ?? 'bg-gray-600'}`}
          title={powerLevel.summary}
        >
          B{powerLevel.bracket} · {powerLevel.score.toFixed(1)}
        </span>
      )}
```

---

### `frontend/src/components/DeckDetailModal.tsx`

**After existing `useQuery` / `useQueryClient` imports**, no new imports needed (already uses `useQuery`).

**After `const [copyFeedback, setCopyFeedback] = useState(false)`** (inside the component body), add:

```typescript
  const { data: powerLevel } = useQuery({
    queryKey: ['deckPowerLevel', deckId],
    queryFn: () => api.getDeckPowerLevel(deckId),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const BRACKET_LABELS: Record<number, string> = {
    1: 'Casual', 2: 'Mid Power', 3: 'High Power', 4: 'Optimised',
  };
  const bracketTextColor = (b: number): string => {
    if (b === 1) return 'text-green-500';
    if (b === 2) return 'text-blue-500';
    if (b === 3) return 'text-orange-500';
    return 'text-red-500';
  };
```

**In the modal header JSX** (after the mana curve `<ResponsiveContainer>` block, before the action buttons), insert:

```tsx
              {powerLevel && (
                <div
                  className="flex flex-col items-center shrink-0 cursor-help px-2"
                  title={powerLevel.summary}
                >
                  <span className={`text-lg font-bold leading-none ${bracketTextColor(powerLevel.bracket)}`}>
                    {powerLevel.score.toFixed(1)}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap mt-0.5">
                    {BRACKET_LABELS[powerLevel.bracket]} · B{powerLevel.bracket}
                  </span>
                </div>
              )}
```

---

## 3. Existing Files — Context Only (No Changes)

| File | Why relevant |
|------|-------------|
| `deckdex/storage/repository.py` | `_row_to_card` defines the dict shape the scoring engine receives; note `"description"` for oracle_text, `"type"` for type_line |
| `deckdex/storage/deck_repository.py` | `get_deck_with_cards` is the data source; no changes needed for core feature |
| `backend/api/dependencies.py` | `get_current_user_id`, `get_deck_repo` — imported as-is in the new endpoint |
| `backend/api/main.py` | No router registration needed; `decks.router` is already included |
| `frontend/src/hooks/useCardImage.ts` | Pattern reference for lazy image fetching inside a tile component |

---

## 4. Card Dict Field Mapping Reference

The `_row_to_card` function in `deckdex/storage/repository.py` maps database columns to these dict keys:

| DB column     | Dict key        | Used in scoring |
|---------------|-----------------|-----------------|
| `name`        | `"name"`        | Yes (fast mana, combos, premium lands) |
| `description` | `"description"` | Yes (tutors, combo oracle text) |
| `type_line`   | `"type"`        | Yes (avg CMC: exclude lands) |
| `cmc`         | `"cmc"`         | Yes |
| `edhrec_rank` | `"edhrec_rank"` | Yes (staple density) |
| `quantity`    | `"quantity"`    | Yes (weighted avg CMC) |
| `is_commander`| `"is_commander"`| No (not used in scoring) |

**Critical**: use `"description"` not `"oracle_text"`, and `"type"` not `"type_line"` when accessing card dicts in `power_level.py`.

---

## 5. Test File Skeleton

### `tests/test_power_level.py`

```python
"""Unit tests for deckdex/services/power_level.py"""
import pytest
from deckdex.services.power_level import (
    estimate_power_level,
    _compute_bracket,
    _build_summary,
    FactorBreakdown,
)


def _card(name: str, description: str = "", type_: str = "Instant", cmc: float = 2.0, edhrec_rank: int = 999) -> dict:
    return {"name": name, "description": description, "type": type_, "cmc": cmc, "edhrec_rank": edhrec_rank, "quantity": 1}


@pytest.fixture()
def empty_deck():
    return []


@pytest.fixture()
def fast_mana_deck():
    return [
        _card("Sol Ring", cmc=1),
        _card("Mana Crypt", cmc=0),
        _card("Mana Vault", cmc=1),
        _card("Chrome Mox", cmc=0),
    ]


@pytest.fixture()
def tutor_deck():
    return [
        _card("Demonic Tutor", description="Search your library for a card"),
        _card("Vampiric Tutor", description="Search your library for a card"),
        _card("Enlightened Tutor", description="Search your library for a card"),
        _card("Imperial Seal", description="Search your library for a card"),
        _card("Mystical Tutor", description="Search your library for a card"),
    ]


class TestEmptyDeck:
    def test_score_is_one(self, empty_deck):
        result = estimate_power_level(empty_deck)
        assert result.score == 1.0

    def test_bracket_is_one(self, empty_deck):
        result = estimate_power_level(empty_deck)
        assert result.bracket == 1


class TestFastMana:
    def test_four_fast_mana_cards_max_factor(self, fast_mana_deck):
        result = estimate_power_level(fast_mana_deck)
        assert result.breakdown.fast_mana == 1.0

    def test_score_elevated(self, fast_mana_deck):
        result = estimate_power_level(fast_mana_deck)
        assert result.score >= 4.0


class TestTutors:
    def test_five_tutors_max_factor(self, tutor_deck):
        result = estimate_power_level(tutor_deck)
        assert result.breakdown.tutors == 1.0


class TestComputeBracket:
    @pytest.mark.parametrize("score,expected", [
        (1.0, 1), (3.0, 1), (3.9, 1),
        (4.0, 2), (5.9, 2),
        (6.0, 3), (7.9, 3),
        (8.0, 4), (10.0, 4),
    ])
    def test_bracket_thresholds(self, score, expected):
        assert _compute_bracket(score) == expected


class TestBuildSummary:
    def test_returns_non_empty_string(self):
        bd = FactorBreakdown(
            fast_mana=0.5, tutors=0.2, combo_pieces=0.0,
            avg_cmc=0.7, land_quality=0.6, staple_density=0.3,
        )
        result = _build_summary(6.5, bd)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_score_appears_in_summary(self):
        bd = FactorBreakdown(
            fast_mana=0.0, tutors=0.0, combo_pieces=0.0,
            avg_cmc=0.5, land_quality=0.0, staple_density=0.0,
        )
        result = _build_summary(3.0, bd)
        assert "3" in result
```
