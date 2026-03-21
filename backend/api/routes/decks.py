"""
Decks API routes.
Decks require Postgres; returns 501 when DATABASE_URL is not set.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from deckdex.importers.deck_text import parse_deck_text
from deckdex.storage.deck_repository import DeckRepository

from ..dependencies import get_current_user_id, get_deck_repo

router = APIRouter(prefix="/api/decks", tags=["decks"])


def require_deck_repo() -> DeckRepository:
    repo = get_deck_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Decks require Postgres. Set DATABASE_URL to use the deck builder.",
        )
    return repo


# --- Request/Response models ---


class DeckCreate(BaseModel):
    name: Optional[str] = "Unnamed Deck"


class DeckUpdate(BaseModel):
    name: str


class AddCardBody(BaseModel):
    card_id: int
    quantity: Optional[int] = 1
    is_commander: Optional[bool] = False


class PatchDeckCardBody(BaseModel):
    is_commander: Optional[bool] = None


class DeckImportBody(BaseModel):
    text: str


class DeckImportSkippedCard(BaseModel):
    name: str
    quantity: int
    reason: str


class DeckImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    skipped: List[DeckImportSkippedCard]
    deck: Dict[str, Any]


class BatchAddCardsBody(BaseModel):
    card_ids: List[int]


class BatchAddResult(BaseModel):
    added: List[int]
    not_found: List[int]
    deck: Dict[str, Any]


class SnapshotDiffCard(BaseModel):
    card_id: int
    name: str
    quantity: int


class SnapshotDiffQuantityChange(BaseModel):
    card_id: int
    name: str
    old_quantity: int
    new_quantity: int


class SnapshotDiff(BaseModel):
    added: List[SnapshotDiffCard]
    removed: List[SnapshotDiffCard]
    quantity_changed: List[SnapshotDiffQuantityChange]
    commander_changed: Optional[str] = None


class DeckSnapshot(BaseModel):
    id: int
    created_at: str
    created_by: int
    change_summary: str
    diff: SnapshotDiff


class DeckHistoryResponse(BaseModel):
    deck_id: int
    snapshots: List[DeckSnapshot]


# --- Comparison models ---


class DeckManaCurveBucket(BaseModel):
    cmc: str
    count: int


class DeckColorCount(BaseModel):
    color: str
    count: int


class DeckComparisonStats(BaseModel):
    deck_id: int
    deck_name: str
    total_cards: int
    total_value: float
    creature_count: int
    instant_count: int
    mana_curve: List[DeckManaCurveBucket]
    color_distribution: List[DeckColorCount]


class OverlapCard(BaseModel):
    name: str
    card_id: Optional[int]
    mana_cost: Optional[str]
    type: Optional[str]
    price: Optional[str]
    deck_ids: List[int]


class DeckComparisonResponse(BaseModel):
    deck_ids: List[int]
    decks: List[DeckComparisonStats]
    overlap_cards: List[OverlapCard]


# --- Comparison helper functions ---

_WUBRG = ["W", "U", "B", "R", "G"]
_CMC_BUCKETS = ["0", "1", "2", "3", "4", "5", "6", "7+"]


def _parse_price(price: Optional[str]) -> float:
    if not price or price.strip() in ("", "N/A"):
        return 0.0
    try:
        return float(str(price).replace(",", ".").strip())
    except (ValueError, TypeError):
        return 0.0


def _cmc_bucket(cmc: Optional[Any]) -> str:
    if cmc is None:
        return "0"
    try:
        n = int(float(cmc))
        if n >= 7:
            return "7+"
        return str(max(0, n))
    except (ValueError, TypeError):
        return "0"


def _primary_type(type_line: Optional[str]) -> str:
    if not type_line:
        return "Other"
    main = type_line.split("—")[0].split("//")[0]
    words = main.split()
    if "Creature" in words:
        return "Creature"
    if "Instant" in words:
        return "Instant"
    return "Other"


def _compute_deck_stats(deck_id: int, deck_name: str, cards: List[Dict[str, Any]]) -> DeckComparisonStats:
    curve_counts: Dict[str, int] = {b: 0 for b in _CMC_BUCKETS}
    color_totals: Dict[str, int] = {c: 0 for c in _WUBRG}
    colorless_count = 0
    creature_count = 0
    instant_count = 0
    total_value = 0.0
    total_cards = 0

    for card in cards:
        qty = card.get("quantity") or 1
        total_cards += qty
        total_value += _parse_price(card.get("price")) * qty

        bucket = _cmc_bucket(card.get("cmc"))
        curve_counts[bucket] = curve_counts.get(bucket, 0) + qty

        ci = (card.get("color_identity") or "").strip().upper()
        letters = [ch for ch in ci if ch in color_totals]
        if not letters or ci == "C":
            colorless_count += qty
        else:
            for ch in letters:
                color_totals[ch] += qty

        ptype = _primary_type(card.get("type"))
        if ptype == "Creature":
            creature_count += qty
        elif ptype == "Instant":
            instant_count += qty

    mana_curve = [DeckManaCurveBucket(cmc=b, count=curve_counts[b]) for b in _CMC_BUCKETS]
    color_distribution = [DeckColorCount(color=c, count=color_totals[c]) for c in _WUBRG]
    color_distribution.append(DeckColorCount(color="C", count=colorless_count))

    return DeckComparisonStats(
        deck_id=deck_id,
        deck_name=deck_name,
        total_cards=total_cards,
        total_value=total_value,
        creature_count=creature_count,
        instant_count=instant_count,
        mana_curve=mana_curve,
        color_distribution=color_distribution,
    )


def _compute_overlap(decks_cards: Dict[int, List[Dict[str, Any]]]) -> List[OverlapCard]:
    name_map: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for deck_id, cards in decks_cards.items():
        for card in cards:
            key = (card.get("name") or "").lower().strip()
            if not key:
                continue
            if key not in name_map:
                name_map[key] = {}
            if deck_id not in name_map[key]:
                name_map[key][deck_id] = card

    result: List[OverlapCard] = []
    for _name_lower, deck_map in sorted(name_map.items()):
        if len(deck_map) < 2:
            continue
        representative = next(iter(deck_map.values()))
        result.append(
            OverlapCard(
                name=representative.get("name") or _name_lower,
                card_id=representative.get("id"),
                mana_cost=representative.get("mana_cost"),
                type=representative.get("type"),
                price=representative.get("price"),
                deck_ids=list(deck_map.keys()),
            )
        )
    return result


# --- Routes ---


@router.get("/")
async def list_decks(repo: DeckRepository = Depends(require_deck_repo), user_id: int = Depends(get_current_user_id)):
    """List all decks (id, name, created_at, updated_at, card_count)."""
    return repo.list_all(user_id=user_id)


@router.post("/", status_code=201)
async def create_deck(
    body: DeckCreate, repo: DeckRepository = Depends(require_deck_repo), user_id: int = Depends(get_current_user_id)
):
    """Create a new deck. Returns created deck."""
    return repo.create(name=body.name or "Unnamed Deck", user_id=user_id)


@router.get("/compare", response_model=DeckComparisonResponse)
async def compare_decks(
    ids: str = Query(..., description="Comma-separated deck IDs (2-4)"),
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Compare 2–4 decks side by side: per-deck stats and overlapping cards."""
    try:
        parsed_ids = [int(part.strip()) for part in ids.split(",") if part.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="ids must be comma-separated integers")

    if len(parsed_ids) < 2 or len(parsed_ids) > 4:
        raise HTTPException(status_code=400, detail="Select between 2 and 4 decks")

    seen: set = set()
    unique_ids: List[int] = []
    for did in parsed_ids:
        if did not in seen:
            seen.add(did)
            unique_ids.append(did)

    decks_data: Dict[int, Dict[str, Any]] = {}
    for deck_id in unique_ids:
        deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
        if deck is None:
            raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found")
        decks_data[deck_id] = deck

    stats_list: List[DeckComparisonStats] = []
    decks_cards: Dict[int, List[Dict[str, Any]]] = {}
    for deck_id, deck in decks_data.items():
        cards = deck.get("cards") or []
        decks_cards[deck_id] = cards
        stats_list.append(_compute_deck_stats(deck_id, deck.get("name") or "", cards))

    overlap = _compute_overlap(decks_cards)

    return DeckComparisonResponse(
        deck_ids=unique_ids,
        decks=stats_list,
        overlap_cards=overlap,
    )


