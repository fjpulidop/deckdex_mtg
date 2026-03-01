"""Collection repository: abstract interface and Postgres implementation."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

from loguru import logger


def _is_incomplete_card(card: Dict[str, Any]) -> bool:
    """True if card looks like 'new added' with only name (missing type_line / main Scryfall fields)."""
    type_line = card.get("type_line") or card.get("type")
    return not (type_line and str(type_line).strip())


def _serialize_created_at(value: Any) -> Optional[str]:
    """Convert DB created_at (datetime or None) to ISO string for API."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


# Card dict keys aligned with API and data-model (name, price, set_name, number/set_number, etc.)
def _row_to_card(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map DB row to API-style card dict (id, name, price, number, created_at, ...)."""
    card = {
        "id": row["id"],
        "name": row.get("name"),
        "english_name": row.get("english_name"),
        "type": row.get("type_line"),
        "description": row.get("description"),
        "keywords": row.get("keywords"),
        "mana_cost": row.get("mana_cost"),
        "cmc": row.get("cmc"),
        "colors": row.get("colors"),
        "color_identity": row.get("color_identity"),
        "power": row.get("power"),
        "toughness": row.get("toughness"),
        "rarity": row.get("rarity"),
        "price": row.get("price_eur") or row.get("price"),
        "release_date": row.get("release_date"),
        "set_id": row.get("set_id"),
        "set_name": row.get("set_name"),
        "number": row.get("set_number"),
        "edhrec_rank": row.get("edhrec_rank"),
        "game_strategy": row.get("game_strategy"),
        "tier": row.get("tier"),
        "created_at": _serialize_created_at(row.get("created_at")),
        "quantity": row.get("quantity", 1),
    }
    return {k: v for k, v in card.items() if v is not None or k in ("id", "quantity")}


def _safe_cmc(value: Any) -> Optional[float]:
    """Convert CMC to float for DB (double precision); treat N/A and invalid as None."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not (value != value):  # reject NaN
        return float(value)
    s = str(value).strip()
    if s in ("", "N/A", "n/a"):
        return None
    try:
        return float(s.replace(",", "."))
    except (ValueError, TypeError):
        return None


def _card_to_row(card: Dict[str, Any]) -> Dict[str, Any]:
    """Map API-style card dict to DB columns (type_line, set_number, price_eur). CMC normalized for double precision."""
    return {
        "name": card.get("name"),
        "english_name": card.get("english_name"),
        "type_line": card.get("type"),
        "description": card.get("description"),
        "keywords": card.get("keywords"),
        "mana_cost": card.get("mana_cost"),
        "cmc": _safe_cmc(card.get("cmc")),
        "colors": card.get("colors"),
        "color_identity": card.get("color_identity"),
        "power": card.get("power"),
        "toughness": card.get("toughness"),
        "rarity": card.get("rarity"),
        "set_id": card.get("set_id"),
        "set_name": card.get("set_name"),
        "set_number": card.get("number"),
        "release_date": card.get("release_date"),
        "edhrec_rank": card.get("edhrec_rank"),
        "scryfall_uri": card.get("scryfall_uri"),
        "price_eur": card.get("price"),
        "price_usd": card.get("price_usd"),
        "price_usd_foil": card.get("price_usd_foil"),
        "game_strategy": card.get("game_strategy"),
        "tier": card.get("tier"),
        "quantity": int(card.get("quantity") or 1),
    }


class CollectionRepository(ABC):
    """Abstract interface for card collection storage."""

    @abstractmethod
    def get_all_cards(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return all cards as list of dicts (API shape, including id). If user_id provided, filter by that user."""
        pass

    def get_cards_for_process(self, user_id: Optional[int] = None, only_incomplete: bool = False) -> List[Dict[str, Any]]:
        """Return cards to process. If only_incomplete=True, only cards that have e.g. only name (no type_line)."""
        cards = self.get_all_cards(user_id=user_id)
        if not only_incomplete:
            return cards
        return [c for c in cards if c.get("id") is not None and _is_incomplete_card(c)]

    @abstractmethod
    def get_cards_for_price_update(self, user_id: Optional[int] = None) -> List[tuple]:
        """Return list of (card_id, name_for_scryfall, current_price_str). If user_id provided, filter by that user."""
        pass

    @abstractmethod
    def get_card_by_id(self, id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Return one card by surrogate id or None. If user_id provided, verify ownership."""
        pass

    @abstractmethod
    def create(self, card: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """Insert a card; return the same card dict with id set. If user_id provided, associate with user."""
        pass

    @abstractmethod
    def update(self, id: int, fields: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Update card by id; return updated card or None if not found. If user_id provided, verify ownership."""
        pass

    @abstractmethod
    def delete(self, id: int, user_id: Optional[int] = None) -> bool:
        """Delete card by id; return True if deleted, False if not found. If user_id provided, verify ownership."""
        pass

    @abstractmethod
    def replace_all(self, cards: List[Dict[str, Any]], user_id: Optional[int] = None) -> int:
        """Replace entire collection with given cards (delete all, insert all). Return count inserted. If user_id provided, replace only user's cards."""
        pass

    def update_quantity(self, card_id: int, quantity: int, user_id: Optional[int] = None) -> bool:
        """Update quantity for a card by id. Returns True if updated, False if not found. If user_id provided, verify ownership."""
        return False

    def get_card_image_by_scryfall_id(self, scryfall_id: str) -> Optional[Tuple[bytes, str]]:
        """Return (image_bytes, content_type) from the global cache if stored, else None."""
        return None

    def save_card_image_to_global_cache(self, scryfall_id: str, content_type: str, data: bytes) -> None:
        """Upsert image into the global card_image_cache. No-op for repositories that do not store images."""
        pass

    def update_card_scryfall_id(self, card_id: int, scryfall_id: str) -> None:
        """Persist the scryfall_id on the cards row (lazy population). No-op if not supported."""
        pass

    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID. Returns user dict or None."""
        pass

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email. Returns user dict or None."""
        pass

    def create_user(self, google_id: str, email: str, display_name: Optional[str] = None, avatar_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user. Returns user dict with id."""
        pass

    def update_user_google_id(self, user_id: int, google_id: str) -> bool:
        """Update user's google_id. Returns True if successful."""
        pass

    def update_user_last_login(self, user_id: int) -> bool:
        """Update user's last_login timestamp. Returns True if successful."""
        pass

    def update_user_profile(self, user_id: int, display_name: Optional[str] = None, avatar_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user's display_name and/or avatar_url. Only updates provided (non-None) fields. Returns updated user dict or None if not found."""
        pass


class PostgresCollectionRepository(CollectionRepository):
    """PostgreSQL implementation of CollectionRepository."""

    def __init__(self, database_url: str, engine=None):
        if engine is None and (not database_url or not database_url.strip().startswith("postgresql")):
            raise ValueError("database_url must be a non-empty postgresql:// URL")
        self._url = database_url
        self._eng = engine

    def _get_engine(self):
        from sqlalchemy import create_engine
        if self._eng is None:
            self._eng = create_engine(self._url, pool_pre_ping=True)
        return self._eng

    def get_all_cards(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            if user_id is not None:
                rows = conn.execute(
                    text("SELECT * FROM cards WHERE user_id = :user_id ORDER BY created_at DESC NULLS LAST, id DESC"),
                    {"user_id": user_id}
                ).mappings().fetchall()
            else:
                rows = conn.execute(text("SELECT * FROM cards ORDER BY created_at DESC NULLS LAST, id DESC")).mappings().fetchall()
            return [_row_to_card(dict(r)) for r in rows]

    def get_cards_for_process(self, user_id: Optional[int] = None, only_incomplete: bool = False) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            if only_incomplete:
                where_clause = """
                    WHERE name IS NOT NULL AND name != ''
                    AND (type_line IS NULL OR TRIM(type_line) = '')
                """
                if user_id is not None:
                    where_clause += " AND user_id = :user_id"
                rows = conn.execute(text(f"""
                    SELECT * FROM cards
                    {where_clause}
                    ORDER BY id
                """), {"user_id": user_id} if user_id is not None else {}).mappings().fetchall()
            else:
                where_clause = ""
                if user_id is not None:
                    where_clause = "WHERE user_id = :user_id"
                rows = conn.execute(
                    text(f"SELECT * FROM cards {where_clause} ORDER BY id"),
                    {"user_id": user_id} if user_id is not None else {}
                ).mappings().fetchall()
            return [_row_to_card(dict(r)) for r in rows]

    def get_cards_for_price_update(self, user_id: Optional[int] = None) -> List[tuple]:
        """Return (card_id, name_for_scryfall, current_price_str). Uses english_name for Scryfall when set, else name."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            where_clause = "WHERE name IS NOT NULL AND name != ''"
            if user_id is not None:
                where_clause += " AND user_id = :user_id"
            rows = conn.execute(
                text(f"SELECT id, name, english_name, price_eur FROM cards {where_clause}"),
                {"user_id": user_id} if user_id is not None else {}
            ).fetchall()
            return [(r[0], (r[2] or r[1]) or "", r[3] or "") for r in rows]

    def get_card_by_id(self, id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            if user_id is not None:
                row = conn.execute(
                    text("SELECT * FROM cards WHERE id = :id AND user_id = :user_id"),
                    {"id": id, "user_id": user_id}
                ).mappings().fetchone()
            else:
                row = conn.execute(text("SELECT * FROM cards WHERE id = :id"), {"id": id}).mappings().fetchone()
            return _row_to_card(dict(row)) if row else None

    def create(self, card: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        from sqlalchemy import text
        row = _card_to_row(card)
        cols = [k for k, v in row.items() if v is not None]
        if user_id is not None:
            cols.append("user_id")
        vals = [row[k] for k in cols[:-1]] + ([user_id] if user_id is not None else [])
        placeholders = ", ".join(f":{k}" for k in cols)
        names = ", ".join(cols)
        engine = self._get_engine()
        with engine.connect() as conn:
            params = {k: row[k] for k in cols if k in row}
            if user_id is not None:
                params["user_id"] = user_id
            result = conn.execute(
                text(f"INSERT INTO cards ({names}) VALUES ({placeholders}) RETURNING id"),
                params
            )
            conn.commit()
            new_id = result.scalar()
        out = dict(card)
        out["id"] = new_id
        return out

    def update(self, id: int, fields: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        # Map API field names to DB columns
        col_map = {"type": "type_line", "number": "set_number", "price": "price_eur"}
        updates = {}
        for k, v in fields.items():
            col = col_map.get(k, k)
            if col in (
                "name", "english_name", "type_line", "description", "keywords", "mana_cost",
                "cmc", "colors", "color_identity", "power", "toughness", "rarity",
                "set_id", "set_name", "set_number", "release_date", "edhrec_rank",
                "scryfall_uri", "price_eur", "price_usd", "price_usd_foil", "game_strategy", "tier"
            ):
                if col == "cmc":
                    v = _safe_cmc(v)
                updates[col] = v
        if not updates:
            return self.get_card_by_id(id, user_id=user_id)
        set_clause = ", ".join(f"{c} = :{c}" for c in updates)
        updates["id"] = id
        if user_id is not None:
            updates["user_id"] = user_id
        engine = self._get_engine()
        with engine.connect() as conn:
            where_clause = "WHERE id = :id"
            if user_id is not None:
                where_clause += " AND user_id = :user_id"
            result = conn.execute(
                text(f"UPDATE cards SET {set_clause}, updated_at = NOW() AT TIME ZONE 'utc' {where_clause} RETURNING id"),
                updates
            )
            conn.commit()
            if result.fetchone() is None:
                return None
        return self.get_card_by_id(id, user_id=user_id)

    def delete(self, id: int, user_id: Optional[int] = None) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            if user_id is not None:
                result = conn.execute(
                    text("DELETE FROM cards WHERE id = :id AND user_id = :user_id"),
                    {"id": id, "user_id": user_id}
                )
            else:
                result = conn.execute(text("DELETE FROM cards WHERE id = :id"), {"id": id})
            conn.commit()
            return result.rowcount > 0

    def replace_all(self, cards: List[Dict[str, Any]], user_id: Optional[int] = None) -> int:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            if user_id is not None:
                conn.execute(text("DELETE FROM cards WHERE user_id = :user_id"), {"user_id": user_id})
            else:
                conn.execute(text("DELETE FROM cards"))
            count = 0
            for card in cards:
                row = _card_to_row(card)
                row["name"] = row["name"] or ""
                cols = [k for k, v in row.items() if v is not None]
                if user_id is not None:
                    cols.append("user_id")
                vals = [row[k] for k in cols[:-1]] + ([user_id] if user_id is not None else [])
                placeholders = ", ".join(f":{k}" for k in cols)
                names = ", ".join(cols)
                params = {k: row[k] for k in cols if k in row}
                if user_id is not None:
                    params["user_id"] = user_id
                conn.execute(text(f"INSERT INTO cards ({names}) VALUES ({placeholders})"), params)
                count += 1
            conn.commit()
        logger.info(f"Replaced collection with {count} cards")
        return count

    def update_quantity(self, card_id: int, quantity: int, user_id: Optional[int] = None) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        quantity = max(1, int(quantity))
        with engine.connect() as conn:
            if user_id is not None:
                result = conn.execute(
                    text("UPDATE cards SET quantity = :qty, updated_at = NOW() AT TIME ZONE 'utc' WHERE id = :id AND user_id = :user_id"),
                    {"qty": quantity, "id": card_id, "user_id": user_id}
                )
            else:
                result = conn.execute(
                    text("UPDATE cards SET quantity = :qty, updated_at = NOW() AT TIME ZONE 'utc' WHERE id = :id"),
                    {"qty": quantity, "id": card_id}
                )
            conn.commit()
            return result.rowcount > 0

    def get_card_image_by_scryfall_id(self, scryfall_id: str) -> Optional[Tuple[bytes, str]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT content_type, data FROM card_image_cache WHERE scryfall_id = :scryfall_id"),
                {"scryfall_id": scryfall_id}
            ).fetchone()
            if row is None:
                return None
            return (bytes(row[1]), row[0] or "image/jpeg")

    def save_card_image_to_global_cache(self, scryfall_id: str, content_type: str, data: bytes) -> None:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO card_image_cache (scryfall_id, content_type, data)
                    VALUES (:scryfall_id, :content_type, :data)
                    ON CONFLICT (scryfall_id) DO UPDATE SET content_type = EXCLUDED.content_type, data = EXCLUDED.data
                """),
                {"scryfall_id": scryfall_id, "content_type": content_type, "data": data}
            )
            conn.commit()

    def update_card_scryfall_id(self, card_id: int, scryfall_id: str) -> None:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE cards SET scryfall_id = :scryfall_id WHERE id = :card_id"),
                {"scryfall_id": scryfall_id, "card_id": card_id}
            )
            conn.commit()

    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, google_id, email, display_name, avatar_url, created_at, last_login FROM users WHERE google_id = :google_id"),
                {"google_id": google_id}
            ).mappings().fetchone()
            if row is None:
                return None
            return dict(row)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, google_id, email, display_name, avatar_url, created_at, last_login FROM users WHERE email = :email"),
                {"email": email}
            ).mappings().fetchone()
            if row is None:
                return None
            return dict(row)

    def create_user(self, google_id: str, email: str, display_name: Optional[str] = None, avatar_url: Optional[str] = None) -> Dict[str, Any]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO users (google_id, email, display_name, avatar_url, created_at, last_login)
                    VALUES (:google_id, :email, :display_name, :avatar_url, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc')
                    RETURNING id, google_id, email, display_name, avatar_url, created_at, last_login
                """),
                {
                    "google_id": google_id,
                    "email": email,
                    "display_name": display_name,
                    "avatar_url": avatar_url
                }
            ).mappings().fetchone()
            conn.commit()
            return dict(result) if result else None

    def update_user_google_id(self, user_id: int, google_id: str) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("UPDATE users SET google_id = :google_id WHERE id = :id"),
                {"google_id": google_id, "id": user_id}
            )
            conn.commit()
            return result.rowcount > 0

    def update_user_last_login(self, user_id: int) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("UPDATE users SET last_login = NOW() AT TIME ZONE 'utc' WHERE id = :id"),
                {"id": user_id}
            )
            conn.commit()
            return result.rowcount > 0

    def update_user_profile(self, user_id: int, display_name: Optional[str] = None, avatar_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        updates = {}
        if display_name is not None:
            updates["display_name"] = display_name
        if avatar_url is not None:
            updates["avatar_url"] = avatar_url
        if not updates:
            # Nothing to update — return current user
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT id, google_id, email, display_name, avatar_url, created_at, last_login FROM users WHERE id = :id"),
                    {"id": user_id}
                ).mappings().fetchone()
                return dict(row) if row else None
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = user_id
        with engine.connect() as conn:
            row = conn.execute(
                text(f"UPDATE users SET {set_clause} WHERE id = :id RETURNING id, google_id, email, display_name, avatar_url, created_at, last_login"),
                updates
            ).mappings().fetchone()
            conn.commit()
            return dict(row) if row else None
