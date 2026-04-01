"""Suggestions API routes: deck card recommendations from newly released sets."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel

from deckdex.storage.deck_repository import DeckRepository
from deckdex.storage.suggestion_repository import SuggestionRepository

from ..dependencies import get_current_user_id, get_deck_repo, get_suggestion_repo

router = APIRouter(prefix="/api", tags=["suggestions"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class DeckSuggestion(BaseModel):
    scryfall_id: str
    card_name: str
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    type_line: Optional[str] = None
    color_identity: Optional[str] = None
    oracle_text: Optional[str] = None
    reason: str
    score: float
    image_uri: Optional[str] = None


class DeckSuggestionsResponse(BaseModel):
    deck_id: int
    set_code: Optional[str] = None
    set_name: Optional[str] = None
    suggestions: List[DeckSuggestion]


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def require_suggestion_repo() -> SuggestionRepository:
    """Raise 501 if Postgres is not configured."""
    repo = get_suggestion_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Deck suggestions require Postgres. Set DATABASE_URL to use this feature.",
        )
    return repo


def require_deck_repo() -> DeckRepository:
    """Raise 501 if Postgres is not configured."""
    repo = get_deck_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Deck suggestions require Postgres. Set DATABASE_URL to use this feature.",
        )
    return repo


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/decks/{deck_id}/suggestions", response_model=DeckSuggestionsResponse)
async def get_deck_suggestions(
    deck_id: int,
    repo: SuggestionRepository = Depends(require_suggestion_repo),
    deck_repo: DeckRepository = Depends(require_deck_repo),
    user_id: int = Depends(get_current_user_id),
) -> DeckSuggestionsResponse:
    """Return card suggestions for a deck, scoped to the current user."""
    # Verify deck ownership
    deck = deck_repo.get_by_id(deck_id, user_id=user_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")

    rows = repo.get_suggestions_for_deck(deck_id, user_id, limit=5)

    set_code: Optional[str] = rows[0]["set_code"] if rows else None
    # Derive set_name from seen_set_codes — not stored in deck_suggestions row,
    # so we expose only set_code; set_name defaults to None if not available.
    set_name: Optional[str] = None

    suggestions = [
        DeckSuggestion(
            scryfall_id=r["scryfall_id"],
            card_name=r["card_name"],
            mana_cost=r.get("mana_cost"),
            cmc=float(r["cmc"]) if r.get("cmc") is not None else None,
            type_line=r.get("type_line"),
            color_identity=r.get("color_identity"),
            oracle_text=r.get("oracle_text"),
            reason=r["reason"],
            score=float(r["score"]),
            image_uri=r.get("image_uri"),
        )
        for r in rows
    ]

    return DeckSuggestionsResponse(
        deck_id=deck_id,
        set_code=set_code,
        set_name=set_name,
        suggestions=suggestions,
    )


@router.delete("/decks/{deck_id}/suggestions/{scryfall_id}", status_code=204)
async def dismiss_suggestion(
    deck_id: int,
    scryfall_id: str,
    repo: SuggestionRepository = Depends(require_suggestion_repo),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Dismiss (delete) a single suggestion for a deck."""
    deleted = repo.delete_suggestion(deck_id, scryfall_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Suggestion not found")


@router.post("/suggestions/refresh", status_code=202)
async def refresh_suggestions(
    request: Request,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """Manually trigger a new-set poll in the background."""
    if not hasattr(request.app.state, "new_set_poller"):
        raise HTTPException(
            status_code=501,
            detail="Suggestion refresh requires Postgres. Set DATABASE_URL to use this feature.",
        )
    background_tasks.add_task(request.app.state.new_set_poller.run_once)
    return {"message": "Suggestion refresh started"}
