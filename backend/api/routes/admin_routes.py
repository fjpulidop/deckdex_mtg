"""Admin-only API routes.

All endpoints require the ``require_admin`` dependency, which in turn
requires authentication (``get_current_user``).  Non-admin users receive 403.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from ..dependencies import (
    require_admin,
    get_catalog_repo,
    get_image_store,
    get_job_repo,
)
from ..services import catalog_service
from deckdex.config_loader import load_config

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _get_catalog_repo_or_501():
    """Return catalog repo or raise 501 if catalog system is unavailable."""
    repo = get_catalog_repo()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Catalog system not available",
        )
    return repo


@router.post("/catalog/sync")
async def trigger_catalog_sync(user: dict = Depends(require_admin)):
    """Start a catalog sync background job.

    Returns 409 if a sync is already running, 501 if catalog unavailable.
    """
    catalog_repo = _get_catalog_repo_or_501()
    image_store = get_image_store()
    job_repo = get_job_repo()

    config = load_config(profile=os.getenv("DECKDEX_PROFILE", "default"))

    try:
        job_id = catalog_service.start_sync(
            catalog_repo=catalog_repo,
            image_store=image_store,
            job_repo=job_repo,
            bulk_data_url=config.catalog.bulk_data_url,
            image_size=config.catalog.image_size,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Catalog sync already in progress",
        )

    logger.info(f"Admin {user.get('email')} triggered catalog sync: {job_id}")
    return {"job_id": job_id, "status": "started", "message": "Catalog sync started"}


@router.get("/catalog/sync/status")
async def get_catalog_sync_status(user: dict = Depends(require_admin)):
    """Return the current catalog sync state."""
    catalog_repo = _get_catalog_repo_or_501()
    return catalog_service.get_sync_status(catalog_repo)
