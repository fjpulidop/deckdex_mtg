"""UserSettingsRepository: per-user settings stored as JSONB in PostgreSQL."""

import json
from typing import Any, Dict

from sqlalchemy import create_engine, text


_DEFAULT_EXTERNAL_APIS = {"scryfall_enabled": False}


class UserSettingsRepository:
    """Read/write user settings from the ``user_settings`` table."""

    def __init__(self, database_url: str, engine=None):
        self._database_url = database_url
        self._eng = engine

    def _engine(self):
        if self._eng is None:
            self._eng = create_engine(self._database_url)
        return self._eng

    # ------------------------------------------------------------------
    # Low-level: full JSONB blob
    # ------------------------------------------------------------------

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Return the full settings dict for *user_id*, or ``{}``."""
        with self._engine().connect() as conn:
            row = conn.execute(
                text("SELECT settings FROM user_settings WHERE user_id = :uid"),
                {"uid": user_id},
            ).fetchone()
        if row is None:
            return {}
        val = row[0]
        if isinstance(val, str):
            return json.loads(val)
        return val if isinstance(val, dict) else {}

    def upsert_user_settings(self, user_id: int, settings: Dict[str, Any]) -> None:
        """Insert or update the full settings blob for *user_id*."""
        blob = json.dumps(settings)
        with self._engine().connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO user_settings (user_id, settings, updated_at)
                    VALUES (:uid, :settings::jsonb, now())
                    ON CONFLICT (user_id)
                    DO UPDATE SET settings = :settings::jsonb, updated_at = now()
                """),
                {"uid": user_id, "settings": blob},
            )
            conn.commit()

    # ------------------------------------------------------------------
    # High-level: external_apis sub-key
    # ------------------------------------------------------------------

    def get_external_apis_settings(self, user_id: int) -> Dict[str, Any]:
        """Return ``external_apis`` sub-object, with defaults applied."""
        all_settings = self.get_user_settings(user_id)
        stored = all_settings.get("external_apis")
        if not isinstance(stored, dict):
            return dict(_DEFAULT_EXTERNAL_APIS)
        return {**_DEFAULT_EXTERNAL_APIS, **stored}

    def update_external_apis_settings(self, user_id: int, settings: Dict[str, Any]) -> None:
        """Merge *settings* into the ``external_apis`` key (upserts the row)."""
        all_settings = self.get_user_settings(user_id)
        ea = all_settings.get("external_apis", {})
        if not isinstance(ea, dict):
            ea = {}
        ea.update(settings)
        all_settings["external_apis"] = ea
        self.upsert_user_settings(user_id, all_settings)
