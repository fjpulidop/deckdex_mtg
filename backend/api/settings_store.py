"""
App settings storage (e.g. Scryfall credentials JSON).
Stores the credentials content internally so the backend remembers it.
Uses a JSON file so no DB migrations are required.
"""
import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger

# Project root: backend/api/settings_store.py -> backend -> project root
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent.parent
_SETTINGS_DIR = _PROJECT_ROOT / "data"
_SETTINGS_FILE = _SETTINGS_DIR / "settings.json"

KEY_SCRYFALL_CREDENTIALS = "scryfall_credentials"


def _ensure_dir() -> None:
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def _read_all() -> dict:
    """Read full settings dict from file. Returns {} if file missing or invalid."""
    if not _SETTINGS_FILE.exists():
        return {}
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not read settings file {_SETTINGS_FILE}: {e}")
        return {}


def _write_all(data: dict) -> None:
    _ensure_dir()
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_scryfall_credentials() -> Optional[dict]:
    """Return stored Scryfall credentials (JSON object), or None if not configured."""
    data = _read_all()
    creds = data.get(KEY_SCRYFALL_CREDENTIALS)
    if creds is None:
        return None
    if isinstance(creds, dict) and creds:
        return creds
    return None


def set_scryfall_credentials(credentials: Optional[dict]) -> None:
    """Store or clear Scryfall credentials (JSON object). None or empty dict clears it."""
    data = _read_all()
    if credentials and isinstance(credentials, dict) and credentials:
        data[KEY_SCRYFALL_CREDENTIALS] = credentials
    else:
        data.pop(KEY_SCRYFALL_CREDENTIALS, None)
    _write_all(data)
