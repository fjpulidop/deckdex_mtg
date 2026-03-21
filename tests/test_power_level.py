"""Unit tests for deckdex/services/power_level.py"""

import pytest

from deckdex.services.power_level import (
    FactorBreakdown,
    _build_summary,
    _compute_bracket,
    estimate_power_level,
)


def _card(
    name: str,
    description: str = "",
    type_: str = "Instant",
    cmc: float = 2.0,
    edhrec_rank: int = 999,
    quantity: int = 1,
) -> dict:
    return {
        "name": name,
        "description": description,
        "type": type_,
        "cmc": cmc,
        "edhrec_rank": edhrec_rank,
        "quantity": quantity,
    }


@pytest.fixture()
def empty_deck():
    return []


@pytest.fixture()
def fast_mana_deck():
    return [
        _card("Sol Ring", cmc=1),
        _card("Mana Crypt", cmc=0),
        _card("Mana Vault", cmc=1),
        _card("Chrome Mox", cmc=0),
    ]


@pytest.fixture()
def tutor_deck():
    return [
        _card("Demonic Tutor", description="Search your library for a card"),
        _card("Vampiric Tutor", description="Search your library for a card"),
        _card("Enlightened Tutor", description="Search your library for a card"),
        _card("Imperial Seal", description="Search your library for a card"),
        _card("Mystical Tutor", description="Search your library for a card"),
    ]


@pytest.fixture()
def basic_land_deck():
    """99 basic lands + 1 plain creature commander."""
    lands = [_card("Plains", type_="Basic Land — Plains", cmc=0) for _ in range(99)]
    commander = _card("Isamaru, Hound of Konda", type_="Legendary Creature — Dog", cmc=1)
    return lands + [commander]


@pytest.fixture()
def cehdh_deck():
    """Representative cEDH-style input with fast mana, tutors, and combos."""
    return [
        _card("Sol Ring", cmc=1),
        _card("Mana Crypt", cmc=0),
        _card("Mana Vault", cmc=1),
        _card("Chrome Mox", cmc=0),
        _card("Demonic Tutor", description="Search your library for a card", cmc=2),
        _card("Vampiric Tutor", description="Search your library for a card", cmc=1),
        _card("Enlightened Tutor", description="Search your library for a card", cmc=1),
        _card("Imperial Seal", description="Search your library for a card", cmc=1),
        _card("Mystical Tutor", description="Search your library for a card", cmc=1),
        _card("Thassa's Oracle", cmc=2),
        _card("Demonic Consultation", cmc=1),
        _card("Tainted Pact", cmc=2),
        _card("Flooded Strand", type_="Land", cmc=0),
        _card("Polluted Delta", type_="Land", cmc=0),
        _card("Scalding Tarn", type_="Land", cmc=0),
        _card("Misty Rainforest", type_="Land", cmc=0),
        _card("Verdant Catacombs", type_="Land", cmc=0),
        _card("Bloodstained Mire", type_="Land", cmc=0),
        _card("Wooded Foothills", type_="Land", cmc=0),
        _card("Windswept Heath", type_="Land", cmc=0),
        _card("Marsh Flats", type_="Land", cmc=0),
        _card("Arid Mesa", type_="Land", cmc=0),
    ]


class TestEmptyDeck:
    def test_score_is_one(self, empty_deck):
        result = estimate_power_level(empty_deck)
        assert result.score == 1.0

    def test_bracket_is_one(self, empty_deck):
        result = estimate_power_level(empty_deck)
        assert result.bracket == 1

    def test_summary_mentions_no_cards(self, empty_deck):
        result = estimate_power_level(empty_deck)
        assert "1" in result.summary


class TestFastMana:
    def test_four_fast_mana_cards_max_factor(self, fast_mana_deck):
        result = estimate_power_level(fast_mana_deck)
        assert result.breakdown.fast_mana == 1.0

    def test_score_elevated(self, fast_mana_deck):
        result = estimate_power_level(fast_mana_deck)
        assert result.score >= 4.0

    def test_partial_fast_mana(self):
        cards = [_card("Sol Ring", cmc=1)]
        result = estimate_power_level(cards)
        assert result.breakdown.fast_mana == pytest.approx(0.25)


class TestTutors:
    def test_five_tutors_max_factor(self, tutor_deck):
        result = estimate_power_level(tutor_deck)
        assert result.breakdown.tutors == 1.0

    def test_no_tutors_zero_factor(self):
        cards = [_card("Lightning Bolt")]
        result = estimate_power_level(cards)
        assert result.breakdown.tutors == 0.0

    def test_partial_tutors(self):
        cards = [
            _card("Demonic Tutor", description="Search your library for a card"),
            _card("Vampiric Tutor", description="Search your library for a card"),
        ]
        result = estimate_power_level(cards)
        # 2 tutors / 5 = 0.4
        assert result.breakdown.tutors == pytest.approx(0.4)


