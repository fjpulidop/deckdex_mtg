"""TappedOut CSV parser.

Expected headers: Qty, Name, Set, [...]
"""
import csv
import io
from typing import List
from .base import ParsedCard


def parse(content: str) -> List[ParsedCard]:
    """Parse TappedOut CSV export into ParsedCard list."""
    reader = csv.DictReader(io.StringIO(content))
    cards: List[ParsedCard] = []
    for row in reader:
        name = (row.get("Name") or "").strip()
        if not name:
            continue
        try:
            qty = int(float(row.get("Qty") or 1))
        except (ValueError, TypeError):
            qty = 1
        set_name = (row.get("Set") or "").strip() or None
        cards.append(ParsedCard(name=name, set_name=set_name, quantity=max(1, qty)))
    return cards
