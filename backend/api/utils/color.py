"""
Color identity normalization utilities.

Shared module for normalizing MTG color identity values from various storage
formats (lists, comma-separated strings, Python list reprs, full color names)
into canonical WUBRG letter strings.
"""

import re
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid WUBRG single-letter codes
VALID_COLORS = {"W", "U", "B", "R", "G"}

# WUBRG canonical ordering
WUBRG_ORDER = "WUBRG"

# Full-name → letter mapping (case-insensitive lookup)
COLOR_NAME_MAP = {
    "white": "W",
    "blue": "U",
    "black": "B",
    "red": "R",
    "green": "G",
}

# Letter → display name mapping
COLOR_DISPLAY = {
    "W": "White",
    "U": "Blue",
    "B": "Black",
    "R": "Red",
    "G": "Green",
    "C": "Colorless",
}


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def normalize_color_identity(raw: Any) -> str:
    """
    Normalize color_identity from various DB formats to a canonical WUBRG string.

    Handles:
      - Python list: ["W", "U"]
      - str repr of Python list: "['W', 'U']"
      - Comma-separated: "W,U" or "W, U"
      - Full names: "Blue" or "['Blue', 'Red']"
      - Single letter: "W"
      - Empty / None → "C" (colorless)

    Returns:
        A string of WUBRG letters in canonical order (e.g. "WU", "BRG"),
        or "C" for colorless/unknown.
    """
    if raw is None:
        return "C"

    if isinstance(raw, list):
        letters = [COLOR_NAME_MAP.get(c.strip().lower(), c.strip().upper()) for c in raw if c]
    elif isinstance(raw, str):
        s = raw.strip()
        if not s or s == "[]":
            return "C"
        # Strip Python list-repr brackets/quotes: "['W', 'U']" → tokens
        if s.startswith("["):
            # Extract quoted tokens from the repr
            tokens = re.findall(r"'([^']*)'", s)
            if not tokens:
                # Fallback: just strip brackets
                tokens = [t.strip() for t in s.strip("[]").split(",") if t.strip()]
            letters = []
            for t in tokens:
                t_lower = t.strip().lower()
                if t_lower in COLOR_NAME_MAP:
                    letters.append(COLOR_NAME_MAP[t_lower])
                elif t.strip().upper() in VALID_COLORS:
                    letters.append(t.strip().upper())
                # else skip unknown tokens
        elif "," in s:
            # Comma-separated: "W,U" or "White,Blue"
            letters = []
            for part in s.split(","):
                p = part.strip()
                p_lower = p.lower()
                if p_lower in COLOR_NAME_MAP:
                    letters.append(COLOR_NAME_MAP[p_lower])
                elif p.upper() in VALID_COLORS:
                    letters.append(p.upper())
        else:
            # Single value: "W" or "Blue"
            s_lower = s.lower()
            if s_lower in COLOR_NAME_MAP:
                letters = [COLOR_NAME_MAP[s_lower]]
            elif s.upper() in VALID_COLORS:
                letters = [s.upper()]
            else:
                # Try each character (e.g. "WU" stored without separator)
                letters = [ch for ch in s.upper() if ch in VALID_COLORS]
    else:
        return "C"

    # Deduplicate and sort in WUBRG order
    unique = sorted(set(letters), key=lambda c: WUBRG_ORDER.index(c) if c in WUBRG_ORDER else 99)
    return "".join(unique) if unique else "C"
