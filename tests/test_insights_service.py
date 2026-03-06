"""Unit tests for backend.api.services.insights_service.

Tests cover:
- _normalize_color_identity helper
- _parse_price helper
- _parse_date helper
- All 17 InsightsService insight handlers
- InsightsSuggestionEngine signal logic

These are pure-computation tests — no mocking, no database, no HTTP.
InsightsService takes plain List[Dict] and returns structured dicts.
"""

from datetime import datetime, timedelta

import pytest

from backend.api.services.insights_service import (
    INSIGHTS_CATALOG,
    InsightsService,
    InsightsSuggestionEngine,
    _normalize_color_identity,
    _parse_date,
    _parse_price,
)

# ---------------------------------------------------------------------------
# Shared sample data
# ---------------------------------------------------------------------------

_NOW = datetime.now()
_YESTERDAY = _NOW - timedelta(days=1)
_LAST_YEAR = _NOW - timedelta(days=365)


def _make_card(**kwargs):
    """Build a minimal card dict with sensible defaults."""
    defaults = {
        "id": 1,
        "name": "Test Card",
        "rarity": "common",
        "set_name": "TST",
        "price": "1.00",
        "color_identity": "R",
        "created_at": _YESTERDAY.isoformat(),
    }
    defaults.update(kwargs)
    return defaults


SAMPLE_CARDS = [
    _make_card(
        id=1,
        name="Lightning Bolt",
        rarity="common",
        set_name="M10",
        price="0.50",
        color_identity="R",
        created_at=_YESTERDAY.isoformat(),
    ),
    _make_card(
        id=2,
        name="Counterspell",
        rarity="uncommon",
        set_name="M10",
        price="1.20",
        color_identity="U",
        created_at=_YESTERDAY.isoformat(),
    ),
    _make_card(
        id=3,
        name="Dark Ritual",
        rarity="common",
        set_name="LEA",
        price="2.00",
        color_identity="B",
        created_at=_LAST_YEAR.isoformat(),
    ),
    _make_card(
        id=4,
        name="Giant Growth",
        rarity="common",
        set_name="LEA",
        price="0.30",
        color_identity="G",
        created_at=_LAST_YEAR.isoformat(),
    ),
    _make_card(
        id=5,
        name="Plains",
        rarity="common",
        set_name="TST",
        price="0.10",
        color_identity="W",
        created_at=_LAST_YEAR.isoformat(),
    ),
    _make_card(
        id=6,
        name="Black Lotus",
        rarity="mythic rare",
        set_name="LEA",
        price="25000.00",
        color_identity="",
        created_at=_LAST_YEAR.isoformat(),
    ),
]


# ---------------------------------------------------------------------------
# _normalize_color_identity
# ---------------------------------------------------------------------------


def test_normalize_color_identity_none_returns_C():
    assert _normalize_color_identity(None) == "C"


def test_normalize_color_identity_empty_string_returns_C():
    assert _normalize_color_identity("") == "C"


def test_normalize_color_identity_empty_list_literal_returns_C():
    assert _normalize_color_identity("[]") == "C"


def test_normalize_color_identity_single_letter_R():
    assert _normalize_color_identity("R") == "R"


def test_normalize_color_identity_single_letter_U():
    assert _normalize_color_identity("U") == "U"


def test_normalize_color_identity_list_of_letters():
    result = _normalize_color_identity(["R", "G"])
    assert result == "RG"


def test_normalize_color_identity_comma_separated():
    result = _normalize_color_identity("R,G")
    assert result == "RG"


def test_normalize_color_identity_list_string_with_quotes():
    result = _normalize_color_identity("['R', 'G']")
    assert result == "RG"


def test_normalize_color_identity_full_color_name_blue():
    assert _normalize_color_identity("blue") == "U"


def test_normalize_color_identity_full_color_name_white():
    assert _normalize_color_identity("white") == "W"


def test_normalize_color_identity_full_color_name_black():
    assert _normalize_color_identity("black") == "B"


def test_normalize_color_identity_full_color_name_red():
    assert _normalize_color_identity("red") == "R"


