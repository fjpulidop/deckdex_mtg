"""
Collection Insights Service

Provides 17 predefined insight queries that run server-side as pure computation.
Covers 5 categories: summary, distribution, ranking, patterns, activity.
"""
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Insight catalog (single source of truth)
# ---------------------------------------------------------------------------

INSIGHTS_CATALOG: List[Dict[str, Any]] = [
    # Summary
    {
        "id": "total_value",
        "label": "How much is my collection worth?",
        "label_key": "insights.total_value.question",
        "keywords": ["value", "worth", "price", "money", "total", "collection"],
        "category": "summary",
        "icon": "💰",
        "response_type": "value",
        "popular": True,
    },
    {
        "id": "total_cards",
        "label": "How many cards do I have?",
        "label_key": "insights.total_cards.question",
        "keywords": ["total", "cards", "count", "how many", "collection size"],
        "category": "summary",
        "icon": "🃏",
        "response_type": "value",
        "popular": True,
    },
    {
        "id": "avg_card_value",
        "label": "What is the average card value?",
        "label_key": "insights.avg_card_value.question",
        "keywords": ["average", "avg", "mean", "value", "price"],
        "category": "summary",
        "icon": "📊",
        "response_type": "value",
        "popular": False,
    },
    # Distribution
    {
        "id": "by_color",
        "label": "How is my collection split by color?",
        "label_key": "insights.by_color.question",
        "keywords": ["color", "colours", "white", "blue", "black", "red", "green", "wubrg", "split", "distribution"],
        "category": "distribution",
        "icon": "🎨",
        "response_type": "distribution",
        "popular": True,
    },
    {
        "id": "by_rarity",
        "label": "How is my collection split by rarity?",
        "label_key": "insights.by_rarity.question",
        "keywords": ["rarity", "rare", "uncommon", "common", "mythic", "split", "distribution"],
        "category": "distribution",
        "icon": "✨",
        "response_type": "distribution",
        "popular": False,
    },
    {
        "id": "by_set",
        "label": "Which sets do I have the most cards from?",
        "label_key": "insights.by_set.question",
        "keywords": ["set", "sets", "expansion", "edition", "most cards"],
        "category": "distribution",
        "icon": "📦",
        "response_type": "distribution",
        "popular": False,
    },
    {
        "id": "value_by_color",
        "label": "Where is my value concentrated by color?",
        "label_key": "insights.value_by_color.question",
        "keywords": ["value", "color", "worth", "money", "concentrated", "breakdown"],
        "category": "distribution",
        "icon": "💎",
        "response_type": "distribution",
        "popular": True,
    },
    {
        "id": "value_by_set",
        "label": "Which sets hold the most value?",
        "label_key": "insights.value_by_set.question",
        "keywords": ["value", "set", "worth", "most valuable", "expensive"],
        "category": "distribution",
        "icon": "🏆",
        "response_type": "distribution",
        "popular": False,
    },
    # Ranking
    {
        "id": "most_valuable",
        "label": "What are my most valuable cards?",
        "label_key": "insights.most_valuable.question",
        "keywords": ["most valuable", "expensive", "top", "best", "highest price"],
        "category": "ranking",
        "icon": "🥇",
        "response_type": "list",
        "popular": True,
    },
    {
        "id": "least_valuable",
        "label": "What are my least valuable cards?",
        "label_key": "insights.least_valuable.question",
        "keywords": ["least valuable", "cheapest", "cheap", "lowest price", "bottom"],
        "category": "ranking",
        "icon": "🔻",
        "response_type": "list",
        "popular": False,
    },
    {
        "id": "most_collected_set",
        "label": "Which set do I collect the most from?",
        "label_key": "insights.most_collected_set.question",
        "keywords": ["most collected", "set", "top set", "focus", "most cards from"],
        "category": "ranking",
        "icon": "📈",
        "response_type": "list",
        "popular": False,
    },
    # Patterns
    {
        "id": "duplicates",
        "label": "Do I have duplicate cards?",
        "label_key": "insights.duplicates.question",
        "keywords": ["duplicates", "duplicate", "copies", "multiple", "same card"],
        "category": "patterns",
        "icon": "🔄",
        "response_type": "list",
        "popular": True,
    },
    {
        "id": "missing_colors",
        "label": "Which MTG colors am I missing?",
        "label_key": "insights.missing_colors.question",
        "keywords": ["missing", "colors", "lacking", "gap", "wubrg"],
        "category": "patterns",
        "icon": "❓",
        "response_type": "comparison",
        "popular": True,
    },
    {
        "id": "no_price",
        "label": "Which cards have no price data?",
        "label_key": "insights.no_price.question",
        "keywords": ["no price", "missing price", "unpriced", "without price", "price data"],
        "category": "patterns",
        "icon": "❌",
        "response_type": "list",
        "popular": False,
    },
    {
        "id": "singleton_sets",
        "label": "Which sets do I have only one card from?",
        "label_key": "insights.singleton_sets.question",
        "keywords": ["singleton", "single", "only one", "one card", "lonely"],
        "category": "patterns",
        "icon": "🔍",
        "response_type": "list",
        "popular": False,
    },
    # Activity
    {
        "id": "recent_additions",
        "label": "What did I add recently?",
        "label_key": "insights.recent_additions.question",
        "keywords": ["recent", "new", "added", "last week", "latest", "recently"],
        "category": "activity",
        "icon": "🆕",
        "response_type": "list",
        "popular": True,
    },
    {
        "id": "monthly_summary",
        "label": "How many cards did I add per month?",
        "label_key": "insights.monthly_summary.question",
        "keywords": ["monthly", "per month", "timeline", "history", "when"],
        "category": "activity",
        "icon": "📅",
        "response_type": "timeline",
        "popular": False,
    },
    {
        "id": "biggest_month",
        "label": "When did I add the most cards?",
        "label_key": "insights.biggest_month.question",
        "keywords": ["biggest month", "most added", "peak", "when most", "most active"],
        "category": "activity",
        "icon": "🚀",
        "response_type": "timeline",
        "popular": False,
    },
]

