"""
Statistics API routes
Endpoints for collection statistics and aggregations
"""
from typing import Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from loguru import logger

from ..dependencies import get_cached_collection, get_current_user_id
from ..filters import filter_collection, parse_price

router = APIRouter(prefix="/api/stats", tags=["stats"])

# Cache for stats keyed by filter params; each entry: { 'data': stats, 'timestamp': datetime }
# Key is a tuple (search, rarity, type, set_name, price_min, price_max) for canonical lookup
_stats_cache: dict[tuple, dict[str, Any]] = {}
_STATS_TTL = 30  # seconds

class Stats(BaseModel):
    """Collection statistics model"""
    total_cards: int
    total_value: float
    average_price: float
    last_updated: str
    
    class Config:
        from_attributes = True

def _cache_key(
    search: Optional[str],
    rarity: Optional[str],
    type_: Optional[str],
    set_name: Optional[str],
    price_min: Optional[str],
    price_max: Optional[str],
) -> tuple:
    """Canonical cache key from filter params (normalized, so same filters hit same key)."""
    return (
        (search or "").strip(),
        (rarity or "").strip().lower(),
        (type_ or "").strip(),
        (set_name or "").strip(),
        (price_min or "").strip(),
        (price_max or "").strip(),
    )


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
        price_str = card.get("price")
        price = parse_price(price_str)
        if price is not None:
            prices.append(price)

    total_value = sum(prices)
    average_price = total_value / len(prices) if prices else 0.0

    return {
        "total_cards": total_cards,
        "total_value": round(total_value, 2),
        "average_price": round(average_price, 2),
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/", response_model=Stats)
async def get_stats(
    request: Request,
    search: Optional[str] = Query(default=None),
    rarity: Optional[str] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    set_name: Optional[str] = Query(default=None),
    price_min: Optional[str] = Query(default=None),
    price_max: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get collection statistics, optionally filtered by query params.

    Optional query params: search, rarity, type, set_name, price_min, price_max.
    Returns statistics with 30-second cache per filter combination.
    """
    key = _cache_key(search, rarity, type_filter, set_name, price_min, price_max)
    logger.info("GET /api/stats %s - user=%s", key, user_id)

    try:
        now = datetime.now()
        if key in _stats_cache:
            entry = _stats_cache[key]
            age = (now - entry["timestamp"]).total_seconds()
            if age < _STATS_TTL:
                logger.debug("Returning cached stats (key=%s, age=%.1fs)", key, age)
                return entry["data"]

        collection = get_cached_collection(user_id=user_id)
        filtered = filter_collection(
            collection, search, rarity, type_filter, set_name, price_min, price_max
        )
        stats = calculate_stats(filtered)
        _stats_cache[key] = {"data": stats, "timestamp": now}
        logger.info("Stats: %s", stats)
        return stats

    except Exception as e:
        logger.error("Error calculating stats: %s", e)
        if "Quota exceeded" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Google Sheets API quota exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            ) from e
        raise HTTPException(status_code=500, detail=f"Failed to calculate stats: {str(e)}") from e


def clear_stats_cache():
    """Clear all stats cache entries to force recalculation on next request."""
    _stats_cache.clear()
    logger.info("Stats cache cleared")