def test_normalize_color_identity_full_color_name_green():
    assert _normalize_color_identity("green") == "G"


def test_normalize_color_identity_wubrg_ordering_preserved():
    # Input out of WUBRG order — output must be in WUBRG order
    result = _normalize_color_identity(["G", "W", "U"])
    assert result == "WUG"


def test_normalize_color_identity_list_with_color_names():
    result = _normalize_color_identity(["blue", "red"])
    assert result == "UR"


def test_normalize_color_identity_invalid_string_returns_C():
    assert _normalize_color_identity("xyz") == "C"


def test_normalize_color_identity_invalid_type_returns_C():
    assert _normalize_color_identity(42) == "C"


def test_normalize_color_identity_multicolor_string_WUBRG():
    # "WUBRG" as a single string — each char is a valid color letter
    result = _normalize_color_identity("WUBRG")
    assert result == "WUBRG"


def test_normalize_color_identity_deduplicates():
    result = _normalize_color_identity(["R", "R", "G"])
    assert result == "RG"


def test_normalize_color_identity_list_string_no_quotes():
    # Format: "[R, G]"
    result = _normalize_color_identity("[R, G]")
    assert result == "RG"


# ---------------------------------------------------------------------------
# _parse_price
# ---------------------------------------------------------------------------


def test_parse_price_none_returns_none():
    assert _parse_price(None) is None


def test_parse_price_empty_string_returns_none():
    assert _parse_price("") is None


def test_parse_price_valid_float_string():
    assert _parse_price("1.50") == pytest.approx(1.50)


def test_parse_price_integer():
    assert _parse_price(5) == pytest.approx(5.0)


def test_parse_price_float():
    assert _parse_price(2.99) == pytest.approx(2.99)


def test_parse_price_zero():
    assert _parse_price("0") == pytest.approx(0.0)


def test_parse_price_eu_decimal_comma():
    # "1,50" → 1.50 (European format)
    assert _parse_price("1,50") == pytest.approx(1.50)


def test_parse_price_eu_thousands_and_decimal():
    # "1.234,56" → 1234.56 (EU: dot as thousands, comma as decimal)
    assert _parse_price("1.234,56") == pytest.approx(1234.56)


def test_parse_price_us_thousands_separator():
    # "1,234.56" → 1234.56 (US: comma as thousands, dot as decimal)
    assert _parse_price("1,234.56") == pytest.approx(1234.56)


def test_parse_price_negative_returns_none():
    assert _parse_price("-1.00") is None


def test_parse_price_non_numeric_returns_none():
    assert _parse_price("abc") is None


def test_parse_price_string_integer():
    assert _parse_price("100") == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------


def test_parse_date_none_returns_none():
    assert _parse_date(None) is None


def test_parse_date_empty_string_returns_none():
    assert _parse_date("") is None


def test_parse_date_iso_full():
    result = _parse_date("2026-01-15T10:30:00")
    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 15


def test_parse_date_iso_with_microseconds():
    result = _parse_date("2026-01-15T10:30:00.123456")
    assert isinstance(result, datetime)
    assert result.year == 2026


def test_parse_date_date_only():
    result = _parse_date("2026-01-15")
    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 15


def test_parse_date_space_separator():
    result = _parse_date("2026-01-15 10:30:00")
    assert isinstance(result, datetime)
    assert result.year == 2026


def test_parse_date_invalid_returns_none():
    assert _parse_date("not-a-date") is None


def test_parse_date_preserves_month_and_day():
    result = _parse_date("2025-12-25")
    assert result is not None
    assert result.month == 12
    assert result.day == 25


# ---------------------------------------------------------------------------
# InsightsService — execute dispatch
# ---------------------------------------------------------------------------


def test_execute_unknown_id_raises_value_error():
    svc = InsightsService(cards=[])
    with pytest.raises(ValueError, match="Unknown insight ID"):
        svc.execute("not_real_id")


