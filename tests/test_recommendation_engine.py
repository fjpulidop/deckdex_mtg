"""Unit tests for deckdex/services/recommendation_engine.py.

Tests cover:
  - compute_suggestions_for_deck: color identity filtering, top-5 cap,
    scoring formula, reason strings, edge cases.
  - Private helpers: _parse_color_identity, _compute_commander_color_identity,
    _is_land, _compute_deck_card_types, _compute_deck_median_cmc,
    _collect_existing_scryfall_ids, _extract_image_uri, _score_card,
    _build_reason.
  - compute_suggestions_for_all_decks: mocked SQLAlchemy engine.

All fixtures use scope="function" (no module-scoped mocks).
"""

import unittest
from collections import Counter
from unittest.mock import MagicMock, patch

from deckdex.services.recommendation_engine import (
    RecommendationEngine,
    _build_reason,
    _collect_existing_scryfall_ids,
    _compute_commander_color_identity,
    _compute_deck_card_types,
    _compute_deck_median_cmc,
    _extract_image_uri,
    _is_land,
    _parse_color_identity,
    _score_card,
    compute_suggestions_for_all_decks,
)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_card(
    scryfall_id: str = "card-001",
    name: str = "Test Card",
    type_line: str = "Creature — Human",
    color_identity: str = "B",
    cmc: float = 3.0,
    rarity: str = "common",
    mana_cost: str = "{2}{B}",
    oracle_text: str = "",
    image_uris: dict | None = None,
    is_commander: bool = False,
) -> dict:
    card = {
        "scryfall_id": scryfall_id,
        "name": name,
        "type_line": type_line,
        "color_identity": color_identity,
        "cmc": cmc,
        "rarity": rarity,
        "mana_cost": mana_cost,
        "oracle_text": oracle_text,
        "image_uris": image_uris,
    }
    if is_commander:
        card["is_commander"] = True
    return card


def _make_new_set_card(
    scryfall_id: str = "new-001",
    name: str = "New Card",
    type_line: str = "Creature — Wizard",
    color_identity: str = "B",
    cmc: float = 3.0,
    rarity: str = "rare",
    mana_cost: str = "{2}{B}",
    oracle_text: str = "",
    image_uris: dict | None = None,
) -> dict:
    """Card dict as returned by the Scryfall API (fields match _extract_card_fields)."""
    return {
        "id": scryfall_id,           # Scryfall uses 'id'
        "scryfall_id": scryfall_id,
        "name": name,
        "type_line": type_line,
        "color_identity": color_identity,
        "cmc": cmc,
        "rarity": rarity,
        "mana_cost": mana_cost,
        "oracle_text": oracle_text,
        "image_uris": image_uris or {},
    }


def _make_engine_with_deck(deck_dict: dict) -> MagicMock:
    """Build a mock deck_repo whose get_deck_with_cards returns deck_dict."""
    deck_repo = MagicMock()
    deck_repo.get_deck_with_cards.return_value = deck_dict
    return deck_repo


# ---------------------------------------------------------------------------
# Tests: _parse_color_identity
# ---------------------------------------------------------------------------


class TestParseColorIdentity(unittest.TestCase):
    def test_empty_string_returns_empty_set(self):
        assert _parse_color_identity("") == set()

    def test_single_color(self):
        assert _parse_color_identity("B") == {"B"}

    def test_multiple_colors_comma_separated(self):
        assert _parse_color_identity("B,G,R") == {"B", "G", "R"}

    def test_normalises_to_uppercase(self):
        assert _parse_color_identity("b,g") == {"B", "G"}

    def test_whitespace_around_commas(self):
        assert _parse_color_identity(" W , U ") == {"W", "U"}

    def test_none_like_empty_string_produces_empty_set(self):
        # The function expects a string; callers guard None with `or ""`
        assert _parse_color_identity("") == set()


# ---------------------------------------------------------------------------
# Tests: _is_land
# ---------------------------------------------------------------------------


class TestIsLand(unittest.TestCase):
    def test_basic_land(self):
        assert _is_land("Basic Land — Forest") is True

    def test_nonland_creature(self):
        assert _is_land("Creature — Human") is False

    def test_case_insensitive(self):
        assert _is_land("LAND") is True

    def test_land_in_middle(self):
        assert _is_land("Snow-covered Land") is True

    def test_empty_string(self):
        assert _is_land("") is False


