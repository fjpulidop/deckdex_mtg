"""MTGO text decklist parser.

Line format: "4 Lightning Bolt"
Lines starting with // or empty lines are skipped.
"""
import re
from typing import List
from .base import ParsedCard

_LINE_RE = re.compile(r'^(\d+)\s+(.+)$')


def parse(content: str) -> List[ParsedCard]:
    """Parse MTGO plain-text decklist into ParsedCard list."""
    cards: List[ParsedCard] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        m = _LINE_RE.match(line)
        if m:
            qty = max(1, int(m.group(1)))
            name = m.group(2).strip()
            if name:
                cards.append(ParsedCard(name=name, set_name=None, quantity=qty))
    return cards
