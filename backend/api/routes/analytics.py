"""
Analytics API routes
Endpoints for collection aggregations used by the Analytics dashboard.
"""

from collections import Counter
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel

from ..dependencies import get_cached_collection, get_collection_repo, get_current_user_id
from ..filters import filter_collection
from ..utils.color import normalize_color_identity as _normalize_color_identity

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# ---------------------------------------------------------------------------
# Cache (same pattern as stats): keyed by (endpoint, filter-params) tuple
# ---------------------------------------------------------------------------
_analytics_cache: dict[tuple, dict[str, Any]] = {}
_ANALYTICS_TTL = 30  # seconds


def _cache_key(
    endpoint: str,
    user_id: int,
    search: Optional[str],
    rarity: Optional[str],
    type_: Optional[str],
    set_name: Optional[str],
    price_min: Optional[str],
    price_max: Optional[str],
    color_identity: Optional[str] = None,
    cmc: Optional[str] = None,
    extra: Optional[str] = None,
) -> tuple:
    """Cache key includes user_id to prevent cross-user data leakage."""
    return (
        endpoint,
        user_id,
        (search or "").strip(),
        (rarity or "").strip().lower(),
        (type_ or "").strip(),
        (set_name or "").strip(),
        (price_min or "").strip(),
        (price_max or "").strip(),
        (color_identity or "").strip(),
        (cmc or "").strip(),
        (extra or ""),
    )


def _make_filters(search, rarity, type_, set_name, price_min, price_max, color_identity=None, cmc=None) -> dict:
    """Build filter dict for repository methods."""
    return {
        "search": search,
        "rarity": rarity,
        "type_": type_,
        "color_identity": color_identity,
        "set_name": set_name,
        "price_min": price_min,
        "price_max": price_max,
        "cmc": cmc,
    }


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


def _filtered_collection(
    search, rarity, type_, set_name, price_min, price_max, color_identity=None, cmc=None, user_id: Optional[int] = None
):
    """Return the filtered collection list."""
    collection = get_cached_collection(user_id=user_id)
    return filter_collection(
        collection,
        search=search,
        rarity=rarity,
        type_=type_,
        color_identity=color_identity,
        set_name=set_name,
        price_min=price_min,
        price_max=price_max,
        cmc=cmc,
    )


# ---------------------------------------------------------------------------
# Type priority for primary-type extraction
# ---------------------------------------------------------------------------
_TYPE_PRIORITY = [
    "Creature",
    "Land",
    "Artifact",
    "Enchantment",
    "Planeswalker",
    "Instant",
    "Sorcery",
    "Battle",
]


def _extract_primary_type(type_line: Optional[str]) -> str:
    """
    Extract the primary MTG card type from a type_line string.

    Splits on "—" (em-dash) to remove subtypes, then on "//" for split cards.
    Checks each word against _TYPE_PRIORITY; first match wins.
    Returns "Other" for unknown or empty type lines.

    Examples:
        "Legendary Creature — Dragon"  → "Creature"
        "Artifact Creature — Golem"    → "Creature"  (Creature > Artifact)
        "Basic Land — Forest"          → "Land"
        ""                             → "Other"
        None                           → "Other"
    """
    if not type_line:
        return "Other"
    # Take only the portion before the em-dash (subtype separator)
    main_part = type_line.split("—")[0].split("//")[0]
    words = main_part.split()
    for priority_type in _TYPE_PRIORITY:
        if priority_type in words:
            return priority_type
    return "Other"


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