class TestComboPieces:
    def test_known_combo_pieces_detected(self):
        cards = [
            _card("Thassa's Oracle", cmc=2),
            _card("Demonic Consultation", cmc=1),
        ]
        result = estimate_power_level(cards)
        assert result.breakdown.combo_pieces > 0.0

    def test_infinite_in_oracle_text_detected(self):
        cards = [
            _card("Custom Combo Card", description="Creates infinite tokens"),
        ]
        result = estimate_power_level(cards)
        assert result.breakdown.combo_pieces > 0.0

    def test_three_combo_pieces_max_factor(self):
        cards = [
            _card("Thassa's Oracle"),
            _card("Demonic Consultation"),
            _card("Tainted Pact"),
        ]
        result = estimate_power_level(cards)
        assert result.breakdown.combo_pieces == 1.0


class TestAvgCmc:
    def test_low_cmc_deck_high_score(self):
        cards = [_card(f"Spell{i}", cmc=1.0) for i in range(10)]
        result = estimate_power_level(cards)
        # avg_cmc <= 1.5 → 1.0
        assert result.breakdown.avg_cmc == 1.0

    def test_high_cmc_deck_low_score(self):
        cards = [_card(f"Spell{i}", cmc=6.0) for i in range(10)]
        result = estimate_power_level(cards)
        # avg_cmc > 4.0 → 0.10
        assert result.breakdown.avg_cmc == pytest.approx(0.10)

    def test_cmc_2_0_band(self):
        cards = [_card(f"Spell{i}", cmc=2.0) for i in range(10)]
        result = estimate_power_level(cards)
        # avg_cmc <= 2.0 → 0.85
        assert result.breakdown.avg_cmc == pytest.approx(0.85)

    def test_lands_excluded_from_avg_cmc(self):
        # All lands: should return 0.5 (fallback for no non-lands)
        cards = [_card("Swamp", type_="Basic Land — Swamp", cmc=0.0) for _ in range(5)]
        result = estimate_power_level(cards)
        assert result.breakdown.avg_cmc == 0.5

    def test_cmc_weighted_by_quantity(self):
        # One copy of CMC-1 card (qty=1) and one copy of CMC-3 (qty=1) → avg=2.0 → 0.85
        cards = [
            {"name": "A", "description": "", "type": "Instant", "cmc": 1.0, "edhrec_rank": 999, "quantity": 1},
            {"name": "B", "description": "", "type": "Instant", "cmc": 3.0, "edhrec_rank": 999, "quantity": 1},
        ]
        result = estimate_power_level(cards)
        assert result.breakdown.avg_cmc == pytest.approx(0.85)


class TestLandQuality:
    def test_ten_premium_lands_max_factor(self):
        lands = [
            _card("Flooded Strand", type_="Land"),
            _card("Polluted Delta", type_="Land"),
            _card("Scalding Tarn", type_="Land"),
            _card("Misty Rainforest", type_="Land"),
            _card("Verdant Catacombs", type_="Land"),
            _card("Bloodstained Mire", type_="Land"),
            _card("Wooded Foothills", type_="Land"),
            _card("Windswept Heath", type_="Land"),
            _card("Marsh Flats", type_="Land"),
            _card("Arid Mesa", type_="Land"),
        ]
        result = estimate_power_level(lands)
        assert result.breakdown.land_quality == 1.0

    def test_no_premium_lands_zero_factor(self):
        cards = [_card("Swamp", type_="Basic Land — Swamp") for _ in range(5)]
        result = estimate_power_level(cards)
        assert result.breakdown.land_quality == 0.0

    def test_five_fetchlands_half_factor(self):
        lands = [
            _card("Flooded Strand", type_="Land"),
            _card("Polluted Delta", type_="Land"),
            _card("Scalding Tarn", type_="Land"),
            _card("Misty Rainforest", type_="Land"),
            _card("Verdant Catacombs", type_="Land"),
        ]
        result = estimate_power_level(lands)
        assert result.breakdown.land_quality == pytest.approx(0.5)


