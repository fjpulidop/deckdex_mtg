"""
Decks API routes.
Decks require Postgres; returns 501 when DATABASE_URL is not set.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
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

        repo.add_card(
            deck_id,
            card_id,
            quantity=card["quantity"],
            is_commander=card["is_commander"],
            user_id=user_id,
        )
        imported_count += 1

    # Fetch the updated deck to return in the response
    updated_deck = repo.get_deck_with_cards(deck_id, user_id=user_id)

    return DeckImportResponse(
        imported_count=imported_count,
        skipped_count=len(skipped),
        skipped=skipped,
        deck=updated_deck,
    )
