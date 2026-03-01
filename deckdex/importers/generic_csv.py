"""Generic CSV parser — best-effort column detection.

Detects a name column and an optional quantity column.
"""
import csv
import io
from typing import List, Optional
from .base import ParsedCard

_NAME_CANDIDATES = ("name", "input name", "card name", "card")
_QTY_CANDIDATES = ("qty", "count", "quantity", "amount", "copies")
_SET_CANDIDATES = ("set", "edition", "set name", "set_name")


def _find_col(headers: List[str], candidates) -> Optional[int]:
    for i, h in enumerate(headers):
        if h in candidates:
            return i
    return None


def parse(content: str) -> List[ParsedCard]:
    """Parse a generic CSV into ParsedCard list."""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return []

    raw_headers = rows[0]
    headers = [h.strip().lower() for h in raw_headers]

    name_col = _find_col(headers, _NAME_CANDIDATES)
    if name_col is None:
        # Fall back to first column that contains "name"
        for i, h in enumerate(headers):
            if "name" in h:
                name_col = i
                break
    if name_col is None:
        name_col = 0  # last resort

    qty_col = _find_col(headers, _QTY_CANDIDATES)
    set_col = _find_col(headers, _SET_CANDIDATES)

    cards: List[ParsedCard] = []
    for row in rows[1:]:
        if not row:
            continue
        name = (row[name_col] if name_col < len(row) else "").strip()
        if not name:
            continue
        qty = 1
        if qty_col is not None and qty_col < len(row):
            try:
                qty = max(1, int(float(row[qty_col])))
            except (ValueError, TypeError):
                qty = 1
        set_name: Optional[str] = None
        if set_col is not None and set_col < len(row):
            set_name = row[set_col].strip() or None
        cards.append(ParsedCard(name=name, set_name=set_name, quantity=qty))
    return cards