# Quick lookup by ID
_CATALOG_BY_ID: Dict[str, Dict[str, Any]] = {entry["id"]: entry for entry in INSIGHTS_CATALOG}

# WUBRG normalization helpers (mirrors analytics.py)
_VALID_COLORS = {"W", "U", "B", "R", "G"}
_COLOR_NAME_MAP = {
    "white": "W",
    "blue": "U",
    "black": "B",
    "red": "R",
    "green": "G",
}
_WUBRG_ORDER = "WUBRG"
_COLOR_DISPLAY = {
    "W": "White",
    "U": "Blue",
    "B": "Black",
    "R": "Red",
    "G": "Green",
    "C": "Colorless",
}


def _normalize_color_identity(raw: Any) -> str:
    """Normalize color_identity to WUBRG letters. Returns 'C' for colorless/unknown."""
    if raw is None:
        return "C"
    if isinstance(raw, list):
        letters = [_COLOR_NAME_MAP.get(c.strip().lower(), c.strip().upper()) for c in raw if c]
    elif isinstance(raw, str):
        s = raw.strip()
        if not s or s == "[]":
            return "C"
        if s.startswith("["):
            tokens = re.findall(r"'([^']*)'", s)
            if not tokens:
                tokens = [t.strip() for t in s.strip("[]").split(",") if t.strip()]
            letters = []
            for t in tokens:
                t_lower = t.strip().lower()
                if t_lower in _COLOR_NAME_MAP:
                    letters.append(_COLOR_NAME_MAP[t_lower])
                elif t.strip().upper() in _VALID_COLORS:
                    letters.append(t.strip().upper())
        elif "," in s:
            letters = []
            for part in s.split(","):
                p = part.strip()
                if p.lower() in _COLOR_NAME_MAP:
                    letters.append(_COLOR_NAME_MAP[p.lower()])
                elif p.upper() in _VALID_COLORS:
                    letters.append(p.upper())
        else:
            s_lower = s.lower()
            if s_lower in _COLOR_NAME_MAP:
                letters = [_COLOR_NAME_MAP[s_lower]]
            elif s.upper() in _VALID_COLORS:
                letters = [s.upper()]
            else:
                letters = [ch for ch in s.upper() if ch in _VALID_COLORS]
    else:
        return "C"

    unique = sorted(set(letters), key=lambda c: _WUBRG_ORDER.index(c) if c in _WUBRG_ORDER else 99)
    return "".join(unique) if unique else "C"