# ---------------------------------------------------------------------------
# Tests: _compute_commander_color_identity
# ---------------------------------------------------------------------------


class TestComputeCommanderColorIdentity(unittest.TestCase):
    def test_commander_card_used_when_present(self):
        cards = [
            _make_card(color_identity="B,G", is_commander=True),
            _make_card(color_identity="R"),
        ]
        result = _compute_commander_color_identity(cards)
        assert result == {"B", "G"}

    def test_no_commander_returns_union(self):
        cards = [
            _make_card(color_identity="B"),
            _make_card(color_identity="G"),
        ]
        result = _compute_commander_color_identity(cards)
        assert result == {"B", "G"}

    def test_empty_deck_returns_empty_set(self):
        assert _compute_commander_color_identity([]) == set()

    def test_colorless_commander(self):
        cards = [_make_card(color_identity="", is_commander=True)]
        result = _compute_commander_color_identity(cards)
        assert result == set()


# ---------------------------------------------------------------------------
# Tests: _compute_deck_card_types
# ---------------------------------------------------------------------------


class TestComputeDeckCardTypes(unittest.TestCase):
    def test_creature_counted(self):
        cards = [_make_card(type_line="Creature — Human")]
        counter = _compute_deck_card_types(cards)
        assert counter["Creature"] == 1
        assert counter["Human"] == 1

    def test_land_skipped(self):
        cards = [
            _make_card(type_line="Basic Land — Forest"),
            _make_card(type_line="Creature — Elf"),
        ]
        counter = _compute_deck_card_types(cards)
        assert "Land" not in counter
        assert counter["Creature"] == 1

    def test_em_dash_separator_handled(self):
        cards = [_make_card(type_line="Creature — Wizard")]
        counter = _compute_deck_card_types(cards)
        assert "—" not in counter
        assert counter["Creature"] == 1

    def test_multiple_cards_accumulate(self):
        cards = [
            _make_card(type_line="Creature — Human"),
            _make_card(type_line="Creature — Human"),
            _make_card(type_line="Instant"),
        ]
        counter = _compute_deck_card_types(cards)
        assert counter["Creature"] == 2
        assert counter["Instant"] == 1

    def test_empty_cards_list(self):
        assert _compute_deck_card_types([]) == Counter()


# ---------------------------------------------------------------------------
# Tests: _compute_deck_median_cmc
# ---------------------------------------------------------------------------


class TestComputeDeckMedianCmc(unittest.TestCase):
    def test_default_when_empty(self):
        assert _compute_deck_median_cmc([]) == 3.0

    def test_excludes_commander(self):
        cards = [_make_card(cmc=6.0, is_commander=True)]
        # Only commander cards — result should be default
        assert _compute_deck_median_cmc(cards) == 3.0

    def test_excludes_lands(self):
        cards = [_make_card(type_line="Basic Land — Forest", cmc=0.0)]
        assert _compute_deck_median_cmc(cards) == 3.0

    def test_median_of_odd_count(self):
        cards = [
            _make_card(cmc=1.0),
            _make_card(cmc=3.0),
            _make_card(cmc=5.0),
        ]
        assert _compute_deck_median_cmc(cards) == 3.0

    def test_median_of_even_count(self):
        cards = [
            _make_card(cmc=2.0),
            _make_card(cmc=4.0),
        ]
        assert _compute_deck_median_cmc(cards) == 3.0

    def test_skips_none_cmc(self):
        cards = [
            _make_card(cmc=2.0),
            {**_make_card(), "cmc": None},
        ]
        assert _compute_deck_median_cmc(cards) == 2.0


# ---------------------------------------------------------------------------
# Tests: _collect_existing_scryfall_ids
# ---------------------------------------------------------------------------