class TypeCount(BaseModel):
    type_line: str
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
    color_identity: Optional[str] = Query(default=None),
    cmc: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id),
):
    """Count of cards per rarity for the filtered collection.

    Postgres path: single SQL GROUP BY query.
    Sheets path: in-memory Counter over cached collection.
    """
    key = _cache_key(
        "rarity", user_id, search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc
    )
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        repo = get_collection_repo()
        if repo is not None:
            filters = _make_filters(search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc)
            rows = repo.get_cards_analytics(user_id=user_id, filters=filters, dimension="rarity")
            result = [{"rarity": r["label"], "count": r["count"]} for r in rows]
        else:
            cards = _filtered_collection(
                search,
                rarity,
                type_filter,
                set_name,
                price_min,
                price_max,
                color_identity=color_identity,
                cmc=cmc,
                user_id=user_id,
            )
            counter: Counter = Counter()
            for c in cards:
                r = (c.get("rarity") or "Unknown").strip()
                if r:
                    counter[r] += int(c.get("quantity") or 1)
            result = sorted(
                [{"rarity": k, "count": v} for k, v in counter.items()],
                key=lambda x: x["count"],
                reverse=True,
            )
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/rarity: %s", e)
        raise HTTPException(status_code=500, detail="Analytics computation failed") from e


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
    color_identity: Optional[str] = Query(default=None),
    cmc: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id),
):
    """Count of cards per color identity for the filtered collection.

    Postgres path: SQL GROUP BY + Python normalization of color identity strings.
    Sheets path: in-memory Counter.
    """
    key = _cache_key(
        "color-identity", user_id, search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc
    )
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        repo = get_collection_repo()
        if repo is not None:
            # SQL returns raw color_identity values; normalize in Python
            filters = _make_filters(search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc)
            rows = repo.get_cards_analytics(user_id=user_id, filters=filters, dimension="color_identity")
            counter: Counter = Counter()
            for r in rows:
                normalized = _normalize_color_identity(r["label"])
                counter[normalized] += r["count"]
            result = sorted(
                [{"color_identity": k, "count": v} for k, v in counter.items()],
                key=lambda x: x["count"],
                reverse=True,
            )
        else:
            cards = _filtered_collection(
                search,
                rarity,
                type_filter,
                set_name,
                price_min,
                price_max,
                color_identity=color_identity,
                cmc=cmc,
                user_id=user_id,
            )
            counter = Counter()
            for c in cards:
                identity = _normalize_color_identity(c.get("color_identity") or c.get("identity") or "")
                counter[identity] += int(c.get("quantity") or 1)
            result = sorted(
                [{"color_identity": k, "count": v} for k, v in counter.items()],
                key=lambda x: x["count"],
                reverse=True,
            )
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/color-identity: %s", e)
        raise HTTPException(status_code=500, detail="Analytics computation failed") from e


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
    color_identity: Optional[str] = Query(default=None),
    cmc: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id),
):
    """Count of cards per CMC bucket for the filtered collection. 7+ grouped.

    Postgres path: SQL CASE bucketing via GROUP BY.
    Sheets path: in-memory bucketing.
    """
    key = _cache_key("cmc", user_id, search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc)
    cached = _get_cached(key)
    if cached is not None:
        return cached

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

    try:
        repo = get_collection_repo()
        if repo is not None:
            filters = _make_filters(search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc)
            rows = repo.get_cards_analytics(user_id=user_id, filters=filters, dimension="cmc")
            unsorted = [{"cmc": r["label"], "count": r["count"]} for r in rows]
            result = sorted(unsorted, key=sort_key)
        else:
            cards = _filtered_collection(
                search,
                rarity,
                type_filter,
                set_name,
                price_min,
                price_max,
                color_identity=color_identity,
                cmc=cmc,
                user_id=user_id,
            )
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
                counter[bucket] += int(c.get("quantity") or 1)
            result = sorted(
                [{"cmc": k, "count": v} for k, v in counter.items()],
                key=sort_key,
            )
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/cmc: %s", e)
        raise HTTPException(status_code=500, detail="Analytics computation failed") from e


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
    color_identity: Optional[str] = Query(default=None),
    cmc: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
):
    """Top N sets by card count for the filtered collection.

    Postgres path: SQL GROUP BY set_name with LIMIT.
    Sheets path: in-memory Counter.
    """
    key = _cache_key(
        "sets",
        user_id,
        search,
        rarity,
        type_filter,
        set_name,
        price_min,
        price_max,
        color_identity,
        cmc,
        extra=str(limit),
    )
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        repo = get_collection_repo()
        if repo is not None:
            filters = _make_filters(search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc)
            rows = repo.get_cards_analytics(user_id=user_id, filters=filters, dimension="set_name", limit=limit)
            result = [{"set_name": r["label"], "count": r["count"]} for r in rows]
        else:
            cards = _filtered_collection(
                search,
                rarity,
                type_filter,
                set_name,
                price_min,
                price_max,
                color_identity=color_identity,
                cmc=cmc,
                user_id=user_id,
            )
            counter: Counter = Counter()
            for c in cards:
                s = (c.get("set_name") or "Unknown").strip()
                if s:
                    counter[s] += int(c.get("quantity") or 1)
            most_common = counter.most_common(limit)
            result = [{"set_name": k, "count": v} for k, v in most_common]
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/sets: %s", e)
        raise HTTPException(status_code=500, detail="Analytics computation failed") from e


# ---------------------------------------------------------------------------
# GET /api/analytics/type
# ---------------------------------------------------------------------------
@router.get("/type", response_model=list[TypeCount])
async def analytics_type(
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
    """Count of cards per primary type for the filtered collection.

    Postgres path: SQL query to fetch filtered type_lines + Python primary-type extraction.
    Sheets path: in-memory Counter with Python extraction.

    Note: Primary type extraction requires Python logic (_extract_primary_type) which is
    complex to replicate in SQL, so we use a hybrid approach for Postgres: SQL filtering
    + Python aggregation on a lightweight query (type_line + quantity only).
    """
    key = _cache_key("type", user_id, search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        repo = get_collection_repo()
        if repo is not None:
            filters_dict = _make_filters(
                search, rarity, type_filter, set_name, price_min, price_max, color_identity, cmc
            )
            rows = repo.get_type_line_data(user_id=user_id, filters=filters_dict)
            counter: Counter = Counter()
            for row in rows:
                primary = _extract_primary_type(row.get("type_line") or "")
                counter[primary] += int(row.get("quantity") or 1)
        else:
            cards = _filtered_collection(
                search,
                rarity,
                type_filter,
                set_name,
                price_min,
                price_max,
                color_identity=color_identity,
                cmc=cmc,
                user_id=user_id,
            )
            counter = Counter()
            for c in cards:
                raw_type = c.get("type_line") or c.get("type") or ""
                primary = _extract_primary_type(raw_type)
                counter[primary] += int(c.get("quantity") or 1)

        result = sorted(
            [{"type_line": k, "count": v} for k, v in counter.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
        _set_cached(key, result)
        return result
    except Exception as e:
        logger.error("Error in analytics/type: %s", e)
        raise HTTPException(status_code=500, detail="Analytics computation failed") from e