def test_execute_returns_standard_envelope():
    svc = InsightsService(cards=SAMPLE_CARDS)
    result = svc.execute("total_cards")
    assert "insight_id" in result
    assert "question" in result
    assert "answer_text" in result
    assert "response_type" in result
    assert "data" in result
    assert result["insight_id"] == "total_cards"


def test_execute_all_17_ids_do_not_raise():
    """Smoke test: every catalog ID must execute without error."""
    svc = InsightsService(cards=SAMPLE_CARDS)
    for entry in INSIGHTS_CATALOG:
        result = svc.execute(entry["id"])
        assert result["insight_id"] == entry["id"]


# ---------------------------------------------------------------------------
# Summary handlers
# ---------------------------------------------------------------------------


class TestTotalValue:
    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("total_value")
        assert "€0.00" in result["answer_text"] or "€0" in result["data"]["primary_value"]
        assert result["data"]["primary_value"] == "€0.00"

    def test_with_priced_cards(self):
        cards = [
            _make_card(name="A", price="10.00"),
            _make_card(name="B", price="5.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("total_value")
        assert "€15.00" in result["answer_text"]
        assert result["data"]["primary_value"] == "€15.00"

    def test_partial_price_data(self):
        cards = [
            _make_card(name="A", price="10.00"),
            _make_card(name="B", price=None),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("total_value")
        # Should mention partial coverage
        assert "1 of 2" in result["answer_text"]

    def test_breakdown_by_rarity(self):
        cards = [
            _make_card(name="A", price="10.00", rarity="rare"),
            _make_card(name="B", price="1.00", rarity="common"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("total_value")
        labels = [item["label"] for item in result["data"]["breakdown"]]
        assert "Rare" in labels or "rare" in [label.lower() for label in labels]

    def test_response_type_is_value(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("total_value")
        assert result["response_type"] == "value"


class TestTotalCards:
    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("total_cards")
        assert "0" in result["answer_text"]
        assert result["data"]["primary_value"] == "0"

    def test_nonzero(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("total_cards")
        count = len(SAMPLE_CARDS)
        assert str(count) in result["answer_text"]
        assert result["data"]["primary_value"] == str(count)

    def test_singular_form(self):
        svc = InsightsService(cards=[_make_card()])
        result = svc.execute("total_cards")
        assert "1 card" in result["answer_text"]
        # Should not say "1 cards"
        assert "1 cards" not in result["answer_text"]


class TestAvgCardValue:
    def test_no_prices(self):
        cards = [_make_card(name="A", price=None), _make_card(name="B", price="")]
        svc = InsightsService(cards=cards)
        result = svc.execute("avg_card_value")
        assert "No price data" in result["answer_text"]

    def test_single_card(self):
        cards = [_make_card(name="A", price="5.00")]
        svc = InsightsService(cards=cards)
        result = svc.execute("avg_card_value")
        assert "€5.00" in result["answer_text"]

    def test_multiple_cards(self):
        cards = [
            _make_card(name="A", price="3.00"),
            _make_card(name="B", price="1.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("avg_card_value")
        # avg = 2.00
        assert "€2.00" in result["answer_text"]

    def test_breakdown_contains_min_max_median(self):
        cards = [
            _make_card(name="A", price="1.00"),
            _make_card(name="B", price="3.00"),
            _make_card(name="C", price="5.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("avg_card_value")
        labels = [item["label"] for item in result["data"]["breakdown"]]
        assert "Min" in labels
        assert "Max" in labels
        assert "Median" in labels

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("avg_card_value")
        assert "No price data" in result["answer_text"]


# ---------------------------------------------------------------------------
# Distribution handlers
# ---------------------------------------------------------------------------


class TestByColor:
    def test_counts_colors(self):
        cards = [
            _make_card(name="A", color_identity="R"),
            _make_card(name="B", color_identity="R"),
            _make_card(name="C", color_identity="U"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("by_color")
        items = result["data"]["items"]
        color_map = {item["color"]: item["count"] for item in items}
        assert color_map["R"] == 2
        assert color_map["U"] == 1

    def test_colorless_fallback(self):
        cards = [_make_card(name="Artifact", color_identity="")]
        svc = InsightsService(cards=cards)
        result = svc.execute("by_color")
        items = result["data"]["items"]
        color_map = {item["color"]: item["count"] for item in items}
        assert color_map.get("C", 0) == 1

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("by_color")
        assert isinstance(result["data"]["items"], list)
        assert len(result["data"]["items"]) == 0

    def test_response_type_is_distribution(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("by_color")
        assert result["response_type"] == "distribution"

    def test_percentages_sum_to_100(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("by_color")
        items = result["data"]["items"]
        if items:
            total_pct = sum(item["percentage"] for item in items)
            # Due to rounding, allow slight deviation
            assert abs(total_pct - 100.0) < 2.0


class TestByRarity:
    def test_counts_rarities(self):
        cards = [
            _make_card(name="A", rarity="common"),
            _make_card(name="B", rarity="common"),
            _make_card(name="C", rarity="rare"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("by_rarity")
        items = result["data"]["items"]
        rarity_map = {item["label"]: item["count"] for item in items}
        assert rarity_map["Common"] == 2
        assert rarity_map["Rare"] == 1

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("by_rarity")
        assert result["data"]["items"] == []

    def test_mythic_rare_ordering(self):
        cards = [
            _make_card(name="A", rarity="common"),
            _make_card(name="B", rarity="rare"),
            _make_card(name="C", rarity="mythic"),
            _make_card(name="D", rarity="uncommon"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("by_rarity")
        labels = [item["label"] for item in result["data"]["items"]]
        # rarity_order = ["Mythic", "Rare", "Uncommon", "Common"]
        # capitalize() on "mythic" → "Mythic"; on "rare" → "Rare"
        if "Mythic" in labels and "Rare" in labels:
            assert labels.index("Mythic") < labels.index("Rare")


class TestBySet:
    def test_top_sets(self):
        cards = [
            _make_card(name="A", set_name="Alpha"),
            _make_card(name="B", set_name="Alpha"),
            _make_card(name="C", set_name="Beta"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("by_set")
        items = result["data"]["items"]
        assert items[0]["label"] == "Alpha"
        assert items[0]["count"] == 2

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("by_set")
        assert result["data"]["items"] == []


class TestValueByColor:
    def test_distributes_value(self):
        cards = [
            _make_card(name="A", color_identity="R", price="10.00"),
            _make_card(name="B", color_identity="U", price="5.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("value_by_color")
        items = result["data"]["items"]
        color_map = {item["color"]: item["count"] for item in items}
        # Red should be ~10.0, Blue ~5.0
        assert color_map["R"] == pytest.approx(10.0)
        assert color_map["U"] == pytest.approx(5.0)

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("value_by_color")
        assert result["data"]["items"] == []

    def test_answer_mentions_top_color(self):
        cards = [
            _make_card(name="A", color_identity="R", price="100.00"),
            _make_card(name="B", color_identity="U", price="1.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("value_by_color")
        assert "Red" in result["answer_text"]


class TestValueBySet:
    def test_ranks_sets(self):
        cards = [
            _make_card(name="A", set_name="Alpha", price="100.00"),
            _make_card(name="B", set_name="Beta", price="1.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("value_by_set")
        items = result["data"]["items"]
        assert items[0]["label"] == "Alpha"

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("value_by_set")
        assert "No price data" in result["answer_text"]


# ---------------------------------------------------------------------------
# Ranking handlers
# ---------------------------------------------------------------------------


class TestMostValuable:
    def test_top10_sorted_desc(self):
        cards = [_make_card(name=f"Card{i}", price=str(float(i))) for i in range(1, 16)]
        svc = InsightsService(cards=cards)
        result = svc.execute("most_valuable")
        items = result["data"]["items"]
        assert len(items) <= 10
        # First item should be most expensive
        assert items[0]["name"] == "Card15"

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("most_valuable")
        assert result["data"]["items"] == []

    def test_answer_mentions_top_card(self):
        cards = [
            _make_card(name="Cheap", price="1.00"),
            _make_card(name="Expensive", price="999.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("most_valuable")
        assert "Expensive" in result["answer_text"]

    def test_excludes_zero_price_cards(self):
        cards = [
            _make_card(name="Zero", price="0.00"),
            _make_card(name="Priced", price="5.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("most_valuable")
        names = [item["name"] for item in result["data"]["items"]]
        assert "Zero" not in names


class TestLeastValuable:
    def test_sorted_ascending(self):
        cards = [
            _make_card(name="Cheap", price="0.10"),
            _make_card(name="Mid", price="1.00"),
            _make_card(name="Expensive", price="10.00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("least_valuable")
        items = result["data"]["items"]
        assert items[0]["name"] == "Cheap"

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("least_valuable")
        assert result["data"]["items"] == []


class TestMostCollectedSet:
    def test_counts(self):
        cards = [
            _make_card(name="A", set_name="Big"),
            _make_card(name="B", set_name="Big"),
            _make_card(name="C", set_name="Small"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("most_collected_set")
        items = result["data"]["items"]
        assert items[0]["name"] == "Big"
        assert "2" in items[0]["detail"]

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("most_collected_set")
        assert result["data"]["items"] == []


# ---------------------------------------------------------------------------
# Patterns handlers
# ---------------------------------------------------------------------------


class TestDuplicates:
    def test_no_dupes(self):
        cards = [
            _make_card(name="Alpha", id=1),
            _make_card(name="Beta", id=2),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("duplicates")
        assert "No duplicate" in result["answer_text"]
        assert result["data"]["items"] == []

    def test_with_dupes(self):
        cards = [
            _make_card(name="Lightning Bolt", id=1),
            _make_card(name="Lightning Bolt", id=2),
            _make_card(name="Lightning Bolt", id=3),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("duplicates")
        assert "Lightning Bolt" in result["answer_text"] or len(result["data"]["items"]) > 0
        items = result["data"]["items"]
        assert len(items) == 1
        assert items[0]["name"] == "Lightning Bolt"
        assert "3 copies" in items[0]["detail"]

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("duplicates")
        assert "No duplicate" in result["answer_text"]


class TestMissingColors:
    def test_all_present(self):
        cards = [
            _make_card(name="W", color_identity="W"),
            _make_card(name="U", color_identity="U"),
            _make_card(name="B", color_identity="B"),
            _make_card(name="R", color_identity="R"),
            _make_card(name="G", color_identity="G"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("missing_colors")
        assert "all 5" in result["answer_text"]

    def test_some_missing(self):
        cards = [_make_card(name="Red Card", color_identity="R")]
        svc = InsightsService(cards=cards)
        result = svc.execute("missing_colors")
        assert "Missing" in result["answer_text"]
        # Should list White, Blue, Black, Green as missing
        items = result["data"]["items"]
        missing_items = [item for item in items if not item["present"]]
        assert len(missing_items) == 4

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("missing_colors")
        # All 5 colors missing
        assert "Missing" in result["answer_text"]
        items = result["data"]["items"]
        assert all(not item["present"] for item in items)

    def test_items_cover_all_wubrg(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("missing_colors")
        items = result["data"]["items"]
        # Must have exactly 5 items (one per WUBRG color)
        assert len(items) == 5


class TestNoPrice:
    def test_all_priced(self):
        cards = [_make_card(name="A", price="1.00"), _make_card(name="B", price="2.00")]
        svc = InsightsService(cards=cards)
        result = svc.execute("no_price")
        assert "All cards have price data" in result["answer_text"]

    def test_some_unpriced(self):
        cards = [
            _make_card(name="Priced", price="1.00"),
            _make_card(name="Unpriced", price=None),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("no_price")
        assert "1 of 2" in result["answer_text"]
        items = result["data"]["items"]
        assert len(items) == 1
        assert items[0]["name"] == "Unpriced"

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("no_price")
        assert "All cards have price data" in result["answer_text"]


class TestSingletonSets:
    def test_none(self):
        cards = [
            _make_card(name="A", set_name="Alpha"),
            _make_card(name="B", set_name="Alpha"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("singleton_sets")
        assert "All sets have more than one card" in result["answer_text"]

    def test_some(self):
        cards = [
            _make_card(name="A", set_name="Alpha"),
            _make_card(name="B", set_name="Alpha"),
            _make_card(name="C", set_name="Beta"),  # singleton
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("singleton_sets")
        assert "1 set" in result["answer_text"]
        items = result["data"]["items"]
        assert len(items) == 1
        assert items[0]["name"] == "Beta"

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("singleton_sets")
        assert "All sets" in result["answer_text"]


# ---------------------------------------------------------------------------
# Activity handlers
# ---------------------------------------------------------------------------


class TestRecentAdditions:
    def test_none_recent(self):
        cards = [
            _make_card(name="Old", created_at=_LAST_YEAR.isoformat()),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("recent_additions")
        assert "No cards added in the last 7 days" in result["answer_text"]
        assert result["data"]["items"] == []

    def test_some_recent(self):
        cards = [
            _make_card(name="New", created_at=_YESTERDAY.isoformat()),
            _make_card(name="Old", created_at=_LAST_YEAR.isoformat()),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("recent_additions")
        assert "1 card" in result["answer_text"]
        items = result["data"]["items"]
        assert len(items) == 1
        assert items[0]["name"] == "New"

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("recent_additions")
        assert "No cards added" in result["answer_text"]

    def test_response_type_is_list(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("recent_additions")
        assert result["response_type"] == "list"


class TestMonthlySummary:
    def test_no_dates(self):
        cards = [_make_card(name="A", created_at=None)]
        svc = InsightsService(cards=cards)
        result = svc.execute("monthly_summary")
        assert "No activity data" in result["answer_text"]

    def test_with_dates(self):
        cards = [
            _make_card(name="A", created_at="2026-01-15T10:00:00"),
            _make_card(name="B", created_at="2026-01-20T12:00:00"),
            _make_card(name="C", created_at="2026-02-01T09:00:00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("monthly_summary")
        items = result["data"]["items"]
        assert len(items) == 2  # Jan and Feb 2026
        # Should be chronological
        assert "Jan 2026" in items[0]["period"]
        assert items[0]["count"] == 2
        assert items[1]["count"] == 1

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("monthly_summary")
        assert "No activity data" in result["answer_text"]

    def test_response_type_is_timeline(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("monthly_summary")
        assert result["response_type"] == "timeline"

    def test_max_12_months(self):
        # Generate 15 months of data
        cards = []
        for month in range(1, 16):
            year = 2025 if month <= 12 else 2026
            m = month if month <= 12 else month - 12
            cards.append(_make_card(name=f"Card{month}", created_at=f"{year}-{m:02d}-01T00:00:00"))
        svc = InsightsService(cards=cards)
        result = svc.execute("monthly_summary")
        assert len(result["data"]["items"]) <= 12


class TestBiggestMonth:
    def test_no_dates(self):
        cards = [_make_card(name="A", created_at=None)]
        svc = InsightsService(cards=cards)
        result = svc.execute("biggest_month")
        assert "No activity data" in result["answer_text"]

    def test_with_dates(self):
        cards = [
            _make_card(name="A", created_at="2026-01-15T00:00:00"),
            _make_card(name="B", created_at="2026-01-20T00:00:00"),
            _make_card(name="C", created_at="2026-01-25T00:00:00"),
            _make_card(name="D", created_at="2026-02-01T00:00:00"),
        ]
        svc = InsightsService(cards=cards)
        result = svc.execute("biggest_month")
        assert "January 2026" in result["answer_text"]
        assert "3 cards" in result["answer_text"]

    def test_empty_collection(self):
        svc = InsightsService(cards=[])
        result = svc.execute("biggest_month")
        assert "No activity data" in result["answer_text"]

    def test_response_type_is_timeline(self):
        svc = InsightsService(cards=SAMPLE_CARDS)
        result = svc.execute("biggest_month")
        assert result["response_type"] == "timeline"


# ---------------------------------------------------------------------------
# InsightsSuggestionEngine
# ---------------------------------------------------------------------------

_VALID_IDS = {entry["id"] for entry in INSIGHTS_CATALOG}


class TestInsightsSuggestionEngine:
    def test_empty_collection_returns_non_empty_suggestions(self):
        engine = InsightsSuggestionEngine(cards=[])
        suggestions = engine.get_suggestions()
        assert len(suggestions) > 0

    def test_all_ids_valid(self):
        engine = InsightsSuggestionEngine(cards=SAMPLE_CARDS)
        suggestions = engine.get_suggestions()
        for s in suggestions:
            assert s["id"] in _VALID_IDS, f"Invalid ID: {s['id']}"

    def test_returns_at_most_limit(self):
        engine = InsightsSuggestionEngine(cards=SAMPLE_CARDS)
        for limit in [1, 3, 6, 10]:
            suggestions = engine.get_suggestions(limit=limit)
            assert len(suggestions) <= limit

    def test_suggestions_have_id_and_label(self):
        engine = InsightsSuggestionEngine(cards=SAMPLE_CARDS)
        suggestions = engine.get_suggestions()
        for s in suggestions:
            assert "id" in s
            assert "label" in s
            assert s["label"]  # non-empty

    def test_duplicates_signal_boosts_duplicates(self):
        # Collection with duplicates
        cards = [
            _make_card(name="Lightning Bolt", id=1),
            _make_card(name="Lightning Bolt", id=2),
        ]
        engine = InsightsSuggestionEngine(cards=cards)
        suggestions = engine.get_suggestions(limit=10)
        ids = [s["id"] for s in suggestions]
        assert "duplicates" in ids

    def test_recent_activity_boosts_recent_additions(self):
        cards = [_make_card(name="NewCard", created_at=_YESTERDAY.isoformat())]
        engine = InsightsSuggestionEngine(cards=cards)
        suggestions = engine.get_suggestions(limit=10)
        ids = [s["id"] for s in suggestions]
        assert "recent_additions" in ids

    def test_missing_colors_boosts_missing_colors(self):
        # Only red cards → 4 colors missing
        cards = [_make_card(name="Bolt", color_identity="R")]
        engine = InsightsSuggestionEngine(cards=cards)
        suggestions = engine.get_suggestions(limit=10)
        ids = [s["id"] for s in suggestions]
        assert "missing_colors" in ids

    def test_large_collection_boosts_by_color(self):
        cards = [_make_card(name=f"Card{i}", id=i) for i in range(101)]
        engine = InsightsSuggestionEngine(cards=cards)
        suggestions = engine.get_suggestions(limit=10)
        ids = [s["id"] for s in suggestions]
        assert "by_color" in ids

    def test_unpriced_cards_boost_no_price(self):
        cards = [_make_card(name=f"Card{i}", id=i, price=None) for i in range(12)]
        engine = InsightsSuggestionEngine(cards=cards)
        suggestions = engine.get_suggestions(limit=10)
        ids = [s["id"] for s in suggestions]
        assert "no_price" in ids

    def test_total_value_always_included(self):
        """total_value has the highest base signal and should appear in suggestions."""
        engine = InsightsSuggestionEngine(cards=SAMPLE_CARDS)
        suggestions = engine.get_suggestions(limit=6)
        ids = [s["id"] for s in suggestions]
        assert "total_value" in ids

    def test_empty_collection_includes_total_cards(self):
        engine = InsightsSuggestionEngine(cards=[])
        suggestions = engine.get_suggestions(limit=6)
        ids = [s["id"] for s in suggestions]
        assert "total_cards" in ids or "total_value" in ids

    def test_high_variance_boosts_most_valuable(self):
        cards = [
            _make_card(name="Cheap", price="0.01"),
            _make_card(name="Expensive", price="10000.00"),
        ]
        engine = InsightsSuggestionEngine(cards=cards)
        suggestions = engine.get_suggestions(limit=10)
        ids = [s["id"] for s in suggestions]
        assert "most_valuable" in ids
