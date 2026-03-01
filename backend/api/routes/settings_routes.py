"""
Settings API: Scryfall credentials, external API toggles, and other app settings.
Credentials are stored as JSON internally; per-user settings in PostgreSQL.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..settings_store import (
    get_scryfall_credentials,
    set_scryfall_credentials,
)
from ..dependencies import get_current_user_id, get_user_settings_repo

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ScryfallCredentialsResponse(BaseModel):
    configured: bool


class ScryfallCredentialsUpdate(BaseModel):
    credentials: dict | None = None


@router.get("/scryfall-credentials", response_model=ScryfallCredentialsResponse)
async def get_scryfall_credentials_status(user_id: int = Depends(get_current_user_id)):
    """
    Return whether Scryfall credentials are configured.
    The stored JSON is not returned for security.
    """
    creds = get_scryfall_credentials()
    return ScryfallCredentialsResponse(configured=creds is not None)


@router.put("/scryfall-credentials", response_model=ScryfallCredentialsResponse)
async def put_scryfall_credentials(body: ScryfallCredentialsUpdate, user_id: int = Depends(get_current_user_id)):
    """
    Store or clear the Scryfall credentials JSON.
    Send { "credentials": { ... } } with the JSON content to save; { "credentials": null } to clear.
    The backend stores it internally and will use it on the next run.
    """
    set_scryfall_credentials(body.credentials)
    creds = get_scryfall_credentials()
    return ScryfallCredentialsResponse(configured=creds is not None)


# --- External APIs per-user settings ---


class ExternalApisSettingsResponse(BaseModel):
    scryfall_enabled: bool


class ExternalApisSettingsUpdate(BaseModel):
    scryfall_enabled: bool


@router.get("/external-apis", response_model=ExternalApisSettingsResponse)
async def get_external_apis_settings(user_id: int = Depends(get_current_user_id)):
    """Return the current user's external API preferences."""
    repo = get_user_settings_repo()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User settings require PostgreSQL",
        )
    settings = repo.get_external_apis_settings(user_id)
    return ExternalApisSettingsResponse(**settings)


@router.put("/external-apis", response_model=ExternalApisSettingsResponse)
async def put_external_apis_settings(
    body: ExternalApisSettingsUpdate,
    user_id: int = Depends(get_current_user_id),
):
    """Update the current user's external API preferences."""
    repo = get_user_settings_repo()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User settings require PostgreSQL",
        )
    repo.update_external_apis_settings(user_id, body.model_dump())
    settings = repo.get_external_apis_settings(user_id)
    return ExternalApisSettingsResponse(**settings)