class TestCollectExistingScryfallIds(unittest.TestCase):
    def test_collects_all_ids(self):
        cards = [
            _make_card(scryfall_id="aaa"),
            _make_card(scryfall_id="bbb"),
        ]
        assert _collect_existing_scryfall_ids(cards) == {"aaa", "bbb"}

    def test_empty_scryfall_id_excluded(self):
        cards = [
            _make_card(scryfall_id=""),
            _make_card(scryfall_id="aaa"),
        ]
        result = _collect_existing_scryfall_ids(cards)
        assert "" not in result
        assert "aaa" in result

    def test_none_scryfall_id_excluded(self):
        cards = [{"name": "Card Without ID"}]
        result = _collect_existing_scryfall_ids(cards)
        assert result == set()

    def test_empty_list(self):
        assert _collect_existing_scryfall_ids([]) == set()


# ---------------------------------------------------------------------------
# Tests: _extract_image_uri
# ---------------------------------------------------------------------------


class TestExtractImageUri(unittest.TestCase):
    def test_extracts_normal_uri(self):
        card = {"image_uris": {"normal": "https://example.com/card.jpg", "small": "..."}}
        assert _extract_image_uri(card) == "https://example.com/card.jpg"

    def test_returns_none_when_no_image_uris(self):
        assert _extract_image_uri({"name": "Card"}) is None

    def test_returns_none_when_image_uris_not_dict(self):
        # Some double-sided cards have a list; guard against that
        assert _extract_image_uri({"image_uris": None}) is None

    def test_returns_none_when_normal_key_missing(self):
        card = {"image_uris": {"small": "https://example.com/small.jpg"}}
        assert _extract_image_uri(card) is None


# ---------------------------------------------------------------------------
# Tests: _score_card
# ---------------------------------------------------------------------------


class TestScoreCard(unittest.TestCase):
    def test_creature_heavy_deck_scores_creature_higher_than_land(self):
        """A creature-heavy deck's type_match bonus for Creature > Land."""
        deck_card_types = Counter({"Creature": 40, "Human": 20})
        deck_card_count = 40

        creature_card = {"type_line": "Creature — Human", "cmc": 3.0, "rarity": "common"}
        land_card = {"type_line": "Basic Land — Forest", "cmc": 0.0, "rarity": "common"}

        creature_score, _ = _score_card(
            card=creature_card,
            deck_card_types=deck_card_types,
            deck_card_count=deck_card_count,
            deck_median_cmc=3.0,
        )
        land_score, _ = _score_card(
            card=land_card,
            deck_card_types=deck_card_types,
            deck_card_count=deck_card_count,
            deck_median_cmc=3.0,
        )
        assert creature_score > land_score

    def test_mythic_rarity_bonus(self):
        deck_card_types: Counter = Counter()
        score, _ = _score_card(
            card={"type_line": "Sorcery", "cmc": 99, "rarity": "mythic"},
            deck_card_types=deck_card_types,
            deck_card_count=0,
            deck_median_cmc=3.0,
        )
        assert abs(score - 0.1) < 0.01

    def test_rare_rarity_bonus(self):
        deck_card_types: Counter = Counter()
        score, _ = _score_card(
            card={"type_line": "Sorcery", "cmc": 99, "rarity": "rare"},
            deck_card_types=deck_card_types,
            deck_card_count=0,
            deck_median_cmc=3.0,
        )
        assert abs(score - 0.07) < 0.01

    def test_uncommon_rarity_bonus(self):
        deck_card_types: Counter = Counter()
        score, _ = _score_card(
            card={"type_line": "Sorcery", "cmc": 99, "rarity": "uncommon"},
            deck_card_types=deck_card_types,
            deck_card_count=0,
            deck_median_cmc=3.0,
        )
        assert abs(score - 0.03) < 0.01

    def test_common_has_no_rarity_bonus(self):
        deck_card_types: Counter = Counter()
        score, _ = _score_card(
            card={"type_line": "Sorcery", "cmc": 99, "rarity": "common"},
            deck_card_types=deck_card_types,
            deck_card_count=0,
            deck_median_cmc=3.0,
        )
        assert score == 0.0

    def test_cmc_exactly_matching_deck_median_gives_max_cmc_bonus(self):
        deck_card_types: Counter = Counter()
        score, _ = _score_card(
            card={"type_line": "Instant", "cmc": 3.0, "rarity": "common"},
            deck_card_types=deck_card_types,
            deck_card_count=0,
            deck_median_cmc=3.0,
        )
        assert abs(score - 0.3) < 0.01

    def test_cmc_far_from_median_gives_zero_cmc_bonus(self):
        deck_card_types: Counter = Counter()
        score, _ = _score_card(
            card={"type_line": "Instant", "cmc": 10.0, "rarity": "common"},
            deck_card_types=deck_card_types,
            deck_card_count=0,
            deck_median_cmc=3.0,
        )
        # |10.0 - 3.0| = 7, 0.3 - 0.1*7 = -0.4 → capped at 0
        assert score == 0.0

    def test_type_match_capped_at_0_6(self):
        # 100 creatures in deck with card_count=1 → matched_count/card_count = 100 → capped 0.6
        deck_card_types = Counter({"Creature": 100})
        score, _ = _score_card(
            card={"type_line": "Creature", "cmc": 99, "rarity": "common"},
            deck_card_types=deck_card_types,
            deck_card_count=1,
            deck_median_cmc=3.0,
        )
        # type_match should be capped at 0.6; cmc contribution negligible at cmc=99
        assert score >= 0.6
        assert score <= 0.6 + 0.001  # only rarity can add on top

    def test_missing_cmc_skips_cmc_bonus(self):
        deck_card_types: Counter = Counter()
        score, _ = _score_card(
            card={"type_line": "Instant", "cmc": None, "rarity": "common"},
            deck_card_types=deck_card_types,
            deck_card_count=0,
            deck_median_cmc=3.0,
        )
        assert score == 0.0


