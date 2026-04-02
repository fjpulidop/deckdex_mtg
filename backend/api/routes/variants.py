"""
Variants API routes
Endpoints for browsing card collection by variant/treatment groupings.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from ..dependencies import get_current_user_id
from ..services import variant_service

router = APIRouter(prefix="/api/collection/variants", tags=["variants"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class VariantCopy(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    finish: str
    variant_label: str
    condition: Optional[str] = None
    quantity: int
    price: Optional[str] = None
    promo_types: Optional[str] = None
    frame_effects: Optional[str] = None
    border_color: Optional[str] = None
    created_at: Optional[str] = None


class VariantSlot(BaseModel):
    """One slot in the set's known variants; owned=True when user owns at least one copy."""

    model_config = ConfigDict(from_attributes=True)

    variant_label: str
    finish: str
    owned: bool
    copies: List[VariantCopy]
    scryfall_image_uri: Optional[str] = None


class CardVariantGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    card_name: str
    total_known_variants: int
    owned_variant_count: int
    slots: List[VariantSlot]


class CollectionVariantsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    groups: List[CardVariantGroup]
    total_cards: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=CollectionVariantsResponse)
async def list_collection_variants(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: int = Depends(get_current_user_id),
) -> CollectionVariantsResponse:
    """Return paginated list of card variant groups for the authenticated user's collection."""
    try:
        result = variant_service.get_collection_variants(
            user_id=user_id,
            search=search,
            limit=limit,
            offset=offset,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=501,
            detail="Variant view requires PostgreSQL. Set DATABASE_URL.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return CollectionVariantsResponse(**result)


@router.get("/{card_name}", response_model=CardVariantGroup)
async def get_card_variant_group(
    card_name: str,
    user_id: int = Depends(get_current_user_id),
) -> CardVariantGroup:
    """Return all variant slots for a single card name."""
    try:
        result = variant_service.get_card_variants(user_id=user_id, card_name=card_name)
    except RuntimeError:
        raise HTTPException(
            status_code=501,
            detail="Variant view requires PostgreSQL. Set DATABASE_URL.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return CardVariantGroup(**result)
