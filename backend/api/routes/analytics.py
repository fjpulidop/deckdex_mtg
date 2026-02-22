"""
Analytics API routes
Endpoints for collection aggregations used by the Analytics dashboard.
"""
import re
from typing import Optional, Any
from collections import Counter
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from loguru import logger

from ..dependencies import get_cached_collection, get_current_user_id
from ..filters import filter_collection, parse_price

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# ---------------------------------------------------------------------------
# Cache (same pattern as stats): keyed by (endpoint, filter-params) tuple
# ---------------------------------------------------------------------------
_analytics_cache: dict[tuple, dict[str, Any]] = {}
_ANALYTICS_TTL = 30  # seconds


def _cache_key(endpoint: str, search: Optional[str], rarity: Optional[str],
               type_: Optional[str], set_name: Optional[str],
               price_min: Optional[str], price_max: Optional[str],
               extra: Optional[str] = None) -> tuple:
    return (
        endpoint,
        (search or "").strip(),
        (rarity or "").strip().lower(),
        (type_ or "").strip(),
        (set_name or "").strip(),
        (price_min or "").strip(),
        (price_max or "").strip(),
        (extra or ""),
    )


def _get_cached(key: tuple) -> Optional[Any]:
    now = datetime.now()
    if key in _analytics_cache:
        entry = _analytics_cache[key]
        age = (now - entry["timestamp"]).total_seconds()
        if age < _ANALYTICS_TTL:
            return entry["data"]
    return None


def _set_cached(key: tuple, data: Any) -> None:
    _analytics_cache[key] = {"data": data, "timestamp": datetime.now()}


def _filtered_collection(search, rarity, type_, set_name, price_min, price_max, user_id: Optional[int] = None):
    """Return the filtered collection list."""
    collection = get_cached_collection(user_id=user_id)
    return filter_collection(collection, search, rarity, type_, set_name, price_min, price_max)


# ---------------------------------------------------------------------------
# Color identity normalization
# ---------------------------------------------------------------------------
# Valid WUBRG single-letter codes
_VALID_COLORS = {"W", "U", "B", "R", "G"}

# Full-name → letter mapping (case-insensitive lookup)
_COLOR_NAME_MAP = {
    "white": "W",
    "blue": "U",
    "black": "B",
    "red": "R",
    "green": "G",
}


def _normalize_color_identity(raw: Any) -> str:
    """
    Normalize color_identity from various DB formats to a canonical WUBRG string.

    Handles:
      - Python list: ["W", "U"]
      - str repr of Python list: "['W', 'U']"
      - Comma-separated: "W,U" or "W, U"
      - Full names: "Blue" or "['Blue', 'Red']"
      - Single letter: "W"
      - Empty / None → "C" (colorless)
    """
    if raw is None:
        return "C"

    if isinstance(raw, list):
        letters = [_COLOR_NAME_MAP.get(c.strip().lower(), c.strip().upper()) for c in raw if c]
    elif isinstance(raw, str):
        s = raw.strip()
        if not s or s == "[]":
            return "C"
        # Strip Python list-repr brackets/quotes: "['W', 'U']" → "W, U"
        if s.startswith("["):
            # Extract quoted tokens from the repr
            tokens = re.findall(r"'([^']*)'", s)
            if not tokens:
                # Fallback: just strip brackets
                tokens = [t.strip() for t in s.strip("[]").split(",") if t.strip()]
            letters = []
            for t in tokens:
                t_lower = t.strip().lower()
                if t_lower in _COLOR_NAME_MAP:
                    letters.append(_COLOR_NAME_MAP[t_lower])
                elif t.strip().upper() in _VALID_COLORS:
                    letters.append(t.strip().upper())
                # else skip unknown tokens
        elif "," in s:
            # Comma-separated: "W,U" or "White,Blue"
            letters = []
            for part in s.split(","):
                p = part.strip()
                p_lower = p.lower()
                if p_lower in _COLOR_NAME_MAP:
                    letters.append(_COLOR_NAME_MAP[p_lower])
                elif p.upper() in _VALID_COLORS:
                    letters.append(p.upper())
        else:
            # Single value: "W" or "Blue"
            s_lower = s.lower()
            if s_lower in _COLOR_NAME_MAP:
                letters = [_COLOR_NAME_MAP[s_lower]]
            elif s.upper() in _VALID_COLORS:
                letters = [s.upper()]
            else:
                # Try each character (e.g. "WU" stored without separator)
                letters = [ch for ch in s.upper() if ch in _VALID_COLORS]
    else:
        return "C"

    # Deduplicate and sort in WUBRG order
    wubrg_order = "WUBRG"
    unique = sorted(set(letters), key=lambda c: wubrg_order.index(c) if c in wubrg_order else 99)
    return "".join(unique) if unique else "C"


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------
class RarityCount(BaseModel):
    rarity: str
    count: int