def _parse_price(raw: Any) -> Optional[float]:
    """Parse price from string/float/int, returns None if invalid."""
    if raw is None or raw == "":
        return None
    try:
        s = str(raw).strip()
        if "," in s and "." in s:
            last_comma = s.rfind(",")
            last_dot = s.rfind(".")
            if last_comma > last_dot:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        val = float(s)
        return val if val >= 0 else None
    except (ValueError, TypeError):
        return None


def _parse_date(raw: Any) -> Optional[datetime]:
    """Parse ISO datetime string, returns None if invalid."""
    if not raw:
        return None
    try:
        s = str(raw).strip()
        # Try various formats
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s[:len(fmt) + 3], fmt)
            except ValueError:
                continue
        # Fallback: just parse the date portion
        return datetime.fromisoformat(s[:10])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# InsightsService
# ---------------------------------------------------------------------------

class InsightsService:
    """Executes insight queries against a user's collection."""

    def __init__(self, cards: List[Dict[str, Any]]):
        self.cards = cards

    def execute(self, insight_id: str) -> Dict[str, Any]:
        """Dispatch to the appropriate insight handler. Raises ValueError for unknown IDs."""
        entry = _CATALOG_BY_ID.get(insight_id)
        if not entry:
            raise ValueError(f"Unknown insight ID: {insight_id}")

        handler = getattr(self, f"_insight_{insight_id}", None)
        if handler is None:
            raise NotImplementedError(f"Insight '{insight_id}' is not implemented")

        result = handler()
        return {
            "insight_id": insight_id,
            "question": entry["label"],
            "answer_text": result.get("answer_text", ""),
            "response_type": entry["response_type"],
            "data": result.get("data", {}),
        }

    # -----------------------------------------------------------------------
    # Summary insights
    # -----------------------------------------------------------------------

    def _insight_total_value(self) -> Dict[str, Any]:
        prices = [p for c in self.cards if (p := _parse_price(c.get("price"))) is not None]
        total = sum(prices)
        counted = len(prices)
        total_cards = len(self.cards)
        unpriced = total_cards - counted

        answer = f"Your collection is worth €{total:,.2f}"
        if unpriced > 0:
            answer += f" ({counted} of {total_cards} cards have price data)"

        # Breakdown by rarity
        rarity_totals: Dict[str, float] = defaultdict(float)
        for card in self.cards:
            p = _parse_price(card.get("price"))
            if p is not None:
                rarity = (card.get("rarity") or "Unknown").capitalize()
                rarity_totals[rarity] += p
        breakdown = sorted(
            [{"label": k, "value": f"€{v:,.2f}"} for k, v in rarity_totals.items()],
            key=lambda x: float(x["value"].replace("€", "").replace(",", "")),
            reverse=True,
        )

        return {
            "answer_text": answer,
            "data": {
                "primary_value": f"€{total:,.2f}",
                "unit": "EUR",
                "breakdown": breakdown,
            },
        }

    def _insight_total_cards(self) -> Dict[str, Any]:
        total = len(self.cards)
        return {
            "answer_text": f"You have {total} card{'' if total == 1 else 's'} in your collection",
            "data": {
                "primary_value": str(total),
                "unit": "cards",
                "breakdown": [],
            },
        }

    def _insight_avg_card_value(self) -> Dict[str, Any]:
        prices = [p for c in self.cards if (p := _parse_price(c.get("price"))) is not None]
        if not prices:
            return {
                "answer_text": "No price data available",
                "data": {"primary_value": "€0.00", "unit": "EUR", "breakdown": []},
            }
        avg = sum(prices) / len(prices)
        median_sorted = sorted(prices)
        mid = len(median_sorted) // 2
        median = (median_sorted[mid - 1] + median_sorted[mid]) / 2 if len(median_sorted) % 2 == 0 else median_sorted[mid]
        return {
            "answer_text": f"Average card value is €{avg:,.2f} (median: €{median:,.2f})",
            "data": {
                "primary_value": f"€{avg:,.2f}",
                "unit": "EUR",
                "breakdown": [
                    {"label": "Median", "value": f"€{median:,.2f}"},
                    {"label": "Min", "value": f"€{min(prices):,.2f}"},
                    {"label": "Max", "value": f"€{max(prices):,.2f}"},
                    {"label": "Cards with price", "value": str(len(prices))},
                ],
            },
        }

    # -----------------------------------------------------------------------
    # Distribution insights
    # -----------------------------------------------------------------------

    def _insight_by_color(self) -> Dict[str, Any]:
        counter: Counter = Counter()
        for card in self.cards:
            identity = _normalize_color_identity(card.get("color_identity") or card.get("colors") or "")
            # Split multi-color into individual color letters for counting
            colors_in_card = [ch for ch in identity if ch in _VALID_COLORS] or ["C"]
            for color in colors_in_card:
                counter[color] += 1

        total = sum(counter.values()) or 1
        wubrg_order_with_c = list(_WUBRG_ORDER) + ["C"]
        items = []
        for color in wubrg_order_with_c:
            if color in counter:
                count = counter[color]
                items.append({
                    "label": _COLOR_DISPLAY.get(color, color),
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                    "color": color,
                })

        most_common_color = max(counter, key=counter.get) if counter else "C"
        display = _COLOR_DISPLAY.get(most_common_color, most_common_color)
        return {
            "answer_text": f"Your collection is most {display} ({counter.get(most_common_color, 0)} cards)",
            "data": {"items": items},
        }

    def _insight_by_rarity(self) -> Dict[str, Any]:
        counter: Counter = Counter()
        for card in self.cards:
            r = (card.get("rarity") or "Unknown").capitalize()
            counter[r] += 1

        total = sum(counter.values()) or 1
        rarity_order = ["Mythic", "Rare", "Uncommon", "Common"]
        ordered_keys = [k for k in rarity_order if k in counter] + sorted(
            [k for k in counter if k not in rarity_order]
        )
        items = [
            {
                "label": k,
                "count": counter[k],
                "percentage": round(counter[k] / total * 100, 1),
            }
            for k in ordered_keys
        ]
        most_common = max(counter, key=counter.get) if counter else "Unknown"
        return {
            "answer_text": f"Most cards are {most_common} ({counter.get(most_common, 0)} cards, {round(counter.get(most_common, 0)/total*100, 1)}%)",
            "data": {"items": items},
        }

    def _insight_by_set(self) -> Dict[str, Any]:
        counter: Counter = Counter()
        for card in self.cards:
            s = (card.get("set_name") or "Unknown").strip()
            counter[s] += 1

        total = sum(counter.values()) or 1
        top = counter.most_common(10)
        items = [
            {
                "label": name,
                "count": count,
                "percentage": round(count / total * 100, 1),
            }
            for name, count in top
        ]
        top_set = top[0][0] if top else "Unknown"
        return {
            "answer_text": f"Most cards are from {top_set} ({top[0][1] if top else 0} cards)",
            "data": {"items": items},
        }

    def _insight_value_by_color(self) -> Dict[str, Any]:
        color_totals: Dict[str, float] = defaultdict(float)
        for card in self.cards:
            p = _parse_price(card.get("price"))
            if p is None:
                continue
            identity = _normalize_color_identity(card.get("color_identity") or card.get("colors") or "")
            colors_in_card = [ch for ch in identity if ch in _VALID_COLORS] or ["C"]
            value_per_color = p / len(colors_in_card)
            for color in colors_in_card:
                color_totals[color] += value_per_color

        total = sum(color_totals.values()) or 1
        wubrg_order_with_c = list(_WUBRG_ORDER) + ["C"]
        items = []
        for color in wubrg_order_with_c:
            if color in color_totals:
                val = color_totals[color]
                items.append({
                    "label": _COLOR_DISPLAY.get(color, color),
                    "count": round(val, 2),
                    "value": f"€{val:,.2f}",
                    "percentage": round(val / total * 100, 1),
                    "color": color,
                })

        top_color = max(color_totals, key=color_totals.get) if color_totals else "C"
        display = _COLOR_DISPLAY.get(top_color, top_color)
        return {
            "answer_text": f"{display} cards hold the most value (€{color_totals.get(top_color, 0):,.2f})",
            "data": {"items": items},
        }

    def _insight_value_by_set(self) -> Dict[str, Any]:
        set_totals: Dict[str, float] = defaultdict(float)
        for card in self.cards:
            p = _parse_price(card.get("price"))
            if p is None:
                continue
            s = (card.get("set_name") or "Unknown").strip()
            set_totals[s] += p

        total = sum(set_totals.values()) or 1
        top = sorted(set_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        items = [
            {
                "label": name,
                "count": round(val, 2),
                "value": f"€{val:,.2f}",
                "percentage": round(val / total * 100, 1),
            }
            for name, val in top
        ]
        top_set = top[0][0] if top else "Unknown"
        return {
            "answer_text": f"{top_set} holds the most value (€{top[0][1]:,.2f})" if top else "No price data",
            "data": {"items": items},
        }

    # -----------------------------------------------------------------------
    # Ranking insights
    # -----------------------------------------------------------------------

    def _insight_most_valuable(self) -> Dict[str, Any]:
        priced = [(c, p) for c in self.cards if (p := _parse_price(c.get("price"))) is not None and p > 0]
        top = sorted(priced, key=lambda x: x[1], reverse=True)[:10]
        items = [
            {
                "card_id": c.get("id"),
                "name": c.get("name") or c.get("english_name") or "Unknown",
                "detail": f"€{p:,.2f}",
                "image_url": None,
            }
            for c, p in top
        ]
        top_price = top[0][1] if top else 0
        top_name = top[0][0].get("name") or "?" if top else "?"
        return {
            "answer_text": f"Most valuable card: {top_name} (€{top_price:,.2f})",
            "data": {"items": items},
        }

    def _insight_least_valuable(self) -> Dict[str, Any]:
        priced = [(c, p) for c in self.cards if (p := _parse_price(c.get("price"))) is not None and p > 0]
        bottom = sorted(priced, key=lambda x: x[1])[:10]
        items = [
            {
                "card_id": c.get("id"),
                "name": c.get("name") or c.get("english_name") or "Unknown",
                "detail": f"€{p:,.2f}",
                "image_url": None,
            }
            for c, p in bottom
        ]
        low_price = bottom[0][1] if bottom else 0
        low_name = bottom[0][0].get("name") or "?" if bottom else "?"
        return {
            "answer_text": f"Least valuable card: {low_name} (€{low_price:,.2f})",
            "data": {"items": items},
        }

    def _insight_most_collected_set(self) -> Dict[str, Any]:
        counter: Counter = Counter()
        for card in self.cards:
            s = (card.get("set_name") or "Unknown").strip()
            counter[s] += 1

        top = counter.most_common(10)
        items = [
            {"name": name, "detail": f"{count} card{'' if count == 1 else 's'}", "card_id": None}
            for name, count in top
        ]
        top_set = top[0][0] if top else "Unknown"
        top_count = top[0][1] if top else 0
        return {
            "answer_text": f"Most collected set: {top_set} ({top_count} cards)",
            "data": {"items": items},
        }

    # -----------------------------------------------------------------------
    # Patterns insights
    # -----------------------------------------------------------------------

    def _insight_duplicates(self) -> Dict[str, Any]:
        name_counts: Counter = Counter()
        name_to_card: Dict[str, Any] = {}
        for card in self.cards:
            name = (card.get("name") or card.get("english_name") or "").strip()
            if name:
                name_counts[name] += 1
                if name not in name_to_card:
                    name_to_card[name] = card

        dupes = [(name, cnt) for name, cnt in name_counts.items() if cnt > 1]
        dupes.sort(key=lambda x: x[1], reverse=True)

        items = [
            {
                "card_id": name_to_card[name].get("id"),
                "name": name,
                "detail": f"{cnt} copies",
                "image_url": None,
            }
            for name, cnt in dupes[:20]
        ]
        total_dupes = len(dupes)
        total_extra = sum(cnt - 1 for _, cnt in dupes)
        if total_dupes == 0:
            answer = "No duplicate cards found"
        else:
            answer = f"{total_dupes} card name{'' if total_dupes == 1 else 's'} appear more than once ({total_extra} extra cop{'' if total_extra == 1 else 'ies'})"
        return {
            "answer_text": answer,
            "data": {"items": items},
        }

    def _insight_missing_colors(self) -> Dict[str, Any]:
        present_colors: set = set()
        for card in self.cards:
            identity = _normalize_color_identity(card.get("color_identity") or card.get("colors") or "")
            for ch in identity:
                if ch in _VALID_COLORS:
                    present_colors.add(ch)

        items = [
            {
                "label": _COLOR_DISPLAY.get(color, color),
                "present": color in present_colors,
                "detail": f"You have {sum(1 for c in self.cards if color in _normalize_color_identity(c.get('color_identity') or c.get('colors') or ''))} cards" if color in present_colors else "No cards of this color",
            }
            for color in _WUBRG_ORDER
        ]
        missing = [_COLOR_DISPLAY[c] for c in _WUBRG_ORDER if c not in present_colors]
        if not missing:
            answer = "You have cards of all 5 MTG colors!"
        else:
            answer = f"Missing colors: {', '.join(missing)}"
        return {
            "answer_text": answer,
            "data": {"items": items},
        }

    def _insight_no_price(self) -> Dict[str, Any]:
        unpriced = [c for c in self.cards if _parse_price(c.get("price")) is None]
        items = [
            {
                "card_id": c.get("id"),
                "name": c.get("name") or c.get("english_name") or "Unknown",
                "detail": "No price data",
                "image_url": None,
            }
            for c in unpriced[:20]
        ]
        count = len(unpriced)
        total = len(self.cards)
        if count == 0:
            answer = "All cards have price data!"
        else:
            answer = f"{count} of {total} cards ({round(count/total*100, 1)}%) have no price data"
        return {
            "answer_text": answer,
            "data": {"items": items},
        }

    def _insight_singleton_sets(self) -> Dict[str, Any]:
        counter: Counter = Counter()
        for card in self.cards:
            s = (card.get("set_name") or "Unknown").strip()
            counter[s] += 1

        singletons = [(name, cnt) for name, cnt in counter.items() if cnt == 1]
        singletons.sort(key=lambda x: x[0])
        items = [
            {"name": name, "detail": "1 card", "card_id": None}
            for name, _ in singletons[:20]
        ]
        count = len(singletons)
        if count == 0:
            answer = "All sets have more than one card"
        else:
            answer = f"{count} set{'' if count == 1 else 's'} have only one card in your collection"
        return {
            "answer_text": answer,
            "data": {"items": items},
        }

    # -----------------------------------------------------------------------
    # Activity insights
    # -----------------------------------------------------------------------

    def _insight_recent_additions(self) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=7)
        recent = []
        for card in self.cards:
            dt = _parse_date(card.get("created_at"))
            if dt and dt >= cutoff:
                recent.append((card, dt))
        recent.sort(key=lambda x: x[1], reverse=True)

        items = [
            {
                "card_id": c.get("id"),
                "name": c.get("name") or c.get("english_name") or "Unknown",
                "detail": dt.strftime("%b %d, %Y"),
                "image_url": None,
            }
            for c, dt in recent[:20]
        ]
        count = len(recent)
        if count == 0:
            answer = "No cards added in the last 7 days"
        else:
            answer = f"{count} card{'' if count == 1 else 's'} added in the last 7 days"
        return {
            "answer_text": answer,
            "data": {"items": items},
        }

    def _insight_monthly_summary(self) -> Dict[str, Any]:
        monthly: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "value": 0.0})
        for card in self.cards:
            dt = _parse_date(card.get("created_at"))
            if dt:
                key = dt.strftime("%Y-%m")
                monthly[key]["count"] += 1
                p = _parse_price(card.get("price"))
                if p is not None:
                    monthly[key]["value"] += p

        # Sort by period and take last 12 months
        sorted_months = sorted(monthly.keys())[-12:]
        items = [
            {
                "period": datetime.strptime(k, "%Y-%m").strftime("%b %Y"),
                "count": monthly[k]["count"],
                "value": f"€{monthly[k]['value']:,.2f}" if monthly[k]["value"] > 0 else None,
            }
            for k in sorted_months
        ]
        total_months = len(monthly)
        total_cards_with_date = sum(m["count"] for m in monthly.values())
        if not items:
            answer = "No activity data available (cards missing created_at)"
        else:
            answer = f"Activity tracked over {total_months} month{'' if total_months == 1 else 's'} ({total_cards_with_date} cards with dates)"
        return {
            "answer_text": answer,
            "data": {"items": items},
        }

    def _insight_biggest_month(self) -> Dict[str, Any]:
        monthly: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "value": 0.0})
        for card in self.cards:
            dt = _parse_date(card.get("created_at"))
            if dt:
                key = dt.strftime("%Y-%m")
                monthly[key]["count"] += 1
                p = _parse_price(card.get("price"))
                if p is not None:
                    monthly[key]["value"] += p

        if not monthly:
            return {
                "answer_text": "No activity data available (cards missing created_at)",
                "data": {"items": []},
            }

        sorted_by_count = sorted(monthly.items(), key=lambda x: x[1]["count"], reverse=True)[:6]
        items = [
            {
                "period": datetime.strptime(k, "%Y-%m").strftime("%b %Y"),
                "count": data["count"],
                "value": f"€{data['value']:,.2f}" if data["value"] > 0 else None,
            }
            for k, data in sorted_by_count
        ]
        top_k, top_data = sorted_by_count[0]
        top_period = datetime.strptime(top_k, "%Y-%m").strftime("%B %Y")
        return {
            "answer_text": f"Most active month: {top_period} ({top_data['count']} cards added)",
            "data": {"items": items},
        }