# ---------------------------------------------------------------------------
# Tests: _build_reason
# ---------------------------------------------------------------------------


class TestBuildReason(unittest.TestCase):
    def test_both_type_and_cmc_match(self):
        deck_card_types = Counter({"Creature": 30, "Human": 10})
        reason = _build_reason(
            type_match=0.5,
            cmc_bonus=0.2,
            deck_median_cmc=3.0,
            type_line="Creature — Human",
            deck_card_types=deck_card_types,
        )
        assert "median CMC" in reason
        assert "3.0" in reason

    def test_type_match_only(self):
        deck_card_types = Counter({"Creature": 30})
        reason = _build_reason(
            type_match=0.5,
            cmc_bonus=0.0,
            deck_median_cmc=3.0,
            type_line="Creature",
            deck_card_types=deck_card_types,
        )
        assert "Creature" in reason
        assert "base" in reason.lower() or "heavy" in reason.lower()

    def test_cmc_match_only(self):
        deck_card_types = Counter({"Creature": 5})
        reason = _build_reason(
            type_match=0.0,
            cmc_bonus=0.2,
            deck_median_cmc=2.5,
            type_line="Instant",
            deck_card_types=deck_card_types,
        )
        assert "mana curve" in reason.lower()
        assert "2.5" in reason

    def test_no_match_returns_color_identity_reason(self):
        deck_card_types = Counter({"Creature": 5})
        reason = _build_reason(
            type_match=0.0,
            cmc_bonus=0.0,
            deck_median_cmc=3.0,
            type_line="Enchantment",
            deck_card_types=deck_card_types,
        )
        assert "color" in reason.lower()

    def test_empty_deck_card_types(self):
        reason = _build_reason(
            type_match=0.0,
            cmc_bonus=0.0,
            deck_median_cmc=3.0,
            type_line="Artifact",
            deck_card_types=Counter(),
        )
        assert isinstance(reason, str)
        assert len(reason) > 0


# ---------------------------------------------------------------------------
# Tests: RecommendationEngine.compute_suggestions_for_deck
# ---------------------------------------------------------------------------


