"""Deck repository: Postgres implementation for decks and deck_cards."""

from typing import List, Dict, Any, Optional

from loguru import logger

from .repository import _row_to_card


def _serialize_ts(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _row_to_deck(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "created_at": _serialize_ts(row.get("created_at")),
        "updated_at": _serialize_ts(row.get("updated_at")),
    }


class DeckRepository:
    """PostgreSQL implementation for decks and deck_cards. Requires same DB as collection (cards table)."""

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

    def create(self, name: str) -> Dict[str, Any]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            r = conn.execute(
                text("""
                    INSERT INTO decks (name)
                    VALUES (:name)
                    RETURNING id, name, created_at, updated_at
                """),
                {"name": name or "Unnamed Deck"}
            )
            row = r.mappings().fetchone()
            conn.commit()
        return _row_to_deck(dict(row))

    def list_all(self) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT d.id, d.name, d.created_at, d.updated_at,
                           (SELECT COUNT(*) FROM deck_cards WHERE deck_id = d.id) AS card_count,
                           (SELECT card_id FROM deck_cards WHERE deck_id = d.id AND is_commander = true LIMIT 1) AS commander_card_id
                    FROM decks d
                    ORDER BY d.updated_at DESC NULLS LAST, d.id DESC
                """)
            ).mappings().fetchall()
        out = [_row_to_deck(dict(r)) for r in rows]
        for i, r in enumerate(rows):
            out[i]["card_count"] = r["card_count"]
            out[i]["commander_card_id"] = r["commander_card_id"]
        return out

    def get_by_id(self, deck_id: int) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, name, created_at, updated_at FROM decks WHERE id = :id"),
                {"id": deck_id}
            ).mappings().fetchone()
        return _row_to_deck(dict(row)) if row else None

    def get_deck_with_cards(self, deck_id: int) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            deck_row = conn.execute(
                text("SELECT id, name, created_at, updated_at FROM decks WHERE id = :id"),
                {"id": deck_id}
            ).mappings().fetchone()
            if not deck_row:
                return None
            deck = _row_to_deck(dict(deck_row))
            # Join deck_cards with cards for full card payload
            rows = conn.execute(
                text("""
                    SELECT c.id, c.name, c.english_name, c.type_line, c.description, c.keywords,
                           c.mana_cost, c.cmc, c.colors, c.color_identity, c.power, c.toughness,
                           c.rarity, c.price_eur, c.release_date, c.set_id, c.set_name, c.set_number,
                           c.edhrec_rank, c.game_strategy, c.tier, c.created_at,
                           dc.quantity, dc.is_commander
                    FROM deck_cards dc
                    JOIN cards c ON c.id = dc.card_id
                    WHERE dc.deck_id = :deck_id
                    ORDER BY dc.is_commander DESC, c.type_line, c.name
                """),
                {"deck_id": deck_id}
            ).mappings().fetchall()
            cards = []
            for r in rows:
                row_dict = dict(r)
                card = _row_to_card({k: row_dict[k] for k in row_dict if k not in ("quantity", "is_commander")})
                card["quantity"] = row_dict.get("quantity", 1)
                card["is_commander"] = bool(row_dict.get("is_commander"))
                cards.append(card)
            deck["cards"] = cards
            return deck

    def update_name(self, deck_id: int, name: str) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    UPDATE decks SET name = :name, updated_at = NOW() AT TIME ZONE 'utc'
                    WHERE id = :id RETURNING id, name, created_at, updated_at
                """),
                {"id": deck_id, "name": name}
            )
            row = result.mappings().fetchone()
            conn.commit()
        return _row_to_deck(dict(row)) if row else None

    def delete(self, deck_id: int) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM decks WHERE id = :id"), {"id": deck_id})
            conn.commit()
            return result.rowcount > 0

    def add_card(self, deck_id: int, card_id: int, quantity: int = 1, is_commander: bool = False) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            # Check card exists in collection
            card_exists = conn.execute(
                text("SELECT 1 FROM cards WHERE id = :card_id"),
                {"card_id": card_id}
            ).fetchone()
            if not card_exists:
                return False
            conn.execute(
                text("""
                    INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
                    VALUES (:deck_id, :card_id, :quantity, :is_commander)
                    ON CONFLICT (deck_id, card_id) DO UPDATE
                    SET quantity = deck_cards.quantity + EXCLUDED.quantity,
                        is_commander = EXCLUDED.is_commander
                """),
                {"deck_id": deck_id, "card_id": card_id, "quantity": quantity, "is_commander": is_commander}
            )
            conn.commit()
        return True

    def remove_card(self, deck_id: int, card_id: int) -> bool:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM deck_cards WHERE deck_id = :deck_id AND card_id = :card_id"),
                {"deck_id": deck_id, "card_id": card_id}
            )
            conn.commit()
            return result.rowcount > 0

    def set_commander(self, deck_id: int, card_id: int) -> bool:
        """Set one card as commander; unset any other commander in this deck. Card must be in deck."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            # Ensure card is in deck
            in_deck = conn.execute(
                text("SELECT 1 FROM deck_cards WHERE deck_id = :deck_id AND card_id = :card_id"),
                {"deck_id": deck_id, "card_id": card_id}
            ).fetchone()
            if not in_deck:
                return False
            conn.execute(
                text("UPDATE deck_cards SET is_commander = false WHERE deck_id = :deck_id"),
                {"deck_id": deck_id}
            )
            conn.execute(
                text("""
                    UPDATE deck_cards SET is_commander = true
                    WHERE deck_id = :deck_id AND card_id = :card_id
                """),
                {"deck_id": deck_id, "card_id": card_id}
            )
            conn.commit()
        return True
