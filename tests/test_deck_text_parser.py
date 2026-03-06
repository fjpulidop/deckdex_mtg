"""Unit tests for deckdex.importers.deck_text.parse_deck_text."""

from deckdex.importers.deck_text import parse_deck_text


def test_parse_standard_lines():
    result = parse_deck_text("4 Lightning Bolt\n2 Counterspell")
    assert len(result) == 2
    assert result[0] == {"name": "Lightning Bolt", "quantity": 4, "is_commander": False}
    assert result[1] == {"name": "Counterspell", "quantity": 2, "is_commander": False}


def test_parse_commander_section():
    text = "//Commander\n1 Atraxa, Praetors' Voice\n//Mainboard\n4 Lightning Bolt"
    result = parse_deck_text(text)
    assert len(result) == 2
    assert result[0]["name"] == "Atraxa, Praetors' Voice"
    assert result[0]["is_commander"] is True
    assert result[1]["name"] == "Lightning Bolt"
    assert result[1]["is_commander"] is False


def test_parse_commander_section_case_insensitive():
    text = "//COMMANDER\n1 Thalia, Guardian of Thraben"
    result = parse_deck_text(text)
    assert len(result) == 1
    assert result[0]["is_commander"] is True


def test_parse_mixed_sections():
    text = "//Commander\n1 Atraxa, Praetors' Voice\n//Sideboard\n2 Force of Will\n"
    result = parse_deck_text(text)
    assert len(result) == 2
    assert result[0]["is_commander"] is True
    assert result[1]["is_commander"] is False  # //Sideboard resets the flag


def test_parse_blank_lines_skipped():
    text = "\n\n4 Lightning Bolt\n\n2 Counterspell\n"
    result = parse_deck_text(text)
    assert len(result) == 2


def test_parse_comment_only_lines():
    text = "// This is a comment\n4 Lightning Bolt"
    result = parse_deck_text(text)
    assert len(result) == 1
    assert result[0]["name"] == "Lightning Bolt"
    assert result[0]["is_commander"] is False


def test_parse_quantity_greater_than_one():
    result = parse_deck_text("4 Llanowar Elves")
    assert result[0]["quantity"] == 4


def test_parse_quantity_one_explicit():
    result = parse_deck_text("1 Sol Ring")
    assert result[0]["quantity"] == 1


def test_parse_empty_text():
    result = parse_deck_text("")
    assert result == []


def test_parse_only_headers_and_blanks():
    result = parse_deck_text("//Commander\n\n//Mainboard\n\n")
    assert result == []


def test_parse_quantity_minimum_is_one():
    # Hypothetically malformed "0 Card" still produces quantity 1
    result = parse_deck_text("0 Lightning Bolt")
    assert result[0]["quantity"] == 1


def test_parse_card_name_with_comma():
    result = parse_deck_text("1 Atraxa, Praetors' Voice")
    assert result[0]["name"] == "Atraxa, Praetors' Voice"


def test_parse_whitespace_trimmed():
    result = parse_deck_text("  2   Counterspell  ")
    assert result[0]["name"] == "Counterspell"
    assert result[0]["quantity"] == 2