@router.get("/{deck_id}")
async def get_deck(
    deck_id: int, repo: DeckRepository = Depends(require_deck_repo), user_id: int = Depends(get_current_user_id)
):
    """Get a single deck with full card list (cards with full payload for UI)."""
    deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.patch("/{deck_id}")
async def update_deck(
    deck_id: int,
    body: DeckUpdate,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Update deck name."""
    deck = repo.update_name(deck_id, body.name, user_id=user_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.delete("/{deck_id}", status_code=204)
async def delete_deck(
    deck_id: int, repo: DeckRepository = Depends(require_deck_repo), user_id: int = Depends(get_current_user_id)
):
    """Delete deck and all its deck_cards."""
    if not repo.delete(deck_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="Deck not found")


@router.post("/{deck_id}/cards", status_code=201)
async def add_card_to_deck(
    deck_id: int,
    body: AddCardBody,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Add a card from the collection to the deck. Card must exist in collection."""
    # Ensure deck exists
    if repo.get_by_id(deck_id, user_id=user_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if not repo.add_card(
        deck_id, body.card_id, quantity=body.quantity or 1, is_commander=body.is_commander or False, user_id=user_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Card not found in collection. Add the card to your collection first.",
        )
    deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
    return deck


@router.post("/{deck_id}/cards/batch", status_code=200)
async def add_cards_to_deck_batch(
    deck_id: int,
    body: BatchAddCardsBody,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Add multiple collection cards to a deck in one request.

    Returns added/not_found id lists and the updated deck.
    Only returns 404 if the deck itself is missing; individual missing
    card IDs are reported in not_found (HTTP 200).
    """
    if not body.card_ids:
        deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
        if deck is None:
            raise HTTPException(status_code=404, detail="Deck not found")
        return {"added": [], "not_found": [], "deck": deck}

    if repo.get_by_id(deck_id, user_id=user_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")

    result = repo.add_cards_batch(deck_id, body.card_ids, user_id=user_id)
    deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
    return {"added": result["added"], "not_found": result["not_found"], "deck": deck}


@router.patch("/{deck_id}/cards/{card_id}")
async def patch_deck_card(
    deck_id: int,
    card_id: int,
    body: PatchDeckCardBody,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Update deck card (e.g. set as commander). When is_commander=true, unsets any other commander."""
    if body.is_commander is True:
        if not repo.set_commander(deck_id, card_id, user_id=user_id):
            raise HTTPException(status_code=404, detail="Deck or card in deck not found")
        deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
        return deck
    raise HTTPException(status_code=400, detail="Only is_commander=true is supported")


@router.delete("/{deck_id}/cards/{card_id}", status_code=204)
async def remove_card_from_deck(
    deck_id: int,
    card_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Remove one card from the deck."""
    if not repo.remove_card(deck_id, card_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="Deck or card in deck not found")


@router.post("/{deck_id}/import", response_model=DeckImportResponse)
async def import_deck_text(
    deck_id: int,
    body: DeckImportBody,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Import cards into a deck from MTGO-style plain text.

    Parses the text, resolves card names against the user's own collection via
    case-insensitive exact match, adds matched cards to the deck (preserving
    quantity and commander status), and returns a summary of matched and skipped
    cards along with the updated deck.
    """
    # Verify the deck exists and belongs to the authenticated user
    if repo.get_by_id(deck_id, user_id=user_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Parse the raw deck list text
    parsed_cards = parse_deck_text(body.text)
    if not parsed_cards:
        deck = repo.get_deck_with_cards(deck_id, user_id=user_id)
        return DeckImportResponse(
            imported_count=0,
            skipped_count=0,
            skipped=[],
            deck=deck,
        )

    # Resolve all unique card names in a single query
    unique_names = list({card["name"].lower() for card in parsed_cards})
    name_to_id = repo.find_card_ids_by_names(unique_names, user_id=user_id)

    imported_count = 0
    skipped: List[DeckImportSkippedCard] = []
    cards_to_import = []

    for card in parsed_cards:
        lower_name = card["name"].lower()
        card_id = name_to_id.get(lower_name)

        if card_id is None:
            skipped.append(
                DeckImportSkippedCard(
                    name=card["name"],
                    quantity=card["quantity"],
                    reason="not_in_collection",
                )
            )
            continue

        cards_to_import.append(
            {
                "card_id": card_id,
                "quantity": card["quantity"],
                "is_commander": card["is_commander"],
            }
        )
        imported_count += 1

    repo.add_cards_from_import(
        deck_id,
        cards_to_import,
        user_id=user_id,
        imported_count=imported_count,
    )

    # Fetch the updated deck to return in the response
    updated_deck = repo.get_deck_with_cards(deck_id, user_id=user_id)

    return DeckImportResponse(
        imported_count=imported_count,
        skipped_count=len(skipped),
        skipped=skipped,
        deck=updated_deck,
    )


@router.get("/{deck_id}/history", response_model=DeckHistoryResponse)
async def get_deck_history(
    deck_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Return the snapshot history for a deck, newest-first. Each entry includes a computed diff."""
    history = repo.get_history(deck_id, user_id=user_id, limit=limit)
    if history is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return DeckHistoryResponse(deck_id=deck_id, snapshots=history)


@router.post("/{deck_id}/revert/{snapshot_id}")
async def revert_deck_to_snapshot(
    deck_id: int,
    snapshot_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
):
    """Revert a deck to the state captured in snapshot_id. Creates a new snapshot recording the revert."""
    try:
        deck = repo.revert_to_snapshot(deck_id, snapshot_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck or snapshot not found")
    return deck
