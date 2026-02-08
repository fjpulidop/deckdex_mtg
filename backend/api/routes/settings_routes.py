"""
Settings API: Scryfall credentials and other app settings.
Credentials are stored as JSON internally; the backend remembers them.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ..settings_store import (
    get_scryfall_credentials,
    set_scryfall_credentials,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ScryfallCredentialsResponse(BaseModel):
    configured: bool


class ScryfallCredentialsUpdate(BaseModel):
    credentials: dict | None = None


@router.get("/scryfall-credentials", response_model=ScryfallCredentialsResponse)
async def get_scryfall_credentials_status():
    """
    Return whether Scryfall credentials are configured.
    The stored JSON is not returned for security.
    """
    creds = get_scryfall_credentials()
    return ScryfallCredentialsResponse(configured=creds is not None)


@router.put("/scryfall-credentials", response_model=ScryfallCredentialsResponse)
async def put_scryfall_credentials(body: ScryfallCredentialsUpdate):
    """
    Store or clear the Scryfall credentials JSON.
    Send { "credentials": { ... } } with the JSON content to save; { "credentials": null } to clear.
    The backend stores it internally and will use it on the next run.
    """
    set_scryfall_credentials(body.credentials)
    creds = get_scryfall_credentials()
    return ScryfallCredentialsResponse(configured=creds is not None)
