"""
Shared collection filtering for cards list and stats.
Same semantics: name contains, exact match for rarity/type/set_name, price range inclusive.
"""
from typing import Optional

from loguru import logger


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string handling multiple formats (European/US with or without thousands separator).
    """
    if not price_str or price_str == "N/A":
        return None
    try:
        price_clean = str(price_str).strip()
        if "," in price_clean and "." in price_clean:
            last_comma_pos = price_clean.rfind(",")
            last_dot_pos = price_clean.rfind(".")
            if last_comma_pos > last_dot_pos:
                price_clean = price_clean.replace(".", "").replace(",", ".")
            else:
                price_clean = price_clean.replace(",", "")
        elif "," in price_clean:
            price_clean = price_clean.replace(",", ".")
        return float(price_clean)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse price '{price_str}': {e}")
        return None


def filter_collection(
    collection: list,
    search: Optional[str] = None,
    rarity: Optional[str] = None,
    type_: Optional[str] = None,
    set_name: Optional[str] = None,
    price_min: Optional[str] = None,
    price_max: Optional[str] = None,
) -> list:
    """Filter collection: name contains, exact match for rarity/type/set_name, price range inclusive."""
    result = collection
    if search and search.strip():
        search_lower = search.strip().lower()
        result = [c for c in result if c.get("name") and search_lower in (c["name"] or "").lower()]
    if rarity and rarity.strip():
        r = rarity.strip().lower()
        result = [c for c in result if (c.get("rarity") or "").lower() == r]
    if type_ and type_.strip():
        t = type_.strip()
        result = [c for c in result if c.get("type") == t]
    if set_name and set_name.strip():
        s = set_name.strip()
        result = [c for c in result if c.get("set_name") == s]
    if price_min or price_max:
        try:
            min_num = float(price_min.replace(",", ".")) if price_min and price_min.strip() else None
        except (ValueError, TypeError):
            min_num = None
        try:
            max_num = float(price_max.replace(",", ".")) if price_max and price_max.strip() else None
        except (ValueError, TypeError):
            max_num = None
        if min_num is not None or max_num is not None:
            filtered = []
            for c in result:
                p = parse_price(c.get("price"))
                if p is None:
                    continue
                if min_num is not None and p < min_num:
                    continue
                if max_num is not None and p > max_num:
                    continue
                filtered.append(c)
            result = filtered
    return result