# ---------------------------------------------------------------------------
# InsightsSuggestionEngine
# ---------------------------------------------------------------------------

class InsightsSuggestionEngine:
    """Analyzes collection signals to suggest the most relevant insights."""

    # Weights: higher = more likely to appear in suggestions
    _BASE_WEIGHT = 1.0

    def __init__(self, cards: List[Dict[str, Any]]):
        self.cards = cards

    def get_suggestions(self, limit: int = 6) -> List[Dict[str, str]]:
        """Return top N suggestion dicts with {id, label}."""
        scores: Dict[str, float] = {}

        # Initialize all popular insights with base weight
        for entry in INSIGHTS_CATALOG:
            if entry["popular"]:
                scores[entry["id"]] = self._BASE_WEIGHT

        # Signal: total_value always included as fallback
        scores["total_value"] = scores.get("total_value", 0) + 2.0

        # Signal: recent activity → boost activity insights
        cutoff = datetime.now() - timedelta(days=7)
        has_recent = any(
            (dt := _parse_date(c.get("created_at"))) is not None and dt >= cutoff
            for c in self.cards
        )
        if has_recent:
            scores["recent_additions"] = scores.get("recent_additions", 0) + 3.0

        # Signal: duplicates detected → boost duplicates
        name_counts: Counter = Counter(
            (c.get("name") or c.get("english_name") or "").strip()
            for c in self.cards
            if (c.get("name") or c.get("english_name") or "").strip()
        )
        has_dupes = any(cnt > 1 for cnt in name_counts.values())
        if has_dupes:
            scores["duplicates"] = scores.get("duplicates", 0) + 2.5

        # Signal: missing colors → boost missing_colors
        present_colors: set = set()
        for card in self.cards:
            identity = _normalize_color_identity(card.get("color_identity") or card.get("colors") or "")
            for ch in identity:
                if ch in _VALID_COLORS:
                    present_colors.add(ch)
        if len(present_colors) < 5:
            scores["missing_colors"] = scores.get("missing_colors", 0) + 2.0

        # Signal: cards without price → boost no_price
        unpriced_count = sum(1 for c in self.cards if _parse_price(c.get("price")) is None)
        if unpriced_count > 0:
            scores["no_price"] = scores.get("no_price", 0) + 1.5
            if unpriced_count > 10:
                scores["no_price"] += 1.0

        # Signal: large collection → boost distribution insights
        if len(self.cards) > 100:
            scores["by_color"] = scores.get("by_color", 0) + 1.5
            scores["value_by_set"] = scores.get("value_by_set", 0) + 1.0

        # Signal: value variance → boost value insights
        prices = [p for c in self.cards if (p := _parse_price(c.get("price"))) is not None]
        if len(prices) >= 2:
            avg = sum(prices) / len(prices)
            variance = sum((p - avg) ** 2 for p in prices) / len(prices)
            if variance > 10:  # High variance
                scores["most_valuable"] = scores.get("most_valuable", 0) + 1.5
                scores["value_by_color"] = scores.get("value_by_color", 0) + 1.0

        # Ensure total_cards is included if collection is empty
        if not self.cards:
            scores["total_cards"] = scores.get("total_cards", 0) + 3.0
            scores["total_value"] = scores.get("total_value", 0) + 2.0

        # Sort by score descending, take top N
        top_ids = sorted(scores, key=scores.get, reverse=True)[:limit]

        return [
            {"id": insight_id, "label": _CATALOG_BY_ID[insight_id]["label"]}
            for insight_id in top_ids
            if insight_id in _CATALOG_BY_ID
        ]
