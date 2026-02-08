"""Collection repository: abstract interface and Postgres implementation."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from loguru import logger


def _is_incomplete_card(card: Dict[str, Any]) -> bool:
    """True if card looks like 'new added' with only name (missing type_line / main Scryfall fields)."""
    type_line = card.get("type_line") or card.get("type")
    return not (type_line and str(type_line).strip())


# Card dict keys aligned with API and data-model (name, price, set_name, number/set_number, etc.)
def _row_to_card(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map DB row to API-style card dict (id, name, price, number, ...)."""
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
    }
    return {k: v for k, v in card.items() if v is not None or k == "id"}


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
    }


class CollectionRepository(ABC):
    """Abstract interface for card collection storage."""

    @abstractmethod
    def get_all_cards(self) -> List[Dict[str, Any]]:
        """Return all cards as list of dicts (API shape, including id)."""
        pass

    def get_cards_for_process(self, only_incomplete: bool = False) -> List[Dict[str, Any]]:
        """Return cards to process. If only_incomplete=True, only cards that have e.g. only name (no type_line)."""
        cards = self.get_all_cards()
        if not only_incomplete:
            return cards
        return [c for c in cards if c.get("id") is not None and _is_incomplete_card(c)]

    @abstractmethod
    def get_cards_for_price_update(self) -> List[tuple]:
        """Return list of (card_id, card_name, current_price_str) for price update job."""
        pass

    @abstractmethod
    def get_card_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Return one card by surrogate id or None."""
        pass

    @abstractmethod
    def create(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a card; return the same card dict with id set."""
        pass

    @abstractmethod
    def update(self, id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update card by id; return updated card or None if not found."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete card by id; return True if deleted, False if not found."""
        pass

    @abstractmethod
    def replace_all(self, cards: List[Dict[str, Any]]) -> int:
        """Replace entire collection with given cards (delete all, insert all). Return count inserted."""
        pass


class PostgresCollectionRepository(CollectionRepository):
    """PostgreSQL implementation of CollectionRepository."""

    def __init__(self, database_url: str):
        if not database_url or not database_url.strip().startswith("postgresql"):
            raise ValueError("database_url must be a non-empty postgresql:// URL")
        self._url = database_url
        self._eng = None

    def _get_engine(self):
        from sqlalchemy import create_engine
        if self._eng is None:
            self._eng = create_engine(self._url, pool_pre_ping=True)
        return self._eng

    def get_all_cards(self) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM cards ORDER BY id")).mappings().fetchall()
            return [_row_to_card(dict(r)) for r in rows]

    def get_cards_for_process(self, only_incomplete: bool = False) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            if only_incomplete:
                rows = conn.execute(text("""
                    SELECT * FROM cards
                    WHERE name IS NOT NULL AND name != ''
                    AND (type_line IS NULL OR TRIM(type_line) = '')
                    ORDER BY id
                """)).mappings().fetchall()
            else:
                rows = conn.execute(text("SELECT * FROM cards ORDER BY id")).mappings().fetchall()
            return [_row_to_card(dict(r)) for r in rows]

    def get_cards_for_price_update(self) -> List[tuple]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, name, price_eur FROM cards WHERE name IS NOT NULL AND name != ''")
            ).fetchall()
            return [(r[0], r[1], r[2] or "") for r in rows]

    def get_card_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM cards WHERE id = :id"), {"id": id}).mappings().fetchone()
            return _row_to_card(dict(row)) if row else None

    def create(self, card: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import text
        row = _card_to_row(card)
        cols = [k for k, v in row.items() if v is not None]
        vals = [row[k] for k in cols]
        placeholders = ", ".join(f":{k}" for k in cols)
        names = ", ".join(cols)
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(f"INSERT INTO cards ({names}) VALUES ({placeholders}) RETURNING id"),
                {k: row[k] for k in cols}
            )
            conn.commit()
            new_id = result.scalar()
        out = dict(card)
        out["id"] = new_id
        return out

    def update(self, id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            return self.get_card_by_id(id)
        set_clause = ", ".join(f"{c} = :{c}" for c in updates)
        updates["id"] = id
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(f"UPDATE cards SET {set_clause}, updated_at = NOW() AT TIME ZONE 'utc' WHERE id = :id RETURNING id"),
                updates
            )
            conn.commit()
            if result.fetchone() is None:
                return None
        return self.get_card_by_id(id)

    def delete(self, id: int) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM cards WHERE id = :id"), {"id": id})
            conn.commit()
            return result.rowcount > 0

    def replace_all(self, cards: List[Dict[str, Any]]) -> int:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM cards"))
            count = 0
            for card in cards:
                row = _card_to_row(card)
                row["name"] = row["name"] or ""
                cols = [k for k, v in row.items() if v is not None]
                vals = [row[k] for k in cols]
                placeholders = ", ".join(f":{k}" for k in cols)
                names = ", ".join(cols)
                conn.execute(text(f"INSERT INTO cards ({names}) VALUES ({placeholders})"), {k: row[k] for k in cols})
                count += 1
            conn.commit()
        logger.info(f"Replaced collection with {count} cards")
        return count
