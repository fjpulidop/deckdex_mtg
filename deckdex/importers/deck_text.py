"""Deck list text parser for the deck import feature.

Parses MTGO-style deck lists with optional section headers:
  //Commander
  1 Atraxa, Praetors' Voice
  //Mainboard
  4 Lightning Bolt
  2 Counterspell

Lines starting with // are treated as section headers.
Blank lines are skipped.
Unrecognised // lines are also skipped.
"""

import re
from typing import List, TypedDict

_LINE_RE = re.compile(r"^(\d+)\s+(.+)$")

_COMMANDER_HEADER = re.compile(r"^//\s*commander\s*$", re.IGNORECASE)


class DeckParsedCard(TypedDict):
    name: str
    quantity: int
    is_commander: bool


def parse_deck_text(text: str) -> List[DeckParsedCard]:
    """Parse MTGO-style deck list text into a list of DeckParsedCard entries.

    Args:
        text: Raw deck list text. Supports optional //Section headers.
              Lines matching ``<qty> <name>`` are parsed as cards.
              Lines starting with // are treated as section headers or skipped.
              Blank lines are skipped.

    Returns:
        List of DeckParsedCard TypedDicts with ``name``, ``quantity``, and
        ``is_commander`` fields.

    Example:
        >>> parse_deck_text("//Commander\\n1 Atraxa, Praetors' Voice\\n//Mainboard\\n4 Lightning Bolt")
        [{'name': "Atraxa, Praetors' Voice", 'quantity': 1, 'is_commander': True},
         {'name': 'Lightning Bolt', 'quantity': 4, 'is_commander': False}]
    """
    cards: List[DeckParsedCard] = []
    is_commander_section = False

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("//"):
            # Detect commander section header; any other // line resets it
            is_commander_section = bool(_COMMANDER_HEADER.match(line))
            continue

        m = _LINE_RE.match(line)
        if m:
            qty = max(1, int(m.group(1)))
            name = m.group(2).strip()
            if name:
                cards.append(
                    DeckParsedCard(
                        name=name,
                        quantity=qty,
                        is_commander=is_commander_section,
                    )
                )

    return cards
