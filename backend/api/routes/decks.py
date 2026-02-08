"""
Decks API routes.
Decks require Postgres; returns 501 when DATABASE_URL is not set.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..dependencies import get_deck_repo
from deckdex.storage.deck_repository import DeckRepository

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


# --- Routes ---

@router.get("/")
async def list_decks(repo: DeckRepository = Depends(require_deck_repo)):
    """List all decks (id, name, created_at, updated_at, card_count)."""
    return repo.list_all()


@router.post("/", status_code=201)
async def create_deck(
    body: DeckCreate,
    repo: DeckRepository = Depends(require_deck_repo),
):
    """Create a new deck. Returns created deck."""
    return repo.create(name=body.name or "Unnamed Deck")


@router.get("/{deck_id}")
async def get_deck(
    deck_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
):
    """Get a single deck with full card list (cards with full payload for UI)."""
    deck = repo.get_deck_with_cards(deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.patch("/{deck_id}")
async def update_deck(
    deck_id: int,
    body: DeckUpdate,
    repo: DeckRepository = Depends(require_deck_repo),
):
    """Update deck name."""
    deck = repo.update_name(deck_id, body.name)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.delete("/{deck_id}", status_code=204)
async def delete_deck(
    deck_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
):
    """Delete deck and all its deck_cards."""
    if not repo.delete(deck_id):
        raise HTTPException(status_code=404, detail="Deck not found")


@router.post("/{deck_id}/cards", status_code=201)
async def add_card_to_deck(
    deck_id: int,
    body: AddCardBody,
    repo: DeckRepository = Depends(require_deck_repo),
):
    """Add a card from the collection to the deck. Card must exist in collection."""
    # Ensure deck exists
    if repo.get_by_id(deck_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if not repo.add_card(
        deck_id,
        body.card_id,
        quantity=body.quantity or 1,
        is_commander=body.is_commander or False,
    ):
        raise HTTPException(
            status_code=404,
            detail="Card not found in collection. Add the card to your collection first.",
        )
    deck = repo.get_deck_with_cards(deck_id)
    return deck


@router.patch("/{deck_id}/cards/{card_id}")
async def patch_deck_card(
    deck_id: int,
    card_id: int,
    body: PatchDeckCardBody,
    repo: DeckRepository = Depends(require_deck_repo),
):
    """Update deck card (e.g. set as commander). When is_commander=true, unsets any other commander."""
    if body.is_commander is True:
        if not repo.set_commander(deck_id, card_id):
            raise HTTPException(status_code=404, detail="Deck or card in deck not found")
        deck = repo.get_deck_with_cards(deck_id)
        return deck
    raise HTTPException(status_code=400, detail="Only is_commander=true is supported")


@router.delete("/{deck_id}/cards/{card_id}", status_code=204)
async def remove_card_from_deck(
    deck_id: int,
    card_id: int,
    repo: DeckRepository = Depends(require_deck_repo),
):
    """Remove one card from the deck."""
    if not repo.remove_card(deck_id, card_id):
        raise HTTPException(status_code=404, detail="Deck or card in deck not found")
