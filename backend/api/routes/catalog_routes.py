"""Catalog API routes: search, autocomplete, card details, images, sync."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from loguru import logger

from ..dependencies import get_current_user_id
from ..services import catalog_service

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def _get_catalog_repo():
    """Lazy import to avoid circular deps; returns CatalogRepository or raises 501."""
    from ..dependencies import get_catalog_repo
    repo = get_catalog_repo()
    if repo is None:
        raise HTTPException(status_code=501, detail="Catalog requires PostgreSQL (DATABASE_URL)")
    return repo


def _get_stores():
    """Return (catalog_repo, image_store) or raise 501."""
    from ..dependencies import get_catalog_repo, get_image_store
    repo = get_catalog_repo()
    if repo is None:
        raise HTTPException(status_code=501, detail="Catalog requires PostgreSQL (DATABASE_URL)")
    return repo, get_image_store()


# ------------------------------------------------------------------
# Search & lookup
# ------------------------------------------------------------------

@router.get("/search")
async def search_cards(
    q: str = Query("", min_length=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
):
    """Search catalog cards by name (case-insensitive contains)."""
    repo = _get_catalog_repo()
    results = catalog_service.search(repo, q, limit=limit)
    return results


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query("", min_length=2),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
):
    """Return matching card names for autocomplete."""
    repo = _get_catalog_repo()
    return catalog_service.autocomplete(repo, q, limit=limit)


@router.get("/cards/{scryfall_id}")
async def get_card(
    scryfall_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Return a single catalog card by scryfall_id."""
    repo = _get_catalog_repo()
    card = catalog_service.get_card(repo, scryfall_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found in catalog")
    return card


@router.get("/cards/{scryfall_id}/image")
async def get_card_image(
    scryfall_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Serve a catalog card image from filesystem."""
    _, image_store = _get_stores()
    result = catalog_service.get_image(image_store, scryfall_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Image not found")
    data, content_type = result
    return Response(content=data, media_type=content_type)


# ------------------------------------------------------------------
# Sync
# ------------------------------------------------------------------

@router.post("/sync")
async def trigger_sync(
    user_id: int = Depends(get_current_user_id),
):
    """Trigger a catalog sync job.  Returns job_id.  409 if already running."""
    from ..dependencies import get_job_repo, get_image_store, get_catalog_repo
    from deckdex.config_loader import load_config
    import os

    repo = get_catalog_repo()
    if repo is None:
        raise HTTPException(status_code=501, detail="Catalog requires PostgreSQL (DATABASE_URL)")

    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))

    try:
        job_id = catalog_service.start_sync(
            catalog_repo=repo,
            image_store=get_image_store(),
            job_repo=get_job_repo(),
            bulk_data_url=config.catalog.bulk_data_url,
            image_size=config.catalog.image_size,
        )
    except RuntimeError:
        raise HTTPException(status_code=409, detail="A catalog sync is already running")

    return {"job_id": job_id}


@router.get("/sync/status")
async def sync_status(
    user_id: int = Depends(get_current_user_id),
):
    """Return current catalog sync state."""
    repo = _get_catalog_repo()
    return catalog_service.get_sync_status(repo)
