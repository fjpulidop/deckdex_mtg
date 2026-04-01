"""Suggestion repository: Postgres implementation for deck_suggestions and seen_set_codes."""

from typing import Any, Dict, List, Optional


class SuggestionRepository:
    """PostgreSQL implementation for deck suggestions and seen set tracking."""

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

    def get_seen_set_codes(self) -> set:
        """Return all set_code values from seen_set_codes."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT set_code FROM seen_set_codes")).fetchall()
        return {row[0] for row in rows}

    def insert_seen_set(self, set_code: str, set_name: str, released_at: str) -> None:
        """Insert a set into seen_set_codes. ON CONFLICT DO NOTHING (idempotent)."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO seen_set_codes (set_code, set_name, released_at)
                    VALUES (:set_code, :set_name, :released_at)
                    ON CONFLICT (set_code) DO NOTHING
                """),
                {"set_code": set_code, "set_name": set_name, "released_at": released_at},
            )

    def get_suggestions_for_deck(self, deck_id: int, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Return suggestions for a deck ordered by score DESC."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            rows = (
                conn.execute(
                    text("""
                        SELECT id, deck_id, user_id, set_code, scryfall_id, card_name,
                               mana_cost, cmc, type_line, color_identity, oracle_text,
                               reason, score, created_at
                        FROM deck_suggestions
                        WHERE deck_id = :deck_id AND user_id = :user_id
                        ORDER BY score DESC
                        LIMIT :limit
                    """),
                    {"deck_id": deck_id, "user_id": user_id, "limit": limit},
                )
                .mappings()
                .fetchall()
            )
        return [dict(row) for row in rows]

    def get_suggestion_count_for_deck(self, deck_id: int, user_id: int) -> int:
        """Return count of suggestions for a deck/user pair."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT COUNT(*) FROM deck_suggestions WHERE deck_id = :deck_id AND user_id = :user_id"),
                {"deck_id": deck_id, "user_id": user_id},
            ).fetchone()
        return row[0] if row else 0

    def upsert_suggestions(self, suggestions: List[Dict[str, Any]]) -> None:
        """Insert or update suggestions. Each dict must contain all required fields."""
        from sqlalchemy import text

        if not suggestions:
            return

        engine = self._get_engine()
        with engine.begin() as conn:
            for s in suggestions:
                conn.execute(
                    text("""
                        INSERT INTO deck_suggestions (
                            deck_id, user_id, set_code, scryfall_id, card_name,
                            mana_cost, cmc, type_line, color_identity, oracle_text,
                            reason, score
                        ) VALUES (
                            :deck_id, :user_id, :set_code, :scryfall_id, :card_name,
                            :mana_cost, :cmc, :type_line, :color_identity, :oracle_text,
                            :reason, :score
                        )
                        ON CONFLICT (deck_id, scryfall_id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            set_code = EXCLUDED.set_code,
                            card_name = EXCLUDED.card_name,
                            mana_cost = EXCLUDED.mana_cost,
                            cmc = EXCLUDED.cmc,
                            type_line = EXCLUDED.type_line,
                            color_identity = EXCLUDED.color_identity,
                            oracle_text = EXCLUDED.oracle_text,
                            reason = EXCLUDED.reason,
                            score = EXCLUDED.score
                    """),
                    {
                        "deck_id": s["deck_id"],
                        "user_id": s["user_id"],
                        "set_code": s["set_code"],
                        "scryfall_id": s["scryfall_id"],
                        "card_name": s["card_name"],
                        "mana_cost": s.get("mana_cost"),
                        "cmc": s.get("cmc"),
                        "type_line": s.get("type_line"),
                        "color_identity": s.get("color_identity"),
                        "oracle_text": s.get("oracle_text"),
                        "reason": s["reason"],
                        "score": s["score"],
                    },
                )

    def delete_suggestion(self, deck_id: int, scryfall_id: str, user_id: int) -> bool:
        """Delete a single suggestion. Returns True if a row was deleted."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM deck_suggestions
                    WHERE deck_id = :deck_id AND scryfall_id = :scryfall_id AND user_id = :user_id
                """),
                {"deck_id": deck_id, "scryfall_id": scryfall_id, "user_id": user_id},
            )
        return result.rowcount > 0

    def delete_suggestions_for_deck(self, deck_id: int, user_id: int) -> int:
        """Delete all suggestions for a deck. Returns row count deleted."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM deck_suggestions WHERE deck_id = :deck_id AND user_id = :user_id"),
                {"deck_id": deck_id, "user_id": user_id},
            )
        return result.rowcount

    def clear_suggestions_for_old_sets(self, current_set_code: str) -> int:
        """Delete suggestions not from the current set. Returns row count deleted."""
        from sqlalchemy import text

        engine = self._get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM deck_suggestions WHERE set_code != :set_code"),
                {"set_code": current_set_code},
            )
        return result.rowcount
