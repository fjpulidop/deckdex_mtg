"""
Cards API routes
Endpoints for accessing card collection data
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from ..dependencies import clear_collection_cache, get_cached_collection, get_collection_repo, get_current_user_id
from ..filters import filter_collection
from ..main import limiter
from ..services.card_image_service import get_card_image_path
from ..services.scryfall_service import CardNotFoundError, resolve_card_by_name, suggest_card_names
from .stats import clear_stats_cache

router = APIRouter(prefix="/api/cards", tags=["cards"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


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
    created_at: Optional[str] = None  # ISO timestamp when card was added
    quantity: Optional[int] = 1

    class Config:
        from_attributes = True


class CardListResponse(BaseModel):
    """Paginated card list response with server-side total count.

    BREAKING CHANGE: /api/cards now returns this wrapper instead of List[Card].
    Clients must access .items to get the card array and .total for pagination controls.
    """

    items: List[Card]
    total: int
    limit: int
    offset: int

    class Config:
        from_attributes = True


class FilterOptions(BaseModel):
    """Distinct type and set values for filter dropdowns."""

    types: List[str]
    sets: List[str]


class PriceHistoryPoint(BaseModel):
    recorded_at: str
    price: float
    source: str
    currency: str


class PriceHistoryResponse(BaseModel):
    card_id: int
    currency: str
    points: List[PriceHistoryPoint]


# ---------------------------------------------------------------------------
# GET /api/cards/filter-options  (must be registered before /{card_id_or_name})
# ---------------------------------------------------------------------------


@router.get("/filter-options", response_model=FilterOptions)
async def get_filter_options(
    user_id: int = Depends(get_current_user_id),
):
    """Return distinct type_line and set_name values for filter dropdowns.

    Postgres path: two DISTINCT SQL queries (no full collection load).
    Sheets path: derive from cached collection.
    """
    repo = get_collection_repo()
    if repo is not None:
        try:
            options = repo.get_filter_options(user_id=user_id)
            return FilterOptions(types=options["types"], sets=options["sets"])
        except Exception as e:
            logger.error("Error fetching filter options from DB: %s", e)
            raise HTTPException(status_code=500, detail="Failed to fetch filter options")
    else:
        try:
            collection = get_cached_collection(user_id=user_id)
            types = sorted({str(c.get("type") or "") for c in collection if c.get("type")})
            sets = sorted({str(c.get("set_name") or "") for c in collection if c.get("set_name")})
            return FilterOptions(types=types, sets=sets)
        except Exception as e:
            logger.error("Error deriving filter options from collection: %s", e)
            raise HTTPException(status_code=500, detail="Failed to fetch filter options")


# ---------------------------------------------------------------------------
# GET /api/cards/suggest  (must be before /{card_id_or_name})
# ---------------------------------------------------------------------------


@router.get("/suggest", response_model=List[str])
async def suggest_cards(
    q: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id),
):
    """
    Return card name suggestions (catalog-first, Scryfall fallback if enabled).
    Query param q: search string. If missing or length < 2, returns empty array.
    """
    if not q or len(q.strip()) < 2:
        return []
    return suggest_card_names(q.strip(), user_id=user_id)


# ---------------------------------------------------------------------------
# GET /api/cards/resolve  (must be before /{card_id_or_name})
# ---------------------------------------------------------------------------


@router.get("/resolve", response_model=Card)
async def resolve_card(
    name: Optional[str] = Query(default=None, alias="name"), user_id: int = Depends(get_current_user_id)
):
    """
    Resolve a card by name: return full card payload (type, rarity, set_name, price, ...)
    from Scryfall (or from collection if already present) for use in POST create.
    Returns 404 if card cannot be resolved.
    """
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Query param 'name' is required")
    try:
        collection = get_cached_collection(user_id=user_id)
        name_lower = name.strip().lower()
        from_coll = next((c for c in collection if (c.get("name") or "").lower() == name_lower), None)
        payload = resolve_card_by_name(name.strip(), from_collection=from_coll, user_id=user_id)
        return Card(**{k: v for k, v in payload.items() if k in Card.model_fields})
    except CardNotFoundError:
        raise HTTPException(status_code=404, detail="Card not found")


# ---------------------------------------------------------------------------
# GET /api/cards/  — paginated list
# ---------------------------------------------------------------------------


_ALLOWED_SORT_COLUMNS = {"name", "created_at", "price_eur", "quantity", "set_name", "rarity", "cmc"}


@router.get("/", response_model=CardListResponse)
@limiter.limit("60/minute")
async def list_cards(
    request: Request,
    limit: int = Query(default=100, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    rarity: Optional[str] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    color_identity: Optional[str] = Query(default=None),
    set_name: Optional[str] = Query(default=None),
    price_min: Optional[str] = Query(default=None),
    price_max: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_dir: Optional[str] = Query(default="desc"),
    user_id: int = Depends(get_current_user_id),
):
    """
    List cards from collection with pagination, filters, and server-side sorting.
    Returns paginated wrapper: { items, total, limit, offset }.

    Same filter semantics as GET /api/stats so list and stats stay in sync.
    type: substring match on type line (e.g. "Creature" matches "Creature — Elf").
    color_identity: comma-separated WUBRG (e.g. "W,U"); card must contain all listed colors.
    sort_by: one of name, created_at, price_eur, quantity, set_name, rarity, cmc (default: created_at).
    sort_dir: asc or desc (default: desc).

    Postgres path: SQL-level filtering, sorting, and pagination (no full collection load).
    Sheets path: cached collection + Python filtering (no server-side sorting).
    """
    # Validate and sanitize sort params — unknown values fall back to defaults
    resolved_sort_by = sort_by if sort_by in _ALLOWED_SORT_COLUMNS else "created_at"
    resolved_sort_dir = sort_dir if sort_dir in ("asc", "desc") else "desc"

    logger.info(
        "GET /api/cards - limit=%s, offset=%s, search=%s, type=%s, color_identity=%s, set_name=%s, sort_by=%s, sort_dir=%s, user=%s",
        limit,
        offset,
        search,
        type_filter,
        color_identity,
        set_name,
        resolved_sort_by,
        resolved_sort_dir,
        user_id,
    )
    try:
        search_param = search if search and search != "undefined" else None
        repo = get_collection_repo()
        if repo is not None:
            # Postgres path: SQL-level filtering, sorting, and pagination
            filters = {
                "search": search_param,
                "rarity": rarity,
                "type_": type_filter,
                "color_identity": color_identity,
                "set_name": set_name,
                "price_min": price_min,
                "price_max": price_max,
            }
            items, total = repo.get_cards_filtered(
                user_id=user_id,
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=resolved_sort_by,
                sort_dir=resolved_sort_dir,
            )
        else:
            # Sheets path: load all, filter in Python, slice
            collection = get_cached_collection(user_id=user_id)
            filtered = filter_collection(
                collection,
                search=search_param,
                rarity=rarity,
                type_=type_filter,
                color_identity=color_identity,
                set_name=set_name,
                price_min=price_min,
                price_max=price_max,
            )
            total = len(filtered)
            items = filtered[offset : offset + limit]

        logger.info("Returning %s cards (total: %s, offset: %s)", len(items), total, offset)
        return CardListResponse(items=items, total=total, limit=limit, offset=offset)

    except Exception as e:
        logger.error(f"Error listing cards: {e}")

        if "Quota exceeded" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Google Sheets API quota exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )

        raise HTTPException(status_code=500, detail="Failed to fetch cards")


# ---------------------------------------------------------------------------
# GET /api/cards/{id}/image
# ---------------------------------------------------------------------------


@router.get("/{id}/image")
async def get_card_image(id: int, user_id: int = Depends(get_current_user_id)):
    """Return the card's image by surrogate id.

    Served via FileResponse (zero-copy). Cache-Control: immutable (1 year).
    Any authenticated user may request any card image — ownership is not required.
    Returns 404 if card not found or image unavailable.
    """
    try:
        file_path, media_type, etag = get_card_image_path(id, user_id=user_id)
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": etag,
            },
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Card or image not found")


# ---------------------------------------------------------------------------
# GET /api/cards/{id}/price-history
# ---------------------------------------------------------------------------


@router.get("/{id}/price-history", response_model=PriceHistoryResponse)
async def get_card_price_history(
    id: int,
    days: int = Query(default=90, ge=1, le=365),
    user_id: int = Depends(get_current_user_id),
):
    """
    Return price history for a card over the last `days` days (default: 90, max: 365).
    Points are ordered oldest-first for chart rendering.
    Returns empty points list (not an error) if card exists but has no history yet.
    Requires PostgreSQL. Returns 501 if DATABASE_URL is not set.
    """
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Price history requires PostgreSQL. Set DATABASE_URL.",
        )
    card = repo.get_card_by_id(id, user_id=user_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Card id {id} not found")
    try:
        points = repo.get_price_history(id, days=days)
        return PriceHistoryResponse(
            card_id=id,
            currency="eur",
            points=[PriceHistoryPoint(**p) for p in points],
        )
    except Exception as e:
        logger.error("Error fetching price history for card %s: %s", id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch price history")


# ---------------------------------------------------------------------------
# GET /api/cards/{card_id_or_name}
# ---------------------------------------------------------------------------


@router.get("/{card_id_or_name}", response_model=Card)
async def get_card(card_id_or_name: str, user_id: int = Depends(get_current_user_id)):
    """
    Get details for a specific card by surrogate id (integer) or by name (string).

    Args:
        card_id_or_name: Numeric id (e.g. 42) or card name (e.g. Black Lotus)

    Returns:
        Card details

    Raises:
        HTTPException: 404 if card not found
    """
    logger.info(f"GET /api/cards/{card_id_or_name} - user={user_id}")

    try:
        repo = get_collection_repo()
        if repo is not None:
            # Try as id first (numeric path segment)
            try:
                card_id = int(card_id_or_name)
                card = repo.get_card_by_id(card_id, user_id=user_id)
                if card is not None:
                    return card
            except ValueError:
                pass
            # Fall back to get by name
            collection = get_cached_collection(user_id=user_id)
            card_name_lower = card_id_or_name.lower()
            for card in collection:
                if card.get("name") and card["name"].lower() == card_name_lower:
                    return card
            raise HTTPException(status_code=404, detail=f"Card '{card_id_or_name}' not found")

        # No repo: use collection (Sheets)
        collection = get_cached_collection(user_id=user_id)
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
        raise HTTPException(status_code=500, detail="Failed to fetch card")


# ---------------------------------------------------------------------------
# POST /api/cards/
# ---------------------------------------------------------------------------


@router.post("/", response_model=Card, status_code=201)
@limiter.limit("30/minute")
async def create_card(request: Request, card: Card, user_id: int = Depends(get_current_user_id)):
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
        created = repo.create(payload, user_id=user_id)
        clear_collection_cache(user_id=user_id)
        clear_stats_cache()
        return created
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        raise HTTPException(status_code=400, detail="Failed to create card")


# ---------------------------------------------------------------------------
# PUT /api/cards/{id}
# ---------------------------------------------------------------------------


@router.put("/{id}", response_model=Card)
@limiter.limit("30/minute")
async def update_card(request: Request, id: int, card: Card, user_id: int = Depends(get_current_user_id)):
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
        updated = repo.update(id, payload, user_id=user_id)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Card id {id} not found")
        clear_collection_cache(user_id=user_id)
        clear_stats_cache()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating card {id}: {e}")
        raise HTTPException(status_code=400, detail="Failed to update card")


# ---------------------------------------------------------------------------
# PATCH /api/cards/{id}/quantity
# ---------------------------------------------------------------------------


@router.patch("/{id}/quantity")
@limiter.limit("30/minute")
async def update_card_quantity(
    request: Request,
    id: int,
    body: Dict[str, Any],
    user_id: int = Depends(get_current_user_id),
):
    """Partial update: set quantity for a card (inline edit from the card table)."""
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(status_code=501, detail="Requires PostgreSQL. Set DATABASE_URL.")
    try:
        quantity = int(body.get("quantity", 1))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="quantity must be an integer")
    if quantity < 1:
        raise HTTPException(status_code=400, detail="quantity must be >= 1")
    updated = repo.update_quantity(id, quantity, user_id=user_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Card id {id} not found")
    clear_collection_cache(user_id=user_id)
    clear_stats_cache()
    return {"id": id, "quantity": quantity}


# ---------------------------------------------------------------------------
# DELETE /api/cards/{id}
# ---------------------------------------------------------------------------


@router.delete("/{id}", status_code=204)
@limiter.limit("30/minute")
async def delete_card(request: Request, id: int, user_id: int = Depends(get_current_user_id)):
    """
    Delete a card by surrogate id. Requires Postgres.
    """
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(
            status_code=501,
            detail="Card delete requires PostgreSQL. Set DATABASE_URL.",
        )
    deleted = repo.delete(id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Card id {id} not found")
    clear_collection_cache(user_id=user_id)
    clear_stats_cache()
