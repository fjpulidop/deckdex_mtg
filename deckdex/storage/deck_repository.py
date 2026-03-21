"""Deck repository: Postgres implementation for decks and deck_cards."""

import json
from typing import Any, Dict, List, Optional

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


def _compute_diff(
    before: List[Dict[str, Any]],
    after: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute card-level diff between two snapshot_data lists.

    Args:
        before: snapshot_data from the older snapshot, or [] for the initial state.
        after: snapshot_data from the newer snapshot.

    Returns:
        Dict with keys: added, removed, quantity_changed, commander_changed.
    """
    before_map: Dict[int, Dict[str, Any]] = {e["card_id"]: e for e in before}
    after_map: Dict[int, Dict[str, Any]] = {e["card_id"]: e for e in after}

    added: List[Dict[str, Any]] = []
    removed: List[Dict[str, Any]] = []
    quantity_changed: List[Dict[str, Any]] = []

    commander_before: Optional[str] = next((e["name"] for e in before if e.get("is_commander")), None)
    commander_after: Optional[str] = next((e["name"] for e in after if e.get("is_commander")), None)

    for card_id, entry in after_map.items():
        if card_id not in before_map:
            added.append({"card_id": card_id, "name": entry["name"], "quantity": entry["quantity"]})
        elif entry["quantity"] != before_map[card_id]["quantity"]:
            quantity_changed.append(
                {
                    "card_id": card_id,
                    "name": entry["name"],
                    "old_quantity": before_map[card_id]["quantity"],
                    "new_quantity": entry["quantity"],
                }
            )

    for card_id, entry in before_map.items():
        if card_id not in after_map:
            removed.append({"card_id": card_id, "name": entry["name"], "quantity": entry["quantity"]})

    return {
        "added": added,
        "removed": removed,
        "quantity_changed": quantity_changed,
        "commander_changed": commander_after if commander_after != commander_before else None,
    }


class DeckRepository:
    """PostgreSQL implementation for decks and deck_cards. Requires same DB as collection (cards table)."""

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

    def _take_snapshot(
        self,
        conn: Any,
        deck_id: int,
        user_id: int,
        change_summary: str,
    ) -> int:
        """Capture the current deck_cards state as a snapshot.

        Must be called inside an open connection BEFORE conn.commit().
        Returns the new snapshot id.
        """
        from sqlalchemy import text

        rows = (
            conn.execute(
                text("""
                    SELECT dc.card_id, c.name, dc.quantity, dc.is_commander
                    FROM deck_cards dc
                    JOIN cards c ON c.id = dc.card_id
                    WHERE dc.deck_id = :deck_id
                    ORDER BY dc.card_id
                """),
                {"deck_id": deck_id},
            )
            .mappings()
            .fetchall()
        )
        snapshot_data = [
            {
                "card_id": r["card_id"],
                "name": r["name"],
                "quantity": r["quantity"],
                "is_commander": bool(r["is_commander"]),
            }
            for r in rows
        ]
        result = conn.execute(
            text("""
                INSERT INTO deck_snapshots (deck_id, created_by, snapshot_data, change_summary)
                VALUES (:deck_id, :created_by, :snapshot_data, :change_summary)
                RETURNING id
            """),
            {
                "deck_id": deck_id,
                "created_by": user_id,
                "snapshot_data": json.dumps(snapshot_data),
                "change_summary": change_summary,
            },
        )
        row = result.mappings().fetchone()
        return row["id"]

    def create(self, name: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            if user_id is not None:
                r = conn.execute(
                    text("""
                        INSERT INTO decks (name, user_id)
                        VALUES (:name, :user_id)
                        RETURNING id, name, created_at, updated_at
                    """),
                    {"name": name or "Unnamed Deck", "user_id": user_id},
                )
            else:
                r = conn.execute(
                    text("""
                        INSERT INTO decks (name)
                        VALUES (:name)
                        RETURNING id, name, created_at, updated_at
                    """),
                    {"name": name or "Unnamed Deck"},
                )
            row = r.mappings().fetchone()
            conn.commit()
        return _row_to_deck(dict(row))

    def list_all(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            where_clause = ""
            params = {}
            if user_id is not None:
                where_clause = "WHERE d.user_id = :user_id"
                params["user_id"] = user_id
            rows = (
                conn.execute(
                    text(f"""
                    SELECT d.id, d.name, d.created_at, d.updated_at,
                           (SELECT COUNT(*) FROM deck_cards WHERE deck_id = d.id) AS card_count,
                           (SELECT card_id FROM deck_cards WHERE deck_id = d.id AND is_commander = true LIMIT 1) AS commander_card_id
                    FROM decks d
                    {where_clause}
                    ORDER BY d.updated_at DESC NULLS LAST, d.id DESC
                """),
                    params,
                )
                .mappings()
                .fetchall()
            )
        out = [_row_to_deck(dict(r)) for r in rows]
        for i, r in enumerate(rows):
            out[i]["card_count"] = r["card_count"]
            out[i]["commander_card_id"] = r["commander_card_id"]
        return out

    def get_by_id(self, deck_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            where_clause = "id = :id"
            params = {"id": deck_id}
            if user_id is not None:
                where_clause += " AND user_id = :user_id"
                params["user_id"] = user_id
            row = (
                conn.execute(text(f"SELECT id, name, created_at, updated_at FROM decks WHERE {where_clause}"), params)
                .mappings()
                .fetchone()
            )
        return _row_to_deck(dict(row)) if row else None

    def get_deck_with_cards(self, deck_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            where_clause = "id = :id"
            params = {"id": deck_id}
            if user_id is not None:
                where_clause += " AND user_id = :user_id"
                params["user_id"] = user_id
            deck_row = (
                conn.execute(text(f"SELECT id, name, created_at, updated_at FROM decks WHERE {where_clause}"), params)
                .mappings()
                .fetchone()
            )
            if not deck_row:
                return None
            deck = _row_to_deck(dict(deck_row))
            # Join deck_cards with cards for full card payload
            rows = (
                conn.execute(
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
                    {"deck_id": deck_id},
                )
                .mappings()
                .fetchall()
            )
            cards = []
            for r in rows:
                row_dict = dict(r)
                card = _row_to_card({k: row_dict[k] for k in row_dict if k not in ("quantity", "is_commander")})
                card["quantity"] = row_dict.get("quantity", 1)
                card["is_commander"] = bool(row_dict.get("is_commander"))
                cards.append(card)
            deck["cards"] = cards
            return deck

    def update_name(self, deck_id: int, name: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            where_clause = "id = :id"
            params = {"id": deck_id, "name": name}
            if user_id is not None:
                where_clause += " AND user_id = :user_id"
                params["user_id"] = user_id
            result = conn.execute(
                text(f"""
                    UPDATE decks SET name = :name, updated_at = NOW() AT TIME ZONE 'utc'
                    WHERE {where_clause} RETURNING id, name, created_at, updated_at
                """),
                params,
            )
            row = result.mappings().fetchone()
            conn.commit()
        return _row_to_deck(dict(row)) if row else None

    def delete(self, deck_id: int, user_id: Optional[int] = None) -> bool:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            where_clause = "id = :id"
            params = {"id": deck_id}
            if user_id is not None:
                where_clause += " AND user_id = :user_id"
                params["user_id"] = user_id
            result = conn.execute(text(f"DELETE FROM decks WHERE {where_clause}"), params)
            conn.commit()
            return result.rowcount > 0

    def add_card(
        self, deck_id: int, card_id: int, quantity: int = 1, is_commander: bool = False, user_id: Optional[int] = None
    ) -> bool:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            # Check card exists in collection and belongs to user if user_id provided
            card_where = "id = :card_id"
            card_params = {"card_id": card_id}
            if user_id is not None:
                card_where += " AND user_id = :user_id"
                card_params["user_id"] = user_id
            card_row = (
                conn.execute(text(f"SELECT id, name FROM cards WHERE {card_where}"), card_params).mappings().fetchone()
            )
            card_exists = card_row is not None
            card_name = card_row["name"] if card_row else "Unknown"
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
                {"deck_id": deck_id, "card_id": card_id, "quantity": quantity, "is_commander": is_commander},
            )
            if user_id is not None:
                self._take_snapshot(conn, deck_id, user_id, f"Added {quantity}x {card_name}")
            conn.commit()
        return True

    def remove_card(self, deck_id: int, card_id: int, user_id: Optional[int] = None) -> bool:
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            # Verify deck ownership if user_id provided
            if user_id is not None:
                deck_check = conn.execute(
                    text("SELECT 1 FROM decks WHERE id = :deck_id AND user_id = :user_id"),
                    {"deck_id": deck_id, "user_id": user_id},
                ).fetchone()
                if not deck_check:
                    return False
            # Fetch card name before delete
            card_name_row = (
                conn.execute(text("SELECT name FROM cards WHERE id = :card_id"), {"card_id": card_id})
                .mappings()
                .fetchone()
            )
            card_name = card_name_row["name"] if card_name_row else f"card {card_id}"
            result = conn.execute(
                text("DELETE FROM deck_cards WHERE deck_id = :deck_id AND card_id = :card_id"),
                {"deck_id": deck_id, "card_id": card_id},
            )
            if user_id is not None and result.rowcount > 0:
                self._take_snapshot(conn, deck_id, user_id, f"Removed {card_name}")
            conn.commit()
            return result.rowcount > 0

    def add_cards_batch(
        self,
        deck_id: int,
        card_ids: List[int],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add multiple cards from the collection to a deck in one transaction.

        Cards not found in the user's collection are skipped and returned in not_found.
        Existing deck_cards entries have their quantity incremented by 1 (same as add_card).
        Returns {"added": [int, ...], "not_found": [int, ...]}.
        """
        from sqlalchemy import text

        if not card_ids:
            return {"added": [], "not_found": []}

        engine = self._get_engine()
        with engine.connect() as conn:
            # 1. Validate cards exist in user's collection (single query)
            card_where = "id = ANY(:ids)"
            card_params: Dict[str, Any] = {"ids": list(card_ids)}
            if user_id is not None:
                card_where += " AND user_id = :user_id"
                card_params["user_id"] = user_id

            rows = (
                conn.execute(
                    text(f"SELECT id FROM cards WHERE {card_where}"),
                    card_params,
                )
                .mappings()
                .fetchall()
            )
            valid_ids = {r["id"] for r in rows}
            not_found = [cid for cid in card_ids if cid not in valid_ids]

            # 2. Insert all valid cards in one transaction
            for cid in valid_ids:
                conn.execute(
                    text("""
                        INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
                        VALUES (:deck_id, :card_id, 1, false)
                        ON CONFLICT (deck_id, card_id) DO UPDATE
                        SET quantity = deck_cards.quantity + 1
                    """),
                    {"deck_id": deck_id, "card_id": cid},
                )
            if valid_ids and user_id is not None:
                self._take_snapshot(conn, deck_id, user_id, f"Added {len(valid_ids)} card(s) in batch")
            if valid_ids:
                conn.commit()

        return {"added": sorted(list(valid_ids)), "not_found": not_found}

    def add_cards_from_import(
        self,
        deck_id: int,
        cards: List[Dict[str, Any]],
        user_id: Optional[int] = None,
        imported_count: int = 0,
    ) -> None:
        """Add cards from a parsed deck import in a single transaction.

        Args:
            deck_id: Target deck id.
            cards: List of dicts with keys: card_id (int), quantity (int), is_commander (bool).
                   All card_ids must already be validated to exist in the user's collection.
            user_id: Authenticated user id. Required for snapshot creation.
            imported_count: Number of cards imported (used in change_summary).
        """
        from sqlalchemy import text

        if not cards:
            return

        engine = self._get_engine()
        with engine.connect() as conn:
            for card in cards:
                conn.execute(
                    text("""
                        INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
                        VALUES (:deck_id, :card_id, :quantity, :is_commander)
                        ON CONFLICT (deck_id, card_id) DO UPDATE
                        SET quantity = deck_cards.quantity + EXCLUDED.quantity,
                            is_commander = EXCLUDED.is_commander
                    """),
                    {
                        "deck_id": deck_id,
                        "card_id": card["card_id"],
                        "quantity": card["quantity"],
                        "is_commander": card["is_commander"],
                    },
                )
            if user_id is not None:
                self._take_snapshot(conn, deck_id, user_id, f"Imported {imported_count} card(s)")
            conn.commit()

    def find_card_ids_by_names(self, names: List[str], user_id: Optional[int] = None) -> Dict[str, int]:
        """Return a mapping of lowercase card name → card id for names found in the collection.

        Executes a single query against the cards table. Resolution is
        case-insensitive (names are lowercased before comparison). When multiple
        rows share the same lowercase name, the one with the lowest id wins.

        Args:
            names: List of card names to resolve (case-insensitive).
            user_id: If provided, restricts the search to cards owned by this user.

        Returns:
            Dict mapping lowercase name → card id for each name found.
        """
        if not names:
            return {}

        from sqlalchemy import text

        engine = self._get_engine()

        lowered: List[str] = [n.lower() for n in names]

        with engine.connect() as conn:
            where_clause = "LOWER(name) = ANY(:names)"
            params: Dict[str, Any] = {"names": lowered}
            if user_id is not None:
                where_clause += " AND user_id = :user_id"
                params["user_id"] = user_id

            rows = (
                conn.execute(
                    text(f"SELECT id, name FROM cards WHERE {where_clause} ORDER BY id ASC"),
                    params,
                )
                .mappings()
                .fetchall()
            )

        result: Dict[str, int] = {}
        for row in rows:
            key = row["name"].lower()
            # First row wins (ORDER BY id ASC ensures lowest id for duplicates)
            if key not in result:
                result[key] = row["id"]
        return result

    def set_commander(self, deck_id: int, card_id: int, user_id: Optional[int] = None) -> bool:
        """Set one card as commander; unset any other commander in this deck. Card must be in deck."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            # Verify deck ownership if user_id provided
            if user_id is not None:
                deck_check = conn.execute(
                    text("SELECT 1 FROM decks WHERE id = :deck_id AND user_id = :user_id"),
                    {"deck_id": deck_id, "user_id": user_id},
                ).fetchone()
                if not deck_check:
                    return False
            # Ensure card is in deck
            in_deck = conn.execute(
                text("SELECT 1 FROM deck_cards WHERE deck_id = :deck_id AND card_id = :card_id"),
                {"deck_id": deck_id, "card_id": card_id},
            ).fetchone()
            if not in_deck:
                return False
            # Fetch card name for snapshot
            card_name_row = (
                conn.execute(text("SELECT name FROM cards WHERE id = :card_id"), {"card_id": card_id})
                .mappings()
                .fetchone()
            )
            card_name = card_name_row["name"] if card_name_row else f"card {card_id}"
            conn.execute(
                text("UPDATE deck_cards SET is_commander = false WHERE deck_id = :deck_id"), {"deck_id": deck_id}
            )
            conn.execute(
                text("""
                    UPDATE deck_cards SET is_commander = true
                    WHERE deck_id = :deck_id AND card_id = :card_id
                """),
                {"deck_id": deck_id, "card_id": card_id},
            )
            if user_id is not None:
                self._take_snapshot(conn, deck_id, user_id, f"Set {card_name} as commander")
            conn.commit()
        return True

    def get_history(
        self,
        deck_id: int,
        user_id: Optional[int] = None,
        limit: int = 50,
    ) -> Optional[List[Dict[str, Any]]]:
        """Return paginated snapshot history for a deck, newest-first.

        Returns None if the deck does not exist or does not belong to user_id.
        Each entry includes a computed diff against the previous snapshot.
        """
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            # Verify deck ownership
            where = "id = :deck_id"
            params: Dict[str, Any] = {"deck_id": deck_id}
            if user_id is not None:
                where += " AND user_id = :user_id"
                params["user_id"] = user_id
            deck_exists = conn.execute(text(f"SELECT 1 FROM decks WHERE {where}"), params).fetchone()
            if not deck_exists:
                return None

            # Fetch limit+1 to have context for diff of the oldest entry
            clamped_limit = min(max(1, limit), 200)
            rows = (
                conn.execute(
                    text("""
                        SELECT id, created_at, created_by, snapshot_data, change_summary
                        FROM deck_snapshots
                        WHERE deck_id = :deck_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"deck_id": deck_id, "limit": clamped_limit + 1},
                )
                .mappings()
                .fetchall()
            )

        snapshots = [dict(r) for r in rows]

        # Compute diffs: each snapshot diffs against the one after it (older)
        # snapshots[0] is newest, snapshots[-1] is oldest
        result = []
        for i, snap in enumerate(snapshots[:clamped_limit]):
            older_data: List[Dict[str, Any]] = []
            if i + 1 < len(snapshots):
                raw = snapshots[i + 1]["snapshot_data"]
                older_data = raw if isinstance(raw, list) else json.loads(raw)
            current_data: List[Dict[str, Any]] = snap["snapshot_data"]
            if not isinstance(current_data, list):
                current_data = json.loads(current_data)

            diff = _compute_diff(before=older_data, after=current_data)
            result.append(
                {
                    "id": snap["id"],
                    "created_at": _serialize_ts(snap["created_at"]),
                    "created_by": snap["created_by"],
                    "change_summary": snap["change_summary"],
                    "diff": diff,
                }
            )

        return result

    def revert_to_snapshot(
        self,
        deck_id: int,
        snapshot_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Revert deck_cards to the state captured in snapshot_id.

        Returns:
            The updated DeckWithCards dict on success.
            None if deck or snapshot not found / wrong owner.

        Raises:
            ValueError: If a card in the snapshot no longer exists in the collection.
                        Route handler should convert to HTTP 409.
        """
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            # 1. Verify deck ownership
            where = "id = :deck_id"
            params: Dict[str, Any] = {"deck_id": deck_id}
            if user_id is not None:
                where += " AND user_id = :user_id"
                params["user_id"] = user_id
            deck_exists = conn.execute(text(f"SELECT 1 FROM decks WHERE {where}"), params).fetchone()
            if not deck_exists:
                return None

            # 2. Load snapshot
            snap_row = (
                conn.execute(
                    text("""
                    SELECT id, snapshot_data
                    FROM deck_snapshots
                    WHERE id = :snapshot_id AND deck_id = :deck_id
                """),
                    {"snapshot_id": snapshot_id, "deck_id": deck_id},
                )
                .mappings()
                .fetchone()
            )
            if not snap_row:
                return None

            snapshot_data: List[Dict[str, Any]] = snap_row["snapshot_data"]
            if not isinstance(snapshot_data, list):
                snapshot_data = json.loads(snapshot_data)

            # 3. Clear current deck_cards
            conn.execute(
                text("DELETE FROM deck_cards WHERE deck_id = :deck_id"),
                {"deck_id": deck_id},
            )

            # 4. Re-insert from snapshot
            for entry in snapshot_data:
                try:
                    conn.execute(
                        text("""
                            INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander)
                            VALUES (:deck_id, :card_id, :quantity, :is_commander)
                        """),
                        {
                            "deck_id": deck_id,
                            "card_id": entry["card_id"],
                            "quantity": entry["quantity"],
                            "is_commander": entry["is_commander"],
                        },
                    )
                except Exception as exc:
                    # FK violation: card no longer in collection
                    raise ValueError(
                        f"Card '{entry['name']}' (id={entry['card_id']}) no longer exists in collection"
                    ) from exc

            # 5. Take snapshot of reverted state
            if user_id is not None:
                self._take_snapshot(conn, deck_id, user_id, f"Reverted to snapshot #{snapshot_id}")

            conn.commit()

        # Return updated deck
        return self.get_deck_with_cards(deck_id, user_id=user_id)