class TestComputeSuggestionsForDeck(unittest.TestCase):
    """Integration-level unit tests for the recommendation engine."""

    def _make_engine(self, cards: list) -> RecommendationEngine:
        deck_repo = MagicMock()
        suggestion_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = {
            "id": 1,
            "name": "Test Deck",
            "cards": cards,
        }
        eng = RecommendationEngine(deck_repo=deck_repo, suggestion_repo=suggestion_repo)
        eng._deck_repo = deck_repo
        return eng, deck_repo

    # --- Deck not found ---

    def test_returns_empty_list_when_deck_not_found(self):
        deck_repo = MagicMock()
        suggestion_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = None
        eng = RecommendationEngine(deck_repo=deck_repo, suggestion_repo=suggestion_repo)

        result = eng.compute_suggestions_for_deck(
            deck_id=999,
            user_id=1,
            new_cards=[_make_new_set_card()],
            set_code="TST",
            set_name="Test Set",
        )
        assert result == []

    # --- Color identity filtering ---

    def test_filters_out_cards_outside_color_identity(self):
        """Cards whose color identity is not a subset of the commander's are excluded."""
        deck_cards = [
            _make_card(color_identity="B", is_commander=True),
        ]
        eng, _ = self._make_engine(deck_cards)

        # Red card — should be filtered out for a mono-black commander
        red_card = _make_new_set_card(scryfall_id="red-001", color_identity="R")
        # Black card — should pass through
        black_card = _make_new_set_card(scryfall_id="black-001", color_identity="B")

        result = eng.compute_suggestions_for_deck(
            deck_id=1,
            user_id=1,
            new_cards=[red_card, black_card],
            set_code="TST",
            set_name="Test Set",
        )
        result_ids = {s["scryfall_id"] for s in result}
        assert "red-001" not in result_ids
        assert "black-001" in result_ids

    def test_colorless_cards_pass_any_color_filter(self):
        """Colorless cards (empty color_identity) are a subset of every identity."""
        deck_cards = [_make_card(color_identity="W", is_commander=True)]
        eng, _ = self._make_engine(deck_cards)

        colorless_card = _make_new_set_card(scryfall_id="colorless-001", color_identity="")
        result = eng.compute_suggestions_for_deck(
            deck_id=1,
            user_id=1,
            new_cards=[colorless_card],
            set_code="TST",
            set_name="Test Set",
        )
        assert any(s["scryfall_id"] == "colorless-001" for s in result)

    def test_filters_cards_already_in_deck(self):
        """Cards with a scryfall_id matching an existing deck card are skipped."""
        deck_cards = [_make_card(scryfall_id="existing-001", color_identity="B")]
        eng, _ = self._make_engine(deck_cards)

        duplicate = _make_new_set_card(scryfall_id="existing-001", color_identity="B")
        result = eng.compute_suggestions_for_deck(
            deck_id=1,
            user_id=1,
            new_cards=[duplicate],
            set_code="TST",
            set_name="Test Set",
        )
        assert result == []

    # --- Top-5 cap ---

    def test_returns_at_most_5_suggestions(self):
        """Even when many cards pass the filter, only 5 are returned."""
        deck_cards = [_make_card(color_identity="B", is_commander=True)]
        eng, _ = self._make_engine(deck_cards)

        new_cards = [
            _make_new_set_card(scryfall_id=f"card-{i:03d}", color_identity="B")
            for i in range(20)
        ]
        result = eng.compute_suggestions_for_deck(
            deck_id=1,
            user_id=1,
            new_cards=new_cards,
            set_code="TST",
            set_name="Test Set",
        )
        assert len(result) <= 5

    def test_sorted_by_score_descending(self):
        """Results are sorted by score DESC."""
        deck_cards = [_make_card(color_identity="B", is_commander=True)]
        eng, _ = self._make_engine(deck_cards)

        new_cards = [
            _make_new_set_card(scryfall_id="mythic-001", color_identity="B", rarity="mythic"),
            _make_new_set_card(scryfall_id="common-001", color_identity="B", rarity="common"),
        ]
        result = eng.compute_suggestions_for_deck(
            deck_id=1,
            user_id=1,
            new_cards=new_cards,
            set_code="TST",
            set_name="Test Set",
        )
        scores = [s["score"] for s in result]
        assert scores == sorted(scores, reverse=True)

    # --- Scoring: creature-heavy deck ---

    def test_creature_heavy_deck_ranks_creature_higher(self):
        """A creature-heavy deck ranks a Creature card above an Instant."""
        # Build a creature-heavy deck (40 creature cards)
        deck_cards = [
            _make_card(scryfall_id=f"dc-{i}", type_line="Creature — Human", color_identity="B,G", cmc=3.0)
            for i in range(40)
        ]
        deck_cards[0]["is_commander"] = True
        deck_cards[0]["color_identity"] = "B,G"

        deck_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = {"id": 1, "name": "Deck", "cards": deck_cards}
        eng = RecommendationEngine(deck_repo=deck_repo, suggestion_repo=MagicMock())

        creature_card = _make_new_set_card(
            scryfall_id="new-creature",
            type_line="Creature — Human",
            color_identity="B,G",
            cmc=3.0,
            rarity="common",
        )
        instant_card = _make_new_set_card(
            scryfall_id="new-instant",
            type_line="Instant",
            color_identity="B",
            cmc=3.0,
            rarity="common",
        )

        result = eng.compute_suggestions_for_deck(
            deck_id=1,
            user_id=1,
            new_cards=[creature_card, instant_card],
            set_code="TST",
            set_name="Test Set",
        )

        id_to_score = {s["scryfall_id"]: s["score"] for s in result}
        assert id_to_score["new-creature"] > id_to_score["new-instant"]

    # --- Suggestion dict shape ---

    def test_suggestion_dict_has_required_fields(self):
        deck_cards = [_make_card(color_identity="B")]
        eng, _ = self._make_engine(deck_cards)

        new_cards = [_make_new_set_card(scryfall_id="shape-001", color_identity="B")]
        result = eng.compute_suggestions_for_deck(
            deck_id=1,
            user_id=1,
            new_cards=new_cards,
            set_code="TST",
            set_name="Test Set",
        )
        assert len(result) == 1
        s = result[0]
        for field in [
            "deck_id", "user_id", "set_code", "scryfall_id",
            "card_name", "mana_cost", "cmc", "type_line", "color_identity",
            "oracle_text", "reason", "score", "image_uri",
        ]:
            assert field in s, f"Missing field: {field}"

    def test_empty_new_cards_returns_empty(self):
        deck_cards = [_make_card(color_identity="B")]
        eng, _ = self._make_engine(deck_cards)

        result = eng.compute_suggestions_for_deck(
            deck_id=1, user_id=1, new_cards=[], set_code="TST", set_name="Test Set"
        )
        assert result == []

    def test_empty_deck_cards_all_colorless_pass(self):
        """Deck with no cards → commander identity = empty set → only colorless new cards pass."""
        deck_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = {"id": 1, "name": "Empty Deck", "cards": []}
        eng = RecommendationEngine(deck_repo=deck_repo, suggestion_repo=MagicMock())

        colored_card = _make_new_set_card(scryfall_id="colored", color_identity="B")
        colorless_card = _make_new_set_card(scryfall_id="colorless", color_identity="")

        result = eng.compute_suggestions_for_deck(
            deck_id=1, user_id=1,
            new_cards=[colored_card, colorless_card],
            set_code="TST", set_name="Test Set",
        )
        ids = {s["scryfall_id"] for s in result}
        assert "colored" not in ids
        assert "colorless" in ids

    def test_image_uri_extracted_from_image_uris_dict(self):
        deck_cards = [_make_card(color_identity="B")]
        eng, _ = self._make_engine(deck_cards)

        new_cards = [
            _make_new_set_card(
                scryfall_id="img-001",
                color_identity="B",
                image_uris={"normal": "https://img.example.com/card.jpg"},
            )
        ]
        result = eng.compute_suggestions_for_deck(
            deck_id=1, user_id=1, new_cards=new_cards, set_code="TST", set_name="Test Set"
        )
        assert result[0]["image_uri"] == "https://img.example.com/card.jpg"

    def test_score_is_rounded_to_4_decimal_places(self):
        deck_cards = [_make_card(color_identity="B")]
        eng, _ = self._make_engine(deck_cards)

        new_cards = [_make_new_set_card(scryfall_id="rnd-001", color_identity="B", rarity="rare")]
        result = eng.compute_suggestions_for_deck(
            deck_id=1, user_id=1, new_cards=new_cards, set_code="TST", set_name="Test Set"
        )
        score = result[0]["score"]
        # round() to 4 places: ensure value equals its 4-decimal rounded form
        assert score == round(score, 4)


