"""Catalog repository: read/write access to the catalog_cards and catalog_sync_state tables."""

from typing import Dict, Any, List, Optional

from loguru import logger


class CatalogRepository:
    """PostgreSQL-backed repository for the global card catalog."""

    def __init__(self, database_url: str, engine=None):
        if engine is None and (not database_url or not database_url.strip().startswith("postgresql")):
            raise ValueError("database_url must be a non-empty postgresql:// URL")
        self._url = database_url
        self._eng = engine

    def _engine(self):
        from sqlalchemy import create_engine
        if self._eng is None:
            self._eng = create_engine(self._url, pool_pre_ping=True)
        return self._eng

    # ------------------------------------------------------------------
    # Card lookups
    # ------------------------------------------------------------------

    def search_by_name(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Return catalog cards whose name contains *query* (case-insensitive)."""
        from sqlalchemy import text
        if not query or not query.strip():
            return []
        with self._engine().connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT * FROM catalog_cards
                    WHERE name ILIKE :pattern
                    ORDER BY name
                    LIMIT :lim
                """),
                {"pattern": f"%{query.strip()}%", "lim": limit},
            ).mappings().fetchall()
            return [dict(r) for r in rows]

    def autocomplete(self, query: str, limit: int = 20) -> List[str]:
        """Return up to *limit* card names matching *query* prefix (case-insensitive)."""
        from sqlalchemy import text
        if not query or len(query.strip()) < 2:
            return []
        with self._engine().connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT DISTINCT name FROM catalog_cards
                    WHERE name ILIKE :pattern
                    ORDER BY name
                    LIMIT :lim
                """),
                {"pattern": f"{query.strip()}%", "lim": limit},
            ).fetchall()
            return [r[0] for r in rows]

    def get_by_scryfall_id(self, scryfall_id: str) -> Optional[Dict[str, Any]]:
        """Return a single catalog card by its Scryfall UUID, or None."""
        from sqlalchemy import text
        with self._engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM catalog_cards WHERE scryfall_id = :sid"),
                {"sid": scryfall_id},
            ).mappings().fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Bulk write (used by sync job)
    # ------------------------------------------------------------------

    def upsert_cards(self, cards: List[Dict[str, Any]]) -> int:
        """Batch UPSERT cards into catalog_cards.  Returns number of rows affected."""
        from sqlalchemy import text
        if not cards:
            return 0
        cols = [
            "scryfall_id", "oracle_id", "name", "type_line", "oracle_text",
            "mana_cost", "cmc", "colors", "color_identity", "power", "toughness",
            "rarity", "set_id", "set_name", "collector_number", "release_date",
            "image_uri_small", "image_uri_normal", "image_uri_large",
            "prices_eur", "prices_usd", "prices_usd_foil", "edhrec_rank",
            "keywords", "legalities", "scryfall_uri",
        ]
        placeholders = ", ".join(f":{c}" for c in cols)
        col_names = ", ".join(cols)
        update_set = ", ".join(
            f"{c} = EXCLUDED.{c}" for c in cols if c != "scryfall_id"
        )
        sql = text(f"""
            INSERT INTO catalog_cards ({col_names}, synced_at)
            VALUES ({placeholders}, NOW())
            ON CONFLICT (scryfall_id) DO UPDATE SET {update_set}, synced_at = NOW()
        """)
        count = 0
        with self._engine().connect() as conn:
            for card in cards:
                params = {c: card.get(c) for c in cols}
                # legalities may be a dict; SQLAlchemy handles JSONB automatically
                conn.execute(sql, params)
                count += 1
            conn.commit()
        return count

    # ------------------------------------------------------------------
    # Image status tracking
    # ------------------------------------------------------------------

    def update_image_status(self, scryfall_id: str, status: str) -> None:
        """Set image_status for a catalog card."""
        from sqlalchemy import text
        with self._engine().connect() as conn:
            conn.execute(
                text("UPDATE catalog_cards SET image_status = :st WHERE scryfall_id = :sid"),
                {"st": status, "sid": scryfall_id},
            )
            conn.commit()

    def get_pending_images(
        self, after_cursor: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return cards with image_status='pending', ordered by scryfall_id.

        If *after_cursor* is provided, only return cards with scryfall_id > cursor.
        """
        from sqlalchemy import text
        if after_cursor:
            sql = text("""
                SELECT scryfall_id, image_uri_normal, image_uri_small, image_uri_large
                FROM catalog_cards
                WHERE image_status = 'pending' AND scryfall_id > :cursor
                ORDER BY scryfall_id
                LIMIT :lim
            """)
            params = {"cursor": after_cursor, "lim": limit}
        else:
            sql = text("""
                SELECT scryfall_id, image_uri_normal, image_uri_small, image_uri_large
                FROM catalog_cards
                WHERE image_status = 'pending'
                ORDER BY scryfall_id
                LIMIT :lim
            """)
            params = {"lim": limit}
        with self._engine().connect() as conn:
            rows = conn.execute(sql, params).mappings().fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Sync state
    # ------------------------------------------------------------------

    def get_sync_state(self) -> Dict[str, Any]:
        """Return the singleton catalog_sync_state row."""
        from sqlalchemy import text
        with self._engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM catalog_sync_state WHERE id = 1")
            ).mappings().fetchone()
            if row is None:
                return {"status": "idle", "total_cards": 0, "total_images_downloaded": 0}
            result = dict(row)
            # Serialize datetimes
            for k in ("last_bulk_sync", "updated_at"):
                v = result.get(k)
                if v and hasattr(v, "isoformat"):
                    result[k] = v.isoformat()
            return result

    def update_sync_state(self, **fields) -> None:
        """Update catalog_sync_state columns.  Pass only the fields to change."""
        from sqlalchemy import text
        if not fields:
            return
        set_parts = [f"{k} = :{k}" for k in fields]
        set_parts.append("updated_at = NOW()")
        sql = text(f"UPDATE catalog_sync_state SET {', '.join(set_parts)} WHERE id = 1")
        with self._engine().connect() as conn:
            conn.execute(sql, fields)
            conn.commit()

    def count_cards(self) -> int:
        """Return total number of rows in catalog_cards."""
        from sqlalchemy import text
        with self._engine().connect() as conn:
            return conn.execute(text("SELECT COUNT(*) FROM catalog_cards")).scalar() or 0

    def count_downloaded_images(self) -> int:
        """Return number of catalog cards with image_status='downloaded'."""
        from sqlalchemy import text
        with self._engine().connect() as conn:
            return conn.execute(
                text("SELECT COUNT(*) FROM catalog_cards WHERE image_status = 'downloaded'")
            ).scalar() or 0
