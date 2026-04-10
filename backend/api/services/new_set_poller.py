"""New Set Poller: polls Scryfall for new MTG sets and generates deck suggestions."""

import time
from datetime import datetime, timezone
from typing import Any, List, Optional

import requests
from loguru import logger

from deckdex.services.recommendation_engine import compute_suggestions_for_all_decks


class NewSetPoller:
    """Polls Scryfall /sets periodically to detect new set releases.

    For each newly detected set, fetches all cards, upserts them into the
    catalog, and runs the recommendation engine across all user decks.
    """

    SETS_URL = "https://api.scryfall.com/sets"
    CARDS_SEARCH_URL = "https://api.scryfall.com/cards/search"
    RELEVANT_SET_TYPES = {"expansion", "core", "masters", "draft_innovation", "commander"}
    PAGE_DELAY_SECONDS = 0.1
    _REQUEST_TIMEOUT = 10
    _USER_AGENT = "DeckDex-MTG/1.0"

    def __init__(
        self,
        engine: Any,
        suggestion_repo: Any,
        deck_repo: Any,
        catalog_repo: Optional[Any] = None,
    ) -> None:
        self._engine = engine
        self._suggestion_repo = suggestion_repo
        self._deck_repo = deck_repo
        self._catalog_repo = catalog_repo

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_once(self) -> List[str]:
        """Poll Scryfall for new sets. Returns list of newly processed set codes.

        All errors for individual sets are caught and logged; processing
        continues for remaining sets.
        """
        try:
            sets_list = self._fetch_sets()
        except Exception as exc:
            logger.error(f"NewSetPoller: failed to fetch sets from Scryfall: {exc}")
            return []

        seen_codes = self._suggestion_repo.get_seen_set_codes()
        processed: List[str] = []

        for set_obj in sets_list:
            set_code = set_obj.get("code", "")
            set_name = set_obj.get("name", set_code)
            released_at = set_obj.get("released_at", "")

            if set_code in seen_codes:
                continue

            try:
                logger.info(f"NewSetPoller: processing new set {set_code!r} ({set_name})")

                # 1. Fetch all cards for this set
                new_cards = self._fetch_cards_for_set(set_code)
                logger.info(f"NewSetPoller: fetched {len(new_cards)} cards for set {set_code!r}")

                # 2. Upsert cards into catalog
                self._upsert_catalog_cards(new_cards)

                # 3. Compute suggestions for all decks
                total_suggestions = compute_suggestions_for_all_decks(
                    engine=self._engine,
                    suggestion_repo=self._suggestion_repo,
                    deck_repo=self._deck_repo,
                    new_cards=new_cards,
                    set_code=set_code,
                    set_name=set_name,
                )

                # 4. Mark set as seen (write last — so partial failures cause a retry)
                self._suggestion_repo.insert_seen_set(set_code, set_name, released_at)

                processed.append(set_code)
                logger.info(f"NewSetPoller: processed new set {set_code!r}: {total_suggestions} suggestions generated")

            except Exception as exc:
                logger.error(
                    f"NewSetPoller: error processing set {set_code!r}: {exc}",
                    exc_info=True,
                )
                # Do NOT add to processed — set will be retried on next poll

        return processed

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_sets(self) -> List[dict]:
        """Fetch and filter relevant sets from Scryfall /sets."""
        today = datetime.now(timezone.utc).date().isoformat()
        response = self._make_get_request(self.SETS_URL)
        data = response.json()
        sets_list = data.get("data", [])

        relevant = []
        for s in sets_list:
            if s.get("set_type") not in self.RELEVANT_SET_TYPES:
                continue
            released_at = s.get("released_at", "")
            if released_at and released_at <= today:
                relevant.append(s)
        return relevant

    def _fetch_cards_for_set(self, set_code: str) -> List[dict]:
        """Paginate through all cards for a given set code.

        Returns a flat list of card dicts with only the fields needed for
        suggestions and catalog upserts.
        """
        url = f"{self.CARDS_SEARCH_URL}?q=set:{set_code}&unique=prints"
        cards: List[dict] = []

        while url:
            response = self._make_get_request(url)
            data = response.json()
            for card in data.get("data", []):
                cards.append(self._extract_card_fields(card))
            url = data.get("next_page")
            if url:
                time.sleep(self.PAGE_DELAY_SECONDS)

        return cards

    def _extract_card_fields(self, card: dict) -> dict:
        """Extract only the fields needed from a raw Scryfall card object."""
        return {
            "scryfall_id": card.get("id"),
            "name": card.get("name"),
            "mana_cost": card.get("mana_cost"),
            "cmc": card.get("cmc"),
            "type_line": card.get("type_line"),
            "color_identity": ",".join(card.get("color_identity", [])),
            "oracle_text": card.get("oracle_text"),
            "rarity": card.get("rarity"),
            "image_uris": card.get("image_uris"),
        }

    def _upsert_catalog_cards(self, cards: List[dict]) -> None:
        """Insert new set cards into catalog_cards (ON CONFLICT DO NOTHING)."""
        if not cards:
            return

        # Try using catalog_repo.upsert_cards if it exists
        if self._catalog_repo is not None and hasattr(self._catalog_repo, "upsert_cards"):
            try:
                self._catalog_repo.upsert_cards(cards)
                return
            except Exception as exc:
                logger.warning(f"NewSetPoller: catalog_repo.upsert_cards failed, falling back to raw insert: {exc}")

        # Fallback: raw INSERT ON CONFLICT DO NOTHING via engine
        if self._engine is None:
            return
        try:
            from sqlalchemy import text

            with self._engine.begin() as conn:
                for card in cards:
                    scryfall_id = card.get("scryfall_id")
                    name = card.get("name")
                    if not scryfall_id or not name:
                        continue
                    image_uri = None
                    image_uris = card.get("image_uris")
                    if isinstance(image_uris, dict):
                        image_uri = image_uris.get("normal")
                    conn.execute(
                        text("""
                            INSERT INTO catalog_cards (
                                scryfall_id, name, mana_cost, cmc, type_line,
                                color_identity, oracle_text, rarity, image_uri
                            ) VALUES (
                                :scryfall_id, :name, :mana_cost, :cmc, :type_line,
                                :color_identity, :oracle_text, :rarity, :image_uri
                            )
                            ON CONFLICT (scryfall_id) DO NOTHING
                        """),
                        {
                            "scryfall_id": scryfall_id,
                            "name": name,
                            "mana_cost": card.get("mana_cost"),
                            "cmc": card.get("cmc"),
                            "type_line": card.get("type_line"),
                            "color_identity": card.get("color_identity"),
                            "oracle_text": card.get("oracle_text"),
                            "rarity": card.get("rarity"),
                            "image_uri": image_uri,
                        },
                    )
        except Exception as exc:
            logger.error(f"NewSetPoller: failed to upsert catalog cards: {exc}")

    def _make_get_request(self, url: str, retry: bool = True) -> requests.Response:
        """GET request with timeout and single retry on connection error."""
        headers = {"User-Agent": self._USER_AGENT}
        try:
            response = requests.get(url, timeout=self._REQUEST_TIMEOUT, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            if retry:
                logger.warning(f"NewSetPoller: connection error on {url}, retrying once")
                time.sleep(1)
                return self._make_get_request(url, retry=False)
            raise