# ---------------------------------------------------------------------------
# Tests: compute_suggestions_for_all_decks
# ---------------------------------------------------------------------------


class TestComputeSuggestionsForAllDecks(unittest.TestCase):
    def _make_sql_engine(self, rows: list) -> MagicMock:
        """Build a mock SQLAlchemy engine yielding (deck_id, user_id) rows."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = rows
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = lambda s: mock_conn
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn
        return mock_engine

    def test_returns_zero_when_no_decks(self):
        sql_engine = self._make_sql_engine([])
        suggestion_repo = MagicMock()
        deck_repo = MagicMock()

        total = compute_suggestions_for_all_decks(
            engine=sql_engine,
            suggestion_repo=suggestion_repo,
            deck_repo=deck_repo,
            new_cards=[],
            set_code="TST",
            set_name="Test Set",
        )
        assert total == 0
        suggestion_repo.upsert_suggestions.assert_not_called()

    def test_calls_upsert_for_each_deck(self):
        rows = [(1, 10), (2, 10)]  # (deck_id, user_id)
        sql_engine = self._make_sql_engine(rows)
        suggestion_repo = MagicMock()

        deck_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = {
            "id": 1,
            "name": "Deck",
            "cards": [_make_card(color_identity="B")],
        }

        new_cards = [_make_new_set_card(scryfall_id="new-001", color_identity="B")]

        compute_suggestions_for_all_decks(
            engine=sql_engine,
            suggestion_repo=suggestion_repo,
            deck_repo=deck_repo,
            new_cards=new_cards,
            set_code="TST",
            set_name="Test Set",
        )
        # upsert_suggestions should be called once per deck that yielded suggestions
        assert suggestion_repo.upsert_suggestions.call_count == len(rows)

    def test_skips_decks_with_null_user_id(self):
        rows = [(1, None)]  # user_id is None — should be skipped
        sql_engine = self._make_sql_engine(rows)
        suggestion_repo = MagicMock()
        deck_repo = MagicMock()

        total = compute_suggestions_for_all_decks(
            engine=sql_engine,
            suggestion_repo=suggestion_repo,
            deck_repo=deck_repo,
            new_cards=[_make_new_set_card()],
            set_code="TST",
            set_name="Test Set",
        )
        assert total == 0
        suggestion_repo.upsert_suggestions.assert_not_called()

    def test_isolates_exception_per_deck(self):
        """An exception for one deck does not stop processing of the next."""
        rows = [(1, 10), (2, 10)]
        sql_engine = self._make_sql_engine(rows)
        suggestion_repo = MagicMock()

        call_count = 0

        def get_deck_with_cards(deck_id, user_id):
            nonlocal call_count
            call_count += 1
            if deck_id == 1:
                raise RuntimeError("Simulated failure for deck 1")
            # deck 2 returns a valid deck
            return {
                "id": deck_id,
                "name": "Deck 2",
                "cards": [_make_card(color_identity="B")],
            }

        deck_repo = MagicMock()
        deck_repo.get_deck_with_cards.side_effect = get_deck_with_cards

        new_cards = [_make_new_set_card(scryfall_id="new-001", color_identity="B")]

        total = compute_suggestions_for_all_decks(
            engine=sql_engine,
            suggestion_repo=suggestion_repo,
            deck_repo=deck_repo,
            new_cards=new_cards,
            set_code="TST",
            set_name="Test Set",
        )

        # deck 1 failed, deck 2 succeeded → at least one call to upsert
        assert call_count == 2
        suggestion_repo.upsert_suggestions.assert_called_once()

    def test_total_count_aggregates_across_decks(self):
        rows = [(1, 10), (2, 10)]
        sql_engine = self._make_sql_engine(rows)
        suggestion_repo = MagicMock()

        deck_repo = MagicMock()
        deck_repo.get_deck_with_cards.return_value = {
            "id": 1,
            "name": "Deck",
            "cards": [_make_card(color_identity="B")],
        }

        # 5 black cards → each deck gets up to 5 suggestions
        new_cards = [
            _make_new_set_card(scryfall_id=f"c-{i}", color_identity="B")
            for i in range(5)
        ]

        total = compute_suggestions_for_all_decks(
            engine=sql_engine,
            suggestion_repo=suggestion_repo,
            deck_repo=deck_repo,
            new_cards=new_cards,
            set_code="TST",
            set_name="Test Set",
        )
        # 2 decks × up to 5 suggestions = at most 10
        assert 0 < total <= 10


if __name__ == "__main__":
    unittest.main()
