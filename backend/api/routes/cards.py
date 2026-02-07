"""
Cards API routes
Endpoints for accessing card collection data
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from loguru import logger

from ..dependencies import get_cached_collection

router = APIRouter(prefix="/api/cards", tags=["cards"])

# Pydantic models for request/response
class Card(BaseModel):
    """Card data model matching Google Sheets column layout"""
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

@router.get("/{card_name}", response_model=Card)
async def get_card(card_name: str):
    """
    Get details for a specific card
    
    Args:
        card_name: Name of the card to retrieve
    
    Returns:
        Card details
    
    Raises:
        HTTPException: 404 if card not found
    """
    logger.info(f"GET /api/cards/{card_name}")
    
    try:
        # Get collection data (cached)
        collection = get_cached_collection()
        
        # Find card by name (case-insensitive)
        card_name_lower = card_name.lower()
        for card in collection:
            if card.get('name') and card['name'].lower() == card_name_lower:
                logger.info(f"Found card: {card['name']}")
                return card
        
        # Card not found
        logger.warning(f"Card not found: {card_name}")
        raise HTTPException(status_code=404, detail=f"Card '{card_name}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching card {card_name}: {e}")
        
        # Check for Google Sheets quota errors
        if 'Quota exceeded' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
            raise HTTPException(
                status_code=503,
                detail="Google Sheets API quota exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to fetch card: {str(e)}")
