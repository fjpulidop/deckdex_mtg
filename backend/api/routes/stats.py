"""
Statistics API routes
Endpoints for collection statistics and aggregations
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel

from ..dependencies import get_cached_collection, get_collection_repo, get_current_user_id
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
    user_id: int,
    search: Optional[str],
    rarity: Optional[str],
    type_: Optional[str],
    set_name: Optional[str],
    price_min: Optional[str],
    price_max: Optional[str],
    color_identity: Optional[str] = None,
    cmc: Optional[str] = None,
) -> tuple:
    """Canonical cache key from filter params (normalized, so same filters hit same key).

    Includes user_id to prevent cross-user cache leakage.
    """
    return (
        user_id,
        (search or "").strip(),
        (rarity or "").strip().lower(),
        (type_ or "").strip(),
        (set_name or "").strip(),
        (price_min or "").strip(),
        (price_max or "").strip(),
        (color_identity or "").strip(),
        (cmc or "").strip(),
    )


def calculate_stats(collection: list) -> dict:
    """
    Calculate collection statistics

    Args:
        collection: List of card data

    Returns:
        Dictionary with statistics
    """
    total_cards = sum(int(card.get("quantity") or 1) for card in collection)

    # Calculate total value and average price (quantity-weighted)
    total_value = 0.0
    priced_qty = 0
    for card in collection:
        price = parse_price(card.get("price"))
        qty = int(card.get("quantity") or 1)
        if price is not None:
            total_value += price * qty
            priced_qty += qty

    average_price = total_value / priced_qty if priced_qty else 0.0

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
    color_identity: Optional[str] = Query(default=None),
    cmc: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get collection statistics, optionally filtered by query params.

    Optional query params: search, rarity, type, set_name, price_min, price_max, color_identity, cmc.
    Returns statistics with 30-second cache per filter combination.
    For Postgres: uses a single SQL aggregation query (no full collection load).
    For Google Sheets: uses cached collection + Python aggregation.
    """
    key = _cache_key(user_id, search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc)
    logger.info("GET /api/stats %s - user=%s", key, user_id)

    try:
        now = datetime.now()
        if key in _stats_cache:
            entry = _stats_cache[key]
            age = (now - entry["timestamp"]).total_seconds()
            if age < _STATS_TTL:
                logger.debug("Returning cached stats (key=%s, age=%.1fs)", key, age)
                return entry["data"]

        repo = get_collection_repo()
        if repo is not None:
            # Postgres path: single SQL aggregation query — no full collection load
            filters = {
                "search": search,
                "rarity": rarity,
                "type_": type_filter,
                "color_identity": color_identity,
                "set_name": set_name,
                "price_min": price_min,
                "price_max": price_max,
                "cmc": cmc,
            }
            agg = repo.get_cards_stats(user_id=user_id, filters=filters)
            stats = {
                **agg,
                "last_updated": datetime.now().isoformat(),
            }
        else:
            # Google Sheets path: in-memory aggregation
            collection = get_cached_collection(user_id=user_id)
            filtered = filter_collection(
                collection,
                search=search,
                rarity=rarity,
                type_=type_filter,
                color_identity=color_identity,
                set_name=set_name,
                price_min=price_min,
                price_max=price_max,
                cmc=cmc,
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
        raise HTTPException(status_code=500, detail="Failed to calculate stats") from e


def clear_stats_cache():
    """Clear all stats cache entries to force recalculation on next request."""
    _stats_cache.clear()
    logger.info("Stats cache cleared")