class TestStapleDensity:
    def test_high_edhrec_rank_not_staple(self):
        cards = [_card("Obscure Card", edhrec_rank=10000)]
        result = estimate_power_level(cards)
        assert result.breakdown.staple_density == 0.0

    def test_low_edhrec_rank_is_staple(self):
        cards = [_card("Sol Ring", edhrec_rank=1)]
        result = estimate_power_level(cards)
        assert result.breakdown.staple_density > 0.0

    def test_none_edhrec_rank_skipped(self):
        cards = [{"name": "Card", "description": "", "type": "Instant", "cmc": 2.0, "edhrec_rank": None, "quantity": 1}]
        result = estimate_power_level(cards)
        assert result.breakdown.staple_density == 0.0


class TestComputeBracket:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (1.0, 1),
            (3.0, 1),
            (3.9, 1),
            (4.0, 2),
            (5.9, 2),
            (6.0, 3),
            (7.9, 3),
            (8.0, 4),
            (10.0, 4),
        ],
    )
    def test_bracket_thresholds(self, score, expected):
        assert _compute_bracket(score) == expected


class TestBuildSummary:
    def test_returns_non_empty_string(self):
        bd = FactorBreakdown(
            fast_mana=0.5,
            tutors=0.2,
            combo_pieces=0.0,
            avg_cmc=0.7,
            land_quality=0.6,
            staple_density=0.3,
        )
        result = _build_summary(6.5, bd)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_score_appears_in_summary(self):
        bd = FactorBreakdown(
            fast_mana=0.0,
            tutors=0.0,
            combo_pieces=0.0,
            avg_cmc=0.5,
            land_quality=0.0,
            staple_density=0.0,
        )
        result = _build_summary(3.0, bd)
        assert "3" in result

    def test_positives_mentioned_when_high(self):
        bd = FactorBreakdown(
            fast_mana=1.0,
            tutors=1.0,
            combo_pieces=0.0,
            avg_cmc=0.3,
            land_quality=0.0,
            staple_density=0.0,
        )
        result = _build_summary(7.0, bd)
        assert "fast mana" in result or "tutors" in result

    def test_absence_mentioned_when_zero(self):
        bd = FactorBreakdown(
            fast_mana=0.0,
            tutors=0.0,
            combo_pieces=0.0,
            avg_cmc=1.0,
            land_quality=0.0,
            staple_density=0.0,
        )
        result = _build_summary(2.0, bd)
        assert "no" in result


class TestBasicLandDeck:
    def test_basic_land_deck_low_score(self, basic_land_deck):
        result = estimate_power_level(basic_land_deck)
        assert result.score <= 3.0


class TestCEDHDeck:
    def test_cehdh_style_deck_high_score(self, cehdh_deck):
        result = estimate_power_level(cehdh_deck)
        assert result.score >= 8.0

    def test_cehdh_bracket_is_four(self, cehdh_deck):
        result = estimate_power_level(cehdh_deck)
        assert result.bracket == 4


class TestKnownHighPowerDeck:
    def test_sol_ring_mana_crypt_tutors_fetchlands_score_above_six(self):
        """A 100-card list with Sol Ring, Mana Crypt, tutors, 5 fetchlands, and realistic EDHREC ranks produces score >= 6.0."""
        # Use realistic EDHREC ranks: Sol Ring ~1, Mana Crypt ~2, Demonic Tutor ~5, Vampiric Tutor ~10
        cards = [
            _card("Sol Ring", cmc=1, edhrec_rank=1),
            _card("Mana Crypt", cmc=0, edhrec_rank=2),
            _card("Mana Vault", cmc=1, edhrec_rank=3),
            _card("Chrome Mox", cmc=0, edhrec_rank=4),
            _card("Demonic Tutor", description="Search your library for a card", cmc=2, edhrec_rank=5),
            _card("Vampiric Tutor", description="Search your library for a card", cmc=1, edhrec_rank=6),
            _card("Enlightened Tutor", description="Search your library for a card", cmc=1, edhrec_rank=7),
            _card("Imperial Seal", description="Search your library for a card", cmc=1, edhrec_rank=8),
            _card("Mystical Tutor", description="Search your library for a card", cmc=1, edhrec_rank=9),
            _card("Flooded Strand", type_="Land", cmc=0, edhrec_rank=10),
            _card("Polluted Delta", type_="Land", cmc=0, edhrec_rank=11),
            _card("Scalding Tarn", type_="Land", cmc=0, edhrec_rank=12),
            _card("Misty Rainforest", type_="Land", cmc=0, edhrec_rank=13),
            _card("Verdant Catacombs", type_="Land", cmc=0, edhrec_rank=14),
        ]
        # Pad to 100 cards with basic lands (cmc=0, land type, high edhrec_rank)
        padding = [_card(f"Forest {i}", type_="Basic Land — Forest", cmc=0) for i in range(86)]
        result = estimate_power_level(cards + padding)
        assert result.score >= 6.0
