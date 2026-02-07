"""
Statistics API routes
Endpoints for collection statistics and aggregations
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from ..dependencies import get_cached_collection

router = APIRouter(prefix="/api/stats", tags=["stats"])

# Cache for stats (separate from collection cache)
_stats_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 30  # seconds
}

class Stats(BaseModel):
    """Collection statistics model"""
    total_cards: int
    total_value: float
    average_price: float
    last_updated: str
    
    class Config:
        from_attributes = True

def calculate_stats(collection: list) -> dict:
    """
    Calculate collection statistics
    
    Args:
        collection: List of card data
    
    Returns:
        Dictionary with statistics
    """
    total_cards = len(collection)
    
    # Calculate total value and average price
    prices = []
    for card in collection:
        price_str = card.get('price')
        if price_str and price_str != 'N/A':
            try:
                # Handle European format (comma as decimal separator)
                price_normalized = str(price_str).replace(',', '.')
                price = float(price_normalized)
                prices.append(price)
            except (ValueError, TypeError):
                continue
    
    total_value = sum(prices)
    average_price = total_value / len(prices) if prices else 0.0
    
    return {
        'total_cards': total_cards,
        'total_value': round(total_value, 2),
        'average_price': round(average_price, 2),
        'last_updated': datetime.now().isoformat()
    }

@router.get("/", response_model=Stats)
async def get_stats():
    """
    Get collection statistics
    
    Returns statistics with 30-second cache:
    - total_cards: Total number of cards in collection
    - total_value: Sum of all card prices (EUR)
    - average_price: Average card price (EUR)
    - last_updated: ISO timestamp of when stats were calculated
    """
    logger.info("GET /api/stats")
    
    try:
        # Check cache
        now = datetime.now()
        if (_stats_cache['data'] is not None and 
            _stats_cache['timestamp'] is not None):
            
            age = (now - _stats_cache['timestamp']).total_seconds()
            if age < _stats_cache['ttl']:
                logger.debug(f"Returning cached stats (age: {age:.1f}s)")
                return _stats_cache['data']
        
        # Calculate fresh stats
        logger.info("Calculating fresh stats")
        collection = get_cached_collection()
        stats = calculate_stats(collection)
        
        # Update cache
        _stats_cache['data'] = stats
        _stats_cache['timestamp'] = now
        
        logger.info(f"Stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        
        # Check for Google Sheets quota errors
        if 'Quota exceeded' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
            raise HTTPException(
                status_code=503,
                detail="Google Sheets API quota exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to calculate stats: {str(e)}")

def clear_stats_cache():
    """Clear the stats cache to force recalculation on next request"""
    _stats_cache['data'] = None
    _stats_cache['timestamp'] = None
    logger.info("Stats cache cleared")