class ColorIdentityCount(BaseModel):
    color_identity: str
    count: int

class CmcCount(BaseModel):
    cmc: str
    count: int

class SetCount(BaseModel):
    set_name: str
    count: int


# ---------------------------------------------------------------------------
# Common filter query parameters (reused across endpoints)
# ---------------------------------------------------------------------------
def _filter_params():
    """Placeholder – FastAPI needs explicit Query() per endpoint, so we repeat them."""
    pass


# ---------------------------------------------------------------------------
# GET /api/analytics/rarity
# ---------------------------------------------------------------------------
@router.get("/rarity", response_model=list[RarityCount])
async def analytics_rarity(
    request: Request,
    search: Optional[str] = Query(default=None),
    rarity: Optional[str] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    set_name: Optional[str] = Query(default=None),
    price_min: Optional[str] = Query(default=None),
    price_max: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id)
):
    """Count of cards per rarity for the filtered collection."""
    key = _cache_key("rarity", search, rarity, type_filter, set_name, price_min, price_max)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        cards = _filtered_collection(search, rarity, type_filter, set_name, price_min, price_max, user_id=user_id)
        counter: Counter = Counter()
        for c in cards:
            r = (c.get("rarity") or "Unknown").strip()
            if r:
                counter[r] += 1
        result = sorted(
            [{"rarity": k, "count": v} for k, v in counter.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/rarity: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# GET /api/analytics/color-identity
# ---------------------------------------------------------------------------
@router.get("/color-identity", response_model=list[ColorIdentityCount])
async def analytics_color_identity(
    request: Request,
    search: Optional[str] = Query(default=None),
    rarity: Optional[str] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    set_name: Optional[str] = Query(default=None),
    price_min: Optional[str] = Query(default=None),
    price_max: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id)
):
    """Count of cards per color identity for the filtered collection."""
    key = _cache_key("color-identity", search, rarity, type_filter, set_name, price_min, price_max)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        cards = _filtered_collection(search, rarity, type_filter, set_name, price_min, price_max, user_id=user_id)
        counter: Counter = Counter()
        for c in cards:
            identity = _normalize_color_identity(c.get("color_identity") or c.get("identity") or "")
            counter[identity] += 1
        result = sorted(
            [{"color_identity": k, "count": v} for k, v in counter.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/color-identity: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# GET /api/analytics/cmc
# ---------------------------------------------------------------------------
@router.get("/cmc", response_model=list[CmcCount])
async def analytics_cmc(
    request: Request,
    search: Optional[str] = Query(default=None),
    rarity: Optional[str] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    set_name: Optional[str] = Query(default=None),
    price_min: Optional[str] = Query(default=None),
    price_max: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id)
):
    """Count of cards per CMC bucket for the filtered collection. 7+ grouped."""
    key = _cache_key("cmc", search, rarity, type_filter, set_name, price_min, price_max)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        cards = _filtered_collection(search, rarity, type_filter, set_name, price_min, price_max, user_id=user_id)
        counter: Counter = Counter()
        for c in cards:
            raw_cmc = c.get("cmc")
            if raw_cmc is None or raw_cmc == "":
                bucket = "Unknown"
            else:
                try:
                    val = int(float(str(raw_cmc)))
                    bucket = str(val) if val < 7 else "7+"
                except (ValueError, TypeError):
                    bucket = "Unknown"
            counter[bucket] += 1

        # Sort: numeric buckets first (0-6), then 7+, then Unknown
        def sort_key(item):
            b = item["cmc"]
            if b == "Unknown":
                return (2, 0)
            if b == "7+":
                return (1, 7)
            try:
                return (0, int(b))
            except ValueError:
                return (2, 0)

        result = sorted(
            [{"cmc": k, "count": v} for k, v in counter.items()],
            key=sort_key,
        )
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/cmc: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# GET /api/analytics/sets
# ---------------------------------------------------------------------------
@router.get("/sets", response_model=list[SetCount])
async def analytics_sets(
    request: Request,
    search: Optional[str] = Query(default=None),
    rarity: Optional[str] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    set_name: Optional[str] = Query(default=None),
    price_min: Optional[str] = Query(default=None),
    price_max: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: int = Depends(get_current_user_id)
):
    """Top N sets by card count for the filtered collection."""
    key = _cache_key("sets", search, rarity, type_filter, set_name, price_min, price_max, extra=str(limit))
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        cards = _filtered_collection(search, rarity, type_filter, set_name, price_min, price_max, user_id=user_id)
        counter: Counter = Counter()
        for c in cards:
            s = (c.get("set_name") or "Unknown").strip()
            if s:
                counter[s] += 1
        most_common = counter.most_common(limit)
        result = [{"set_name": k, "count": v} for k, v in most_common]
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/sets: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
