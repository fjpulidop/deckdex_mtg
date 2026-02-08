"""
Statistics API routes
Endpoints for collection statistics and aggregations
"""
from typing import Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from ..dependencies import get_cached_collection

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

def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string handling multiple formats (European/US with or without thousands separator).
    
    Supported formats:
    - European with thousands: "1.234,56" → 1234.56
    - European without thousands: "1234,56" → 1234.56
    - US with thousands: "1,234.56" → 1234.56
    - US without thousands: "1234.56" → 1234.56
    
    Args:
        price_str: Price string to parse
        
    Returns:
        Parsed float value or None if invalid
    """
    if not price_str or price_str == 'N/A':
        return None
        
    try:
        price_clean = str(price_str).strip()
        
        # Detect format by last separator position
        if ',' in price_clean and '.' in price_clean:
            # Mixed format: check which comes last
            last_comma_pos = price_clean.rfind(',')
            last_dot_pos = price_clean.rfind('.')
            
            if last_comma_pos > last_dot_pos:
                # European: "1.234,56" → remove dots, replace comma with dot
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                # US: "1,234.56" → remove commas
                price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Only comma: assume European decimal "1234,56"
            price_clean = price_clean.replace(',', '.')
        # else: only dots or no separator, use as-is
        
        return float(price_clean)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse price '{price_str}': {e}")
        return None

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


def _filter_collection(
    collection: list,
    search: Optional[str],
    rarity: Optional[str],
    type_: Optional[str],
    set_name: Optional[str],
    price_min: Optional[str],
    price_max: Optional[str],
) -> list:
    """Filter collection by same semantics as dashboard: name contains, exact match for rarity/type/set_name, price range inclusive."""
    result = collection
    if search and search.strip():
        search_lower = search.strip().lower()
        result = [c for c in result if c.get("name") and search_lower in (c["name"] or "").lower()]
    if rarity and rarity.strip():
        r = rarity.strip().lower()
        result = [c for c in result if (c.get("rarity") or "").lower() == r]
    if type_ and type_.strip():
        t = type_.strip()
        result = [c for c in result if c.get("type") == t]
    if set_name and set_name.strip():
        s = set_name.strip()
        result = [c for c in result if c.get("set_name") == s]
    if price_min or price_max:
        try:
            min_num = float(price_min.replace(",", ".")) if price_min and price_min.strip() else None
        except (ValueError, TypeError):
            min_num = None
        try:
            max_num = float(price_max.replace(",", ".")) if price_max and price_max.strip() else None
        except (ValueError, TypeError):
            max_num = None
        if min_num is not None or max_num is not None:
            filtered = []
            for c in result:
                p = parse_price(c.get("price"))
                if p is None:
                    continue
                if min_num is not None and p < min_num:
                    continue
                if max_num is not None and p > max_num:
                    continue
                filtered.append(c)
            result = filtered
    return result


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
    search: Optional[str] = Query(default=None),
    rarity: Optional[str] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    set_name: Optional[str] = Query(default=None),
    price_min: Optional[str] = Query(default=None),
    price_max: Optional[str] = Query(default=None),
):
    """
    Get collection statistics, optionally filtered by query params.

    Optional query params: search, rarity, type, set_name, price_min, price_max.
    Returns statistics with 30-second cache per filter combination.
    """
    key = _cache_key(search, rarity, type_filter, set_name, price_min, price_max)
    logger.info("GET /api/stats %s", key)

    try:
        now = datetime.now()
        if key in _stats_cache:
            entry = _stats_cache[key]
            age = (now - entry["timestamp"]).total_seconds()
            if age < _STATS_TTL:
                logger.debug("Returning cached stats (key=%s, age=%.1fs)", key, age)
                return entry["data"]

        collection = get_cached_collection()
        filtered = _filter_collection(
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
