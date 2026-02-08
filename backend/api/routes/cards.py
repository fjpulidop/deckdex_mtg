"""
Cards API routes
Endpoints for accessing card collection data
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from loguru import logger

from ..dependencies import get_cached_collection, get_collection_repo, clear_collection_cache
from ..services.card_image_service import get_card_image as resolve_card_image

router = APIRouter(prefix="/api/cards", tags=["cards"])

# Pydantic models for request/response
class Card(BaseModel):
    """Card data model matching Google Sheets column layout + optional id (Postgres)"""
    id: Optional[int] = None
    name: Optional[str] = None
    english_name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    color_identity: Optional[str] = None
    colors: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    rarity: Optional[str] = None
    price: Optional[str] = None
    release_date: Optional[str] = None
    set_id: Optional[str] = None
    set_name: Optional[str] = None
    number: Optional[str] = None
    edhrec_rank: Optional[str] = None
    game_strategy: Optional[str] = None
    tier: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[Card])
async def list_cards(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None)
):
    """
    List cards from collection with optional pagination and search
    
    Args:
        limit: Maximum number of cards to return (1-1000)
        offset: Number of cards to skip
        search: Search term to filter cards by name (case-insensitive)
    
    Returns:
        List of cards matching criteria
    """
    logger.info(f"GET /api/cards - limit={limit}, offset={offset}, search={search}")
    
    try:
        # Get collection data (cached)
        collection = get_cached_collection()
        
        # Filter by search term if provided (ignore literal "undefined" from JS)
        if search and search != 'undefined':
            search_lower = search.lower()
            collection = [
                card for card in collection 
                if card.get('name') and search_lower in card['name'].lower()
            ]
        
        # Apply pagination
        total = len(collection)
        paginated = collection[offset:offset + limit]
        
        logger.info(f"Returning {len(paginated)} cards (total: {total}, offset: {offset})")
        return paginated
        
    except Exception as e:
        logger.error(f"Error listing cards: {e}")
        
        # Check for Google Sheets quota errors
        if 'Quota exceeded' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
            raise HTTPException(
                status_code=503,
                detail="Google Sheets API quota exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to fetch cards: {str(e)}")


@router.get("/{id}/image")
async def get_card_image(id: int):
    """
    Return the card's image by surrogate id. If not stored, fetch from Scryfall, store, then return.
    Returns 404 if card not found or image unavailable.
    """
    try:
        data, media_type = resolve_card_image(id)
        return Response(content=data, media_type=media_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Card or image not found")


@router.get("/{card_id_or_name}", response_model=Card)
async def get_card(card_id_or_name: str):
    """
    Get details for a specific card by surrogate id (integer) or by name (string).

    Args:
        card_id_or_name: Numeric id (e.g. 42) or card name (e.g. Black Lotus)

    Returns:
        Card details

    Raises:
        HTTPException: 404 if card not found
    """
    logger.info(f"GET /api/cards/{card_id_or_name}")

    try:
        repo = get_collection_repo()
        if repo is not None:
            # Try as id first (numeric path segment)
            try:
                card_id = int(card_id_or_name)
                card = repo.get_card_by_id(card_id)
                if card is not None:
                    return card
            except ValueError:
                pass
            # Fall back to get by name
            collection = get_cached_collection()
            card_name_lower = card_id_or_name.lower()
            for card in collection:
                if card.get("name") and card["name"].lower() == card_name_lower:
                    return card
            raise HTTPException(status_code=404, detail=f"Card '{card_id_or_name}' not found")

        # No repo: use collection (Sheets)
        collection = get_cached_collection()
        card_name_lower = card_id_or_name.lower()
        for card in collection:
            if card.get("name") and card["name"].lower() == card_name_lower:
                return card
        raise HTTPException(status_code=404, detail=f"Card '{card_id_or_name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching card {card_id_or_name}: {e}")
        if "Quota exceeded" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Google Sheets API quota exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Card, status_code=201)
async def create_card(card: Card):
    """
    Create a new card. Requires Postgres (DATABASE_URL set).
    """
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Card create requires PostgreSQL. Set DATABASE_URL.",
        )
    try:
        payload = card.model_dump(exclude_unset=True, exclude={"id"})
        created = repo.create(payload)
        clear_collection_cache()
        return created
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=Card)
async def update_card(id: int, card: Card):
    """
    Update a card by surrogate id. Requires Postgres.
    """
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Card update requires PostgreSQL. Set DATABASE_URL.",
        )
    try:
        payload = card.model_dump(exclude_unset=True, exclude={"id"})
        updated = repo.update(id, payload)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Card id {id} not found")
        clear_collection_cache()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating card {id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id}", status_code=204)
async def delete_card(id: int):
    """
    Delete a card by surrogate id. Requires Postgres.
    """
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Card delete requires PostgreSQL. Set DATABASE_URL.",
        )
    deleted = repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Card id {id} not found")
    clear_collection_cache()
